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
import shutil


class CacheConfig:
    """
    Stores cache configuration details for each level:
      - sets
      - ways
      - latency
    """
    def __init__(self, sets, ways, latency):
        self.sets = sets
        self.ways = ways
        self.latency = latency
        self.block_size = 64
        self.calculate = self.block_size * self.sets * self.ways
        self.size = self.get_size_readable()

    def get_size_readable(self):
        """
        Returns cache size in readable format (B, kB, or MB) as an integer.
        """
        if self.calculate >= 1024 * 1024:
            return f"{self.calculate // (1024 * 1024)}MB"  # Integer division
        elif self.calculate >= 1024:
            return f"{self.calculate // 1024}kB"  # Integer division
        else:
            return f"{self.calculate}B"  # Already an integer

    

class GEM5Runner:
    def __init__(
        self,
        gem5_path: str,
        bin_dir: str,
        simulation_file: str,
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
        self.gem5_path = gem5_path
        self.bin_dir = bin_dir
        self.simulation_file = simulation_file
        self.config_bin_name = 'gem5.opt'
        self.config_ISA = "X86/"
        self.config_bin_gem5 = self.gem5_path + "/build/" + self.config_ISA + \
                                                            self.config_bin_name
        self.path_from_gem5_to_binaries = "../../../../../../../../testsGem5/" + \
                                        self.bin_dir

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
        self.modified_config = None  
        self.modified_config_simulate = None
        self.system_file_name = 'my_system.py'
        self.simulate_file = 'simulate.py'

        self.L1I_Config = L1I_Config or []
        self.L1D_Config = L1D_Config or []
        self.L2_Config = L2_Config or []
        self.LLC_Config = LLC_Config or []

        # Group all cache configs into a single list of 4-tuples
        self.Samples = list(zip(self.L1I_Config, self.L1D_Config, 
                                self.L2_Config, self.LLC_Config))
        

    def modify_size_cache(self, L1I, L1D, L2C, LLC):
        """
        Modify cache configurations (L1I, L1D, L2, LLC) in the my_system.py file.
        
        Parameters:
            - L1I (CacheConfig): L1 Instruction cache configuration
            - L1D (CacheConfig): L1 Data cache configuration
            - L2C (CacheConfig): L2 cache configuration
            - LLC (CacheConfig): Last-level cache (L3) configuration
        """
        
        my_system_path = os.path.join(self.simulation_file, self.system_file_name)

        with open(my_system_path, 'r') as file:
            content = file.read()
    
        # Regex patterns for modifying cache configurations
        patterns = {
            "L1I": {
                "size": r"(self\.cpu\.icache\.size\s*=\s*)['\"]\S+",
                "assoc": r"(self\.cpu\.icache\.assoc\s*=\s*)\d+\S+",
                "mshrs": r"(self\.cpu\.icache\.mshrs\s*=\s*)\d+\S+",
                "tag_latency": r"(self\.cpu\.icache\.tag_latency\s*=\s*)\d+\S+",
                "data_latency": r"(self\.cpu\.icache\.data_latency\s*=\s*)\d+\S+",
                "response_latency": r"(self\.cpu\.icache\.response_latency\s*=\s*)\d+\S+",
            },
            "L1D": {
                "size": r"(self\.cpu\.dcache\.size\s*=\s*)['\"]\S+",
                "assoc": r"(self\.cpu\.dcache\.assoc\s*=\s*)\d+\S+",
                "mshrs": r"(self\.cpu\.dcache\.mshrs\s*=\s*)\d+\S+",
                "tag_latency": r"(self\.cpu\.dcache\.tag_latency\s*=\s*)\d+\S+",
                "data_latency": r"(self\.cpu\.dcache\.data_latency\s*=\s*)\d+\S+",
                "response_latency": r"(self\.cpu\.dcache\.response_latency\s*=\s*)\d+\S+",
            },
            "L2": {
                "size": r"(self\.l2cache\.size\s*=\s*)['\"]\S+",
                "assoc": r"(self\.l2cache\.assoc\s*=\s*)\d+\S+",
                "mshrs": r"(self\.l2cache\.mshrs\s*=\s*)\d+\S+",
                "tag_latency": r"(self\.l2cache\.tag_latency\s*=\s*)\d+\S+",
                "data_latency": r"(self\.l2cache\.data_latency\s*=\s*)\d+\S+",
                "response_latency": r"(self\.l2cache\.response_latency\s*=\s*)\d+\S+",
            },
            "LLC": {  # L3 Cache
                "size": r"(self\.l3cache\.size\s*=\s*)['\"]\S+",
                "assoc": r"(self\.l3cache\.assoc\s*=\s*)\d+\S+",
                "mshrs": r"(self\.l3cache\.mshrs\s*=\s*)\d+\S+",
                "tag_latency": r"(self\.l3cache\.tag_latency\s*=\s*)\d+\S+",
                "data_latency": r"(self\.l3cache\.data_latency\s*=\s*)\d+\S+",
                "response_latency": r"(self\.l3cache\.response_latency\s*=\s*)\d+\S+",
            }
        }

        # Define new values from arguments
        new_values = {
            "L1I": L1I,
            "L1D": L1D,
            "L2": L2C,
            "LLC": LLC,
        }

        # Apply replacements using regex
        # Apply replacements using regex
        for cache, params in patterns.items():
            cache_config = new_values[cache]  # Get the CacheConfig object
            for param, pattern in params.items():
                # Ensure the attribute exists in the CacheConfig object
                if hasattr(cache_config, param):
                    value = getattr(cache_config, param)  # Get attribute value dynamically
                    if param == "size":
                        new_line = rf"\1'{value}'"
                    else:
                        new_line = rf"\1{value}"
                    content = re.sub(pattern, new_line, content)


        self.modified_config = content

        # Write the modified content back to the file
        #with open(my_system_path, 'w') as file:
        #    file.write(content)

    def modify_replacement_policy(self, policy: str, L3) -> None:
        """
        Modify the replacement policy in the L3 cache configuration 
        and update `self.modified_config` instead of writing directly to the file.

        Parameters:
            - policy (str): The new replacement policy (e.g., "DRRIP", "LRU", etc.).
            - L3: Object containing L3 cache parameters (must have `.size` and `.assoc` attributes).
        """
        time.sleep(0.2) 
        if not hasattr(self, "modified_config") or not self.modified_config:
            my_system_path = os.path.join(self.simulation_file, self.system_file_name)
            with open(my_system_path, "r") as file:
                self.modified_config = file.read()

        pattern = r"(self\.l3cache\.replacement_policy\s*=\s*)\S+\(.*?\)"

        if policy == "DRRIP":
            new_line = rf"\1DRRIPRP(constituency_size={L3.calculate}, team_size={L3.ways})"
        else:
            new_line = rf"\1{policy}()"

        self.modified_config = re.sub(pattern, new_line, self.modified_config)


    def modify_prefetcher(self, prefetcher) -> None:
        time.sleep(0.3)  # Optional delay if needed
        # Ensure `self.modified_config` is loaded (fallback to reading the file)
        if not hasattr(self, "modified_config") or not self.modified_config:
            my_system_path = os.path.join(self.simulation_file, self.system_file_name)
            with open(my_system_path, "r") as file:
                self.modified_config = file.read()

        # Define the regex pattern to locate the existing replacement policy assignment
        pattern = r"(self\.l3cache\.prefetcher\s*=\s*)\S+"

        new_line = rf"\1{prefetcher}()"

        # Perform the replacement in `self.modified_config`
        self.modified_config = re.sub(pattern, new_line, self.modified_config)

    def modify_branch(self, branch) -> None:
        time.sleep(0.35)  # Optional delay if needed

        # Ensure `self.modified_config` is loaded (fallback to reading the file)
        if not hasattr(self, "modified_config") or not self.modified_config:
            my_system_path = os.path.join(self.simulation_file, self.system_file_name)
            with open(my_system_path, "r") as file:
                self.modified_config = file.read()

        # Define the regex pattern to locate the existing replacement policy assignment
        pattern = r"(self\.cpu\.branchPred\s*=\s*)\S+"
        new_line = rf"\1{branch}()"

        self.modified_config = re.sub(pattern, new_line, self.modified_config)

    def modify_simulate_py(self, binary) -> None:
        """
        Modify the `simulate.py` file to update the binary path and the 
        instruction limit (system.cpu.max_insts_any_thread).
        """
        path_to_bin = os.path.join(self.path_from_gem5_to_binaries, binary)
        simulate_path = os.path.join(self.simulation_file, "simulate.py")

        with open(simulate_path, 'r') as file:
            content = file.read()

        # Regex pattern to replace the binary path
        binpath_pattern = r'binpath\s*=\s*os\.path\.join\(thispath,\s*["\'].*?["\']\)'
        new_binpath_line = f'binpath = os.path.join(thispath, "{path_to_bin}")'

        # Ensure the instruction limit modification works correctly
        inst_limit_pattern = r'system\.cpu\.max_insts_any_thread\s*=\s*\d+'
        new_inst_limit_line = f'system.cpu.max_insts_any_thread = {self.simulation_instructions}'

        # Apply modifications
        modified_content = re.sub(binpath_pattern, new_binpath_line, content)
        modified_content = re.sub(inst_limit_pattern, new_inst_limit_line, modified_content)

        self.modified_config_simulate = modified_content




    def write_modified_config(self, index, binary, branch, prefetcher, policy) -> None:
        """
        Write the modified configurations (`modified_config` and `modified_config_simulate`)
        to the appropriate destination.
        """
        if not hasattr(self, "modified_config") or not self.modified_config:
            print("No configuration changes to write.")
            return
        
        dir_files_simulation = os.path.join(self.gem5_path, "configs", binary, f"Sample{index}", branch, prefetcher, policy)
        dir_files_output = os.path.join(self.output_dir, binary, f"Sample{index}", branch, prefetcher, policy)

        os.makedirs(dir_files_output, exist_ok=True)
        os.makedirs(dir_files_simulation, exist_ok=True)

        dest_dir = os.path.join(dir_files_simulation)
        simulation_files = os.listdir(self.simulation_file)

        for filename in simulation_files:
            src_path = os.path.join(self.simulation_file, filename)
            dest_path = os.path.join(dest_dir, filename)
            
            # Only copy files (not directories)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dest_path)

        # Write the modified my_system.py file
        modified_file_path = os.path.join(dest_dir, self.system_file_name)
        with open(modified_file_path, "w") as file:
            file.write(self.modified_config)
        
        # Write the modified simulate.py file
        modified_simulate_path = os.path.join(dest_dir, "simulate.py")
        with open(modified_simulate_path, "w") as file:
            file.write(self.modified_config_simulate)
        
        return dest_dir, dir_files_output


        
    def exec_bin(
        self,
        policy: Optional[str],
        branch: Optional[str],
        prefetcher: Optional[str],
        binary : Optional[str],
        exec_dir_files : Optional[str],
        dir_files_output : Optional[str]
    ) -> None:
        
        bin = os.path.join(self.config_bin_gem5)

        command = [bin]

        command += ["-d",str(dir_files_output)]

        execution = exec_dir_files + '/' + self.simulate_file

        command += [execution]

        subprocess.run(command)
        self.SGlobal.release()


    def execute_all_policies(self) -> None:
        # Ensure output directory
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for binary in os.listdir(self.bin_dir):
                for index, sample in enumerate(self.Samples, start=5):
                    L1I, L1D, L2C, L3 = sample

                    # Each sample set has its own folder
                    sample_folder = os.path.join(self.output_dir_orig, f"Sample{index}")
                    if not os.path.exists(sample_folder):
                        os.makedirs(sample_folder)
                    self.output_dir = sample_folder

                    # Modify cache sizes
                    self.modify_size_cache(L1I, L1D, L2C, L3)

                    # For each combination of policies/prefetchers/branch
                    # If you only want to run certain fields, you can just
                    # leave them empty or pass None to skip.
                    for policy in self.policies or [None]:
                        for prefetcher in self.prefetchers or [None]:
                            for branch in self.branch_predictors or [None]:
                                # Do JSON modifications
                                
                                self.modify_replacement_policy(policy,L3)
                                self.modify_prefetcher(prefetcher)
                                self.modify_branch(branch)
                                self.modify_simulate_py(binary)

                                exec_dir_files,dir_files_output = \
                                    self.write_modified_config(index,binary,
                                                              branch,prefetcher,
                                                              policy)
                                self.SGlobal.acquire()
                                # Launch parallel jobs for each trace

                                executor.submit(self.exec_bin, policy, branch, 
                                            prefetcher,binary,exec_dir_files,
                                            dir_files_output)



def main():

    """
    Example usage:
        python3 script.py <threads> <gem5_path> <binary_dir>
                          <file_directory_system> <simulation_output>
                          <warmup_instructions> <simulation_instructions>
    """
    if len(sys.argv) < 6:
        print(
            "Usage: python3 script.py <threads> <gem5_path> <binary_dir> "
            "<file_directory_system> <simulation_output> "
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

    gem5_path = sys.argv[2]
    binary_dir = sys.argv[3]
    my_system_dir = sys.argv[4]
    output_dir = sys.argv[5]

    warmup_instructions = (
        int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6].isdigit() else None
    )
    simulation_instructions = (
        int(sys.argv[7]) if len(sys.argv) > 7 and sys.argv[7].isdigit() else None
    )

    policies = ["LRURP","RandomRP","FIFORP","BIPRP","DRRIP","SHiPMemRP"]
    
    prefetchers = ["TaggedPrefetcher","StridePrefetcher"]

    branches = ["BiModeBP", "GshareBP", "TAGE"]

    # ----------------------------------------------------------
    #  Define your new cache configuration lists in main
    # ----------------------------------------------------------
    # Example cache configurations
    L1I_config = [
        #CacheConfig(64, 8, 4),
        #CacheConfig(64, 8, 4),
        #CacheConfig(64, 8, 4),
        CacheConfig(64, 8, 4),
        #CacheConfig(64, 8, 4),
    ]
    L1D_config = [
        #CacheConfig(64, 8, 4),
        #CacheConfig(64, 12, 5),
        #CacheConfig(64, 8, 4),
        CacheConfig(64, 8, 4),
        #CacheConfig(64, 12, 4),
    ]
    L2_config = [
        #CacheConfig(512, 8, 8),
        #CacheConfig(820, 8, 8),
        #CacheConfig(512, 8, 8),
        CacheConfig(512, 8, 8),
        #CacheConfig(1024, 8, 15),
    ]
    LLC_config = [
        #CacheConfig(2048, 16, 20),
        #CacheConfig(2048, 16, 22),
        #CacheConfig(4096, 16, 21),
        CacheConfig(8192, 16, 22),
        #CacheConfig(2048, 16, 45),
    ]

    # Initialize the ChampSimRunner
    gem5_runner = GEM5Runner(
        gem5_path=gem5_path,
        bin_dir=binary_dir,
        simulation_file=my_system_dir,
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

    gem5_runner.execute_all_policies()


if __name__ == "__main__":
    main()