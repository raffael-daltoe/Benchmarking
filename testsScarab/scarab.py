import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import threading
import sys
import re
import time

###############################################################################
# Helper class for Cache Config
###############################################################################
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


class ScarabExecutor:
    def __init__(
        self,
        scarab_path,
        policies,
        policies_Cache,
        branch_predictors,
        prefetchers,
        prefetchers_names,
        policies_Cache_names,
        threads,
        trace_dir,
        output_dir,
        simulation_instructions,
        warmup,
        param,
        L1I_config,   # List of CacheConfig objects for L1I
        L1D_config,   # List of CacheConfig objects for L1D
        L2_config,    # List of CacheConfig objects for L2
        LLC_config,   # List of CacheConfig objects for LLC
    ):
        self.scarab_path = scarab_path
        self.policies = policies
        self.policies_cache = policies_Cache
        self.branch_predictors = branch_predictors
        self.prefetchers = prefetchers
        self.prefetchers_names = prefetchers_names
        self.cache_policy_map = policies_Cache_names
        self.threads = threads
        self.trace_dir = trace_dir
        self.output_dir = output_dir
        self.output_dir_orig = output_dir
        self.simulation_instructions = simulation_instructions
        self.warmup_instructions = warmup
        self.param = param

        # Semaphores if needed
        self.S1_semaphore = threading.Semaphore(1)
        self.S2_semaphore = threading.Semaphore(1)
        self.S3_semaphore = threading.Semaphore(1)
        self.S4_semaphore = threading.Semaphore(1)
        self.S5_semaphore = threading.Semaphore(1)

        # Create a list of cache configuration tuples from the four lists
        # Each tuple is (L1I_cfg, L1D_cfg, L2_cfg, LLC_cfg).
        self.cache_samples = list(zip(L1I_config, L1D_config, L2_config, LLC_config))

    ###########################################################################
    # Modify cache sizes in PARAMS.in
    ###########################################################################
    def modify_cache_size(self, L1I, L1D, L2, LLC):
        """
        Modify the textual PARAMS.in file to reflect the new sets/ways/latency
        for L1I, L1D, L2 (mlc), and LLC (which is listed as `--l1_size` in the file).
        """
        time.sleep(0.5)
        self.S1_semaphore.acquire()
        # 1) Read original param file
        with open(self.param, "r") as f:
            content = f.read()

        # 2) Compute new sizes in bytes (assuming 64-byte lines)
        new_icache_size = L1I.sets * L1I.ways * 64
        new_dcache_size = L1D.sets * L1D.ways * 64
        new_mlc_size    = L2.sets * L2.ways * 64
        new_l1_size     = LLC.sets * LLC.ways * 64  # "LLC" is named l1_size in your file

        # 3) Prepare new assoc
        new_icache_assoc = L1I.ways
        new_dcache_assoc = L1D.ways
        new_mlc_assoc    = L2.ways
        new_l1_assoc     = LLC.ways

        # 4) Prepare latencies
        #  (The example shows `--dcache_cycles`, `--mlc_cycles`, `--l1_cycles` in the param file)
        new_dcache_cycles = L1D.latency
        new_mlc_cycles    = L2.latency
        new_l1_cycles     = LLC.latency
        # There's no explicit iCache latency in your snippet, so we skip it unless you add it.

        # 5) Regex substitutions
        content = re.sub(r"--icache_size\s+\d+",       f"--icache_size {new_icache_size}", content)
        content = re.sub(r"--icache_assoc\s+\d+",      f"--icache_assoc {new_icache_assoc}", content)

        content = re.sub(r"--dcache_size\s+\d+",       f"--dcache_size {new_dcache_size}", content)
        content = re.sub(r"--dcache_assoc\s+\d+",      f"--dcache_assoc {new_dcache_assoc}", content)
        content = re.sub(r"--dcache_cycles\s+\d+",     f"--dcache_cycles {new_dcache_cycles}", content)

        content = re.sub(r"--mlc_size\s+\d+",          f"--mlc_size {new_mlc_size}", content)
        content = re.sub(r"--mlc_assoc\s+\d+",         f"--mlc_assoc {new_mlc_assoc}", content)
        content = re.sub(r"--mlc_cycles\s+\d+",        f"--mlc_cycles {new_mlc_cycles}", content)

        content = re.sub(r"--l1_size\s+\d+",           f"--l1_size {new_l1_size}", content)
        content = re.sub(r"--l1_assoc\s+\d+",          f"--l1_assoc {new_l1_assoc}", content)
        content = re.sub(r"--l1_cycles\s+\d+",         f"--l1_cycles {new_l1_cycles}", content)

        # 6) Write the updated content back to PARAMS.in
        with open(self.param, "w") as f:
            f.write(content)

    ###########################################################################
    # Existing replacement modifications
    ###########################################################################
    def modify_replacement_cache(self, new_policy):
        time.sleep(0.5)
        self.S2_semaphore.acquire()

        with open(self.param, 'r') as file:
            content = file.read()

        patterns = [
            r"--l1_cache_repl_policy\s+\S+",
            #r"--mlc_cache_repl_policy\s+\S+",
            #r"--dcache_repl\s+\S+",
            #r"--icache_repl\s+\S+"
        ]

        updated_content = content
        for pattern in patterns:
            param_name = pattern.split('--')[1].split('\\')[0]
            replacement = f"--{param_name} {new_policy}"
            updated_content = re.sub(pattern, replacement, updated_content)

        with open(self.param, 'w') as file:
            file.write(updated_content)

    def modify_branch_predictor(self, new_branch):
        time.sleep(0.5)
        self.S3_semaphore.acquire()

        with open(self.param, 'r') as file:
            content = file.read()

        patterns = [
            r"--bp_mech\s+\S+",
        ]

        updated_content = content
        for pattern in patterns:
            param_name = pattern.split('--')[1].split('\\')[0]
            replacement = f"--{param_name} {new_branch}"
            updated_content = re.sub(pattern, replacement, updated_content)

        with open(self.param, 'w') as file:
            file.write(updated_content)

    def modify_prefetcher(self, prefetcher):
        """
        Modifies the selected prefetcher in the PARAMS.in file.
        Only one prefetcher is enabled at a time (others set to 0).
        
        Available prefetchers:
        - "0": Enables --pref_stride_on
        - "1": Enables --pref_stridepc_on
        - "2": Enables --pref_ghb_on
        """
        time.sleep(0.5)
        self.S4_semaphore.acquire()

        prefetcher_map = {
            "0": {"--pref_stride_on": "1", "--pref_stridepc_on": "0", "--pref_ghb_on": "0"},
            "1": {"--pref_stride_on": "0", "--pref_stridepc_on": "1", "--pref_ghb_on": "0"},
            "2": {"--pref_stride_on": "0", "--pref_stridepc_on": "0", "--pref_ghb_on": "1"},
        }

        # Validate input
        if prefetcher not in prefetcher_map:
            print(f"Invalid Prefetcher Option: {prefetcher}. Exiting...")
            sys.exit(1)

        with open(self.param, 'r') as file:
            content = file.read()

        # Update prefetcher settings dynamically
        for key, value in prefetcher_map[prefetcher].items():
            content = re.sub(rf"{key}\s+\S+", f"{key} {value}", content)

        # Write the updated content back to the file
        with open(self.param, 'w') as file:
            file.write(content)
            
    def modify_replacement_policy(self, new_policy):
        time.sleep(0.5)
        self.S5_semaphore.acquire()
        with open(self.param, 'r') as file:
            content = file.read()

        pattern = r"(--ramulator_scheduling_policy\s+)\S+"
        updated_content = re.sub(pattern, rf"\1{new_policy}", content)

        with open(self.param, 'w') as file:
            file.write(updated_content)

    def write_file(self):
        scarab_output_path = os.path.join(self.scarab_path, "src/PARAMS.in")
        local_output_path = os.path.join(os.getcwd(), "PARAMS.in")

        with open(self.param, 'r') as original_file:
            original_content = original_file.read()

        # Write to both output paths
        for output_path in [scarab_output_path, local_output_path]:
            with open(output_path, 'w') as modified_file:
                modified_file.write(original_content)

        # Release the semaphores if needed
        self.S1_semaphore.release()
        self.S2_semaphore.release()
        self.S3_semaphore.release()
        self.S4_semaphore.release()
        self.S5_semaphore.release()
        

    ###########################################################################
    # Running Scarab
    ###########################################################################
    def exec_single_trace(self, trace_file, trace_path, policy_Cache):
        policy_Cache_name = self.cache_policy_map.get(policy_Cache, policy_Cache)
        trace_name = os.path.splitext(trace_file)[0]
        bin_dir = os.path.abspath(os.path.join(trace_path, "../../bin"))
        trace_output_dir = os.path.join(self.output_dir, trace_name, policy_Cache_name)
        os.makedirs(trace_output_dir, exist_ok=True)

        command = [
            os.path.join(self.scarab_path, "src/scarab"),
            "--frontend", "memtrace",
            "--fetch_off_path_ops", "0",
            f"--cbp_trace_r0={trace_path}",
            f"--inst_limit={self.simulation_instructions}",
            f"--memtrace_modules_log={bin_dir}",
            f"--output_dir={trace_output_dir}"
        ]

        print(f"[INFO] Executing Scarab for {trace_file} with command:")
        print("       " + " ".join(command))

        subprocess.run(command)

    def prepare_execution(self, executor, policy_Cache, trace_folder):
        for trace_file in os.listdir(trace_folder):
            if trace_file.endswith('.trace.gz') or trace_file.endswith('.champsimtrace.xz'):
                trace_path = os.path.join(trace_folder, trace_file)
                executor.submit(self.exec_single_trace, trace_file, trace_path, policy_Cache)

    ###########################################################################
    # Main entry to run all experiments
    ###########################################################################
    def execute_all_traces(self):
        """
            For each cache configuration sample:
            1) Modify the cache sizes in PARAMS.in
            2) Create a subfolder named Sample{index} for that config.
            3) For each memory-policy and cache-policy combination, modify those in
                PARAMS.in, write out, and then run all the traces in parallel.
        """
        os.makedirs(self.output_dir, exist_ok=True)

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for index, (L1I_cfg, L1D_cfg, L2_cfg, LLC_cfg) in enumerate(self.cache_samples, start=5):
                sample_folder = os.path.join(self.output_dir_orig, f"Sample{index}")
                os.makedirs(sample_folder, exist_ok=True)

                self.modify_cache_size(L1I_cfg, L1D_cfg, L2_cfg, LLC_cfg)

                # 3) For each directory in your trace path, do the standard loop
                for trace_subdir in os.listdir(self.trace_dir):
                    full_subdir_path = os.path.join(self.trace_dir, trace_subdir)
                    if os.path.isdir(full_subdir_path):
                        trace_folder = os.path.join(full_subdir_path, 'trace')
                        if os.path.exists(trace_folder):
                                # For each cache replacement policy
                            for policy_Cache in self.policies_cache or [None]:
                                # For each Branch Predictor
                                for branch in self.branch_predictors or [None]:
                                    branch_folder = os.path.join(sample_folder,f"{branch}")
                                    os.makedirs(branch_folder, exist_ok=True)
                                    # For each prefetcher
                                    for prefetcher in self.prefetchers or [None]:
                                        prefetcher_name = self.prefetchers_names.get(prefetcher, f"{prefetcher}")
                                        prefetcher_folder = os.path.join(branch_folder, prefetcher_name)
                                        os.makedirs(prefetcher_folder, exist_ok=True)

                                        # Apply the L1/MLC/DCache replacement policy
                                        self.modify_replacement_cache(policy_Cache)
                                        # Apply the Branch predictor
                                        self.modify_branch_predictor(branch) 
                                        # Apply the Preftecher
                                        self.modify_prefetcher(prefetcher)

                                        # Write out final param changes (PARAMS.in)
                                        self.write_file()

                                        self.output_dir = prefetcher_folder
                                            
                                        #   2) Now launch the traces in parallel
                                        self.prepare_execution(
                                            executor, policy_Cache, trace_folder
                                        )
                                        


