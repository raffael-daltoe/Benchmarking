import os
import json
import requests
import subprocess
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import sys
from dataclasses import dataclass
import re
from typing import List, Optional


@dataclass
class CacheConfig:
    """Stores cache configuration details."""
    sets: int
    ways: int
    latency: int


class ChampSimRunner:
    """
    A class to handle building, configuring, and running ChampSim on
    different replacement policies, prefetchers, and branch predictors,
    as well as different cache configurations.

    Attributes:
        champ_sim_path (str): Path to the ChampSim repository.
        trace_dir (str): Directory where trace files are stored.
        config_file (str): Path to the base JSON config file for ChampSim.
        output_dir (str): Directory to store the output files.
        output_dir_orig (str): Original top-level output directory.
        policies (List[str]): List of replacement policies to test.
        prefetchers (List[str]): List of prefetchers to test.
        branch_predictors (List[str]): List of branch predictors to test.
        threads (int): Number of threads/workers for parallel execution.
        warmup_instructions (Optional[int]): Number of warmup instructions.
        simulation_instructions (Optional[int]): Number of simulation instructions.
        L1I_Config (List[CacheConfig]): List of L1I cache configurations.
        L1D_Config (List[CacheConfig]): List of L1D cache configurations.
        L2_Config (List[CacheConfig]): List of L2C cache configurations.
        LLC_Config (List[CacheConfig]): List of LLC cache configurations.
    """

    def __init__(
        self,
        champ_sim_path: str,
        trace_dir: str,
        config_file: str,
        output_dir: str,
        policies: List[str],
        prefetchers: List[str],
        branch_predictors: List[str],
        threads: int,
        warmup_instructions: Optional[int] = None,
        simulation_instructions: Optional[int] = None,
        L1I_Config: Optional[List[CacheConfig]] = None,
        L1D_Config: Optional[List[CacheConfig]] = None,
        L2_Config: Optional[List[CacheConfig]] = None,
        LLC_Config: Optional[List[CacheConfig]] = None,
    ):
        self.champ_sim_path = champ_sim_path
        self.trace_dir = trace_dir
        self.config_file = config_file
        self.config_bin_name = 'champsim'

        self.output_dir = output_dir
        self.output_dir_orig = output_dir

        self.policies = policies
        self.prefetchers = prefetchers
        self.branch_predictors = branch_predictors
        self.threads = threads

        # Optional instruction boundaries
        self.warmup_instructions = warmup_instructions
        self.simulation_instructions = simulation_instructions

        # Semaphores to coordinate certain tasks
        self.S1_replacement = threading.Semaphore(1)
        self.S2_replacement = threading.Semaphore(1)
        self.S3_replacement = threading.Semaphore(1)
        self.SGlobal = threading.Semaphore(threads)

        # Initially, nothing is modified
        self.modified_config = None  # Will hold JSON config in memory
        self.json_config_name = None
        self.json_directory = 'json_files/'

        self.L1I_Config = L1I_Config or []
        self.L1D_Config = L1D_Config or []
        self.L2_Config = L2_Config or []
        self.LLC_Config = LLC_Config or []

        # Group all cache configs into a single list of 4-tuples
        self.Samples = list(zip(self.L1I_Config, self.L1D_Config, 
                                self.L2_Config, self.LLC_Config))

    def download_traces(self, trace_urls: List[str]) -> None:
        """Download trace files if they are not already present."""
        if not os.path.exists(self.trace_dir):
            os.makedirs(self.trace_dir)

        for file_url in trace_urls:
            file_name = os.path.basename(file_url)
            file_path = os.path.join(self.trace_dir, file_name)

            if os.path.exists(file_path):
                print(f"File {file_name} already exists, skipping download.")
                continue

            print(f"Downloading {file_name}...")
            with requests.get(file_url, stream=True) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"Downloaded {file_name}.")

    def modify_replacement_policy(self, policy: str) -> None:
        """Modify the replacement policy in the loaded config."""
        time.sleep(0.2)
        self.S1_replacement.acquire()
        self.modified_config['LLC']['replacement'] = policy

    def modify_prefetcher(self, prefetcher: str) -> None:
        """Modify the prefetcher in the loaded config."""
        time.sleep(0.3)
        self.S2_replacement.acquire()
        self.modified_config['LLC']['prefetcher'] = prefetcher

    def modify_branch(self, branch: str) -> None:
        """Modify the branch predictor in the loaded config."""
        time.sleep(0.35)
        self.S3_replacement.acquire()
        self.modified_config['ooo_cpu'][0]['branch_predictor'] = branch

    def modify_output_exec_name(self, policy: str, prefetcher: str, branch: str) -> None:
        """
        Update the JSON config executable name and store it for usage
        in compilation and execution steps.
        """
        updated_config = self.modified_config.copy()
        updated_config['executable_name'] = f'champsim_{policy}_{prefetcher}_{branch}'
        self.config_bin_name = f'champsim_{policy}_{prefetcher}_{branch}'
        self.modified_config = updated_config

    def write_modified_config(self, file_path: str) -> None:
        """
        Write the modified JSON config to disk, copy to ChampSim path,
        then run config.sh and make.
        """
        if not self.modified_config:
            print("No configuration changes to write.")
            return

        # Write the modified config locally
        with open(file_path, 'w') as file:
            json.dump(self.modified_config, file, indent=4)

        # Ensure json_directory exists in ChampSim path
        subprocess.run(
            ['mkdir', '-p', self.json_directory],
            cwd=self.champ_sim_path
        )

        # Full path to the config inside ChampSim
        self.json_config_name = os.path.join(
            self.champ_sim_path,
            self.json_directory,
            f'{self.config_bin_name}.json'
        )

        # Relative path for config.sh usage
        json_to_config = os.path.join(self.json_directory, f'{self.config_bin_name}.json')

        # Copy the config file to the ChampSim directory
        subprocess.run(['cp', file_path, self.json_config_name])

        # Run config.sh to generate the configs
        subprocess.run(["./config.sh", json_to_config],
                       cwd=self.champ_sim_path, check=True)

        # Build with the new config
        subprocess.run(["make", f"-j{self.threads}"],
                       cwd=self.champ_sim_path,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT,
                       check=True)

    def exec_single_trace(
        self,
        trace_name: str,
        trace_path: str,
        policy: Optional[str],
        branch: Optional[str],
        prefetcher: Optional[str],
    ) -> None:
        """
        Execute ChampSim on a single trace file with the
        given (policy, branch, prefetch) configuration.
        """
        # Define naming for output logs
        temp_output_file = os.path.join(
            self.output_dir,
            f"{trace_name}_pol:{policy}_bra:{branch}_pre:{prefetcher}_output.txt"
        )
        final_output_file = os.path.join(
            self.output_dir,
            f"{trace_name}_pol:{policy}_bra:{branch}_pre:{prefetcher}_output_DONE.txt"
        )

        # The final ChampSim binary path
        champsim_bin = os.path.join(self.champ_sim_path, 'bin', self.config_bin_name)

        # Build the command
        command = [champsim_bin]
        if self.warmup_instructions:
            command += ["--warmup-instructions", str(self.warmup_instructions)]
        if self.simulation_instructions:
            command += ["--simulation-instructions", str(self.simulation_instructions)]
        command.append(trace_path)

        print(f"Executing ChampSim for {trace_name} "
              f"(Policy={policy}, Branch={branch}, Prefetch={prefetcher})...")

        # Release semaphores so that future config changes can happen
        self.S1_replacement.release()
        self.S2_replacement.release()
        self.S3_replacement.release()

        try:
            with open(temp_output_file, 'w') as outfile:
                subprocess.run(command, stdout=outfile, stderr=outfile, check=True)

            # Mark the output file as DONE
            os.rename(temp_output_file, final_output_file)
            print(f"[DONE] {trace_name} => {final_output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error: ChampSim execution failed for {trace_name}. {e}")
        finally:
            self.SGlobal.release()

    def verify_already_executed(
            self,
            policy: Optional[str], 
            prefetch: Optional[str], 
            branch: Optional[str],
            trace_name: Optional[str]
    ) -> None:
        """
        Verify if this simulation was already executed
        """
        try:
            if not os.path.exists(self.output_dir):
                raise UnboundLocalError
            file_name = f"{trace_name}_pol:{policy}_bra:{branch}_pre:{prefetch}_output_DONE.txt"
            for name in os.listdir(self.output_dir):
                if name == file_name:
                    print(f"File {file_name} already executed")
                    return True
            return False
        except UnboundLocalError:
            print(f"Directory not found: {self.output_dir}")
            sys.exit(1)

    def prepare_execution(
        self,
        executor: ThreadPoolExecutor,
        policy: Optional[str],
        branch: Optional[str],
        prefetcher: Optional[str],
    ) -> None:
        
        for trace_file in os.listdir(self.trace_dir):
            #print(f"trace = {trace_file} and all traces are = {os.listdir(self.trace_dir)}")
            if trace_file.endswith('.champsimtrace') or trace_file.endswith('.xz'):
                # Remove the extensions .xz or .champsimtrace
                if trace_file.endswith('.xz'):
                    clean_trace_file = trace_file[:-3]
                    clean_trace_file = os.path.splitext(clean_trace_file)[0]
                elif trace_file.endswith('.champsimtrace'):
                    clean_trace_file = trace_file[:-13]
                    clean_trace_file = os.path.splitext(clean_trace_file)[0]
                
                    
                   # trace_name = os.path.splitext(trace_file)[0]
                if self.verify_already_executed(policy, prefetcher, branch, clean_trace_file):
                    self.S2_replacement.release()
                    self.S1_replacement.release()
                    self.S3_replacement.release()
                    continue
                else:
                    trace_path = os.path.join(self.trace_dir, trace_file)
                    self.SGlobal.acquire()
                    # Pass the cleaned trace file without extensions
                    executor.submit(
                        self.exec_single_trace,
                        clean_trace_file,
                        trace_path,
                        policy,
                        branch,
                        prefetcher
                    )

    def modify_size_cache(
        self,
        L1I: CacheConfig,
        L1D: CacheConfig,
        L2C: CacheConfig,
        LLC: CacheConfig
    ) -> None:
        """
        Load the base config file and change the cache config
        parameters for L1I, L1D, L2, and LLC.
        """
        with open(self.config_file, 'r') as file:
            config = json.load(file)

        config['L1I'].update({
            'sets': L1I.sets,
            'ways': L1I.ways,
            'latency': L1I.latency
        })
        config['L1D'].update({
            'sets': L1D.sets,
            'ways': L1D.ways,
            'latency': L1D.latency
        })
        config['L2C'].update({
            'sets': L2C.sets,
            'ways': L2C.ways,
            'latency': L2C.latency
        })
        config['LLC'].update({
            'sets': LLC.sets,
            'ways': LLC.ways,
            'latency': LLC.latency
        })

        self.modified_config = config

    def modify_hawkeye_algorithm(self, LLC: CacheConfig) -> None:
        """
        If using Hawkeye, ensure hawkeye_algorithm.cc has consistent
        LLC_SETS and LLC_WAYS definitions with the JSON configuration.
        """
        file_path = os.path.join(self.champ_sim_path, 'replacement', 'hawkeye', 'hawkeye_algorithm.cc')
        if not os.path.isfile(file_path):
            # Some replacements might not exist in the repo
            return

        with open(file_path, 'r') as file:
            content = file.read()

        # Pattern replacements
        sets_pattern = r"#define\s+LLC_SETS\s+NUM_CORE\s*\*\s*\d+"
        ways_pattern = r"#define\s+LLC_WAYS\s*\d+"

        sets_replacement = f"#define LLC_SETS NUM_CORE*{LLC.sets}"
        ways_replacement = f"#define LLC_WAYS {LLC.ways}"

        content = re.sub(sets_pattern, sets_replacement, content)
        content = re.sub(ways_pattern, ways_replacement, content)

        with open(file_path, 'w') as file:
            file.write(content)

    def modify_mockingjay(self, LLC: CacheConfig) -> None:
        """
        If using mockingjay, ensure mockingjay.cc has consistent
        LLC_SET and LLC_WAY definitions with the JSON configuration.
        """
        file_path = os.path.join(self.champ_sim_path, 'replacement', 'mockingjay', 'mockingjay.cc')
        if not os.path.isfile(file_path):
            return

        with open(file_path, 'r') as file:
            content = file.read()

        # Pattern replacements
        set_pattern = r"#define\s+LLC_SET\s+\d+"
        way_pattern = r"#define\s+LLC_WAY\s+\d+"

        set_replacement = f"#define LLC_SET {LLC.sets}"
        way_replacement = f"#define LLC_WAY {LLC.ways}"

        content = re.sub(set_pattern, set_replacement, content)
        content = re.sub(way_pattern, way_replacement, content)

        with open(file_path, 'w') as file:
            file.write(content)

    def is_already_executed(
        self,
        policy: Optional[str],
        prefetcher: Optional[str],
        branch: Optional[str],
        trace_name: str
    ) -> bool:
        """
        Check if the results for a particular config and trace
        have already been produced (i.e., DONE file exists).
        """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        file_name = f"{trace_name}_pol:{policy}_bra:{branch}_pre:{prefetcher}_output_DONE.txt"
        file_path = os.path.join(self.output_dir, file_name)
        if os.path.exists(file_path):
            print(f"[SKIP] Output already exists for {file_name}.")
            return True
        return False

    def execute_all_policies(self, trace_urls: List[str]) -> None:
        """
        Download the traces (if necessary), then for each sample set
        of cache configurations, build and execute all combos of
        replacement policy, prefetcher, and branch predictor.
        """
        # Ensure output directory
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Download traces
        self.download_traces(trace_urls)

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for index, sample in enumerate(self.Samples, start=1):
                L1I, L1D, L2C, LLC = sample

                # Each sample set has its own folder
                sample_folder = os.path.join(self.output_dir_orig, f"Sample{index}")
                if not os.path.exists(sample_folder):
                    os.makedirs(sample_folder)
                self.output_dir = sample_folder

                # Modify cache sizes
                self.modify_size_cache(L1I, L1D, L2C, LLC)
                # If we are using hawkeye or mockingjay, we fix them too
                self.modify_hawkeye_algorithm(LLC)
                self.modify_mockingjay(LLC)

                # For each combination of policies/prefetchers/branch
                # If you only want to run certain fields, you can just
                # leave them empty or pass None to skip.
                for policy in self.policies or [None]:
                    for prefetcher in self.prefetchers or [None]:
                        for branch in self.branch_predictors or [None]:
                            # Do JSON modifications
                            self.modify_replacement_policy(policy)
                            self.modify_prefetcher(prefetcher)
                            self.modify_branch(branch)

                            self.modify_output_exec_name(
                                policy, prefetcher, branch
                            )
                            self.write_modified_config(self.config_file)

                            # Launch parallel jobs for each trace
                            self.prepare_execution(executor, policy, branch, prefetcher)


def main() -> None:
    """
    Example usage:
        python3 script.py <threads> <champsim_path> <trace_dir>
                          <config_file> <output_dir>
                          <warmup_instructions> <simulation_instructions>
    """
    if len(sys.argv) < 6:
        print(
            "Usage: python3 script.py <number_of_threads> <champsim_path> "
            "<trace_dir> <config_file> <output_dir> "
            "[warmup_instructions] [simulation_instructions]"
        )
        sys.exit(1)

    try:
        threads = int(sys.argv[1])
        if threads < 1:
            raise ValueError
    except ValueError:
        print("Please provide a valid (positive) number of threads.")
        sys.exit(1)

    champ_sim_path = sys.argv[2]
    trace_dir = sys.argv[3]
    config_file = sys.argv[4]
    output_dir = sys.argv[5]

    warmup_instructions = (
        int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6].isdigit() else None
    )
    simulation_instructions = (
        int(sys.argv[7]) if len(sys.argv) > 7 and sys.argv[7].isdigit() else None
    )

    # You can populate trace_urls from any source as needed
    trace_urls = [
        #"https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/400.perlbench-41B.champsimtrace.xz",
        #"https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/400.perlbench-50B.champsimtrace.xz",
    ]

    policies = [
                "bip",
                "hawkeye",
                "fifo",
                "emissary",
                "pcn",
                "rlr",
                "drrip",
                "lru",
                "ship",
                "mockingjay",
                "random"
                ]
    

    prefetchers = ["next_line","ip_stride","no"]

    branches = ["bimodal", "gshare", "tage"]
    
    
    # Example cache configurations
    L1I_config = [
        CacheConfig(64, 8, 4),
        CacheConfig(64, 8, 4),
    ]
    L1D_config = [
        CacheConfig(64, 8, 4),
        CacheConfig(64, 8, 4),
    ]
    L2_config = [
        CacheConfig(512, 8, 8),
        CacheConfig(512, 8, 8),
    ]
    LLC_config = [
        CacheConfig(2048, 16, 20),
        CacheConfig(4096, 16, 21),
    ]

    # Initialize the ChampSimRunner
    champ_sim_runner = ChampSimRunner(
        champ_sim_path=champ_sim_path,
        trace_dir=trace_dir,
        config_file=config_file,
        output_dir=output_dir,
        policies=policies,
        prefetchers=prefetchers,
        branch_predictors=branches,
        threads=threads,
        warmup_instructions=warmup_instructions,
        simulation_instructions=simulation_instructions,
        L1I_Config=L1I_config,
        L1D_Config=L1D_config,
        L2_Config=L2_config,
        LLC_Config=LLC_config
    )

    # Execute all policies for the given traces
    champ_sim_runner.execute_all_policies(trace_urls)


if __name__ == "__main__":
    main()