def is_number(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def main():
    if len(sys.argv) < 8:
        print("Usage: python3 script.py <threads> <scarab_path> <trace_dir> "
              "<output_dir> <simulation_instructions> <warmup> <param>")
        sys.exit(1)

    try:
        threads = int(sys.argv[1])
        if threads < 1:
            raise ValueError
    except ValueError:
        print("Please provide a valid number of threads.")
        sys.exit(1)

    scarab_path = sys.argv[2]
    trace_dir = sys.argv[3]
    output_dir = sys.argv[4]
    simulation_instructions = int(sys.argv[5]) if (len(sys.argv) > 5 and is_number(sys.argv[5])) else None
    warmup = sys.argv[6]
    param_file = sys.argv[7]

    # Example sets of DRAM scheduling policies:
    policies = ["FCFS", "FRFCFS", "FRFCFS_Cap", "FRFCFS_PriorHit"]
    
    # Example sets of cache-level replacement policies:
    policies_Cache = ["0", "1", "3"]
    policies_Cache_names =  {
        "0": "REPL_TRUE_LRU",
        "1": "REPL_RANDOM",
        "3": "REPL_ROUND_ROBIN"
    }
    
    branch_predictors = ["gshare","tagescl"]

    # Prefetchers  ["pref_stride_on","pref_stridepc_on"]
    prefetchers = ["0","1"]
    prefetchers_names = {
        "0": "stride",
        "1": "stridepc"
    }

    # ----------------------------------------------------------
    #  Define your new cache configuration lists in main
    # ----------------------------------------------------------
    # Example cache configurations
    L1I_config = [
        #CacheConfig(64, 8, 4),
        #CacheConfig(64, 8, 4),
        #CacheConfig(64, 8, 4),
        #CacheConfig(64, 8, 4),
        CacheConfig(64, 8, 4),
    ]
    L1D_config = [
        #CacheConfig(64, 8, 4),
        #CacheConfig(64, 12, 5),
        #CacheConfig(64, 8, 4),
        #CacheConfig(64, 8, 4),
        CacheConfig(64, 12, 4),
    ]
    L2_config = [
        #CacheConfig(512, 8, 8),
        #CacheConfig(820, 8, 8),
        #CacheConfig(512, 8, 8),
        #CacheConfig(512, 8, 8),
        CacheConfig(1024, 8, 15),
    ]
    LLC_config = [
        #CacheConfig(2048, 16, 20),
        #CacheConfig(2048, 16, 22),
        #CacheConfig(4096, 16, 21),
        #CacheConfig(8192, 16, 22),
        CacheConfig(2048, 16, 45),
    ]

    # Construct the ScarabExecutor with these lists
    scarab_executor = ScarabExecutor(
        scarab_path=scarab_path,
        policies=policies,
        policies_Cache=policies_Cache,
        branch_predictors = branch_predictors,
        prefetchers=prefetchers,
        prefetchers_names = prefetchers_names,
        policies_Cache_names = policies_Cache_names,
        threads=threads,
        trace_dir=trace_dir,
        output_dir=output_dir,
        simulation_instructions=simulation_instructions,
        warmup=warmup,
        param=param_file,
        L1I_config=L1I_config,
        L1D_config=L1D_config,
        L2_config=L2_config,
        LLC_config=LLC_config,
    )

    # Kick off the entire run
    scarab_executor.execute_all_traces()

if __name__ == "__main__":
    main()

