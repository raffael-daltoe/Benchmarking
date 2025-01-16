import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import threading
import sys
import re
import time

class ScarabExecutor:
    def __init__(self, scarab_path, policies, policies_Cache,
                 threads, trace_dir, output_dir,
                 simulation_instructions, warmup, param):
        self.scarab_path = scarab_path
        self.policies = policies
        self.policies_cache = policies_Cache
        self.threads = threads
        self.trace_dir = trace_dir
        self.output_dir = output_dir
        self.simulation_instructions = simulation_instructions
        self.warmup_instructions = warmup
        self.param = param
        self.modified_config = None
        self.S1_semaphore = threading.Semaphore(1)
        self.S2_semaphore = threading.Semaphore(1)

    def exec_single_trace(self, trace_file, trace_path, policy_MM, policy_Cache):
        trace_name = os.path.splitext(trace_file)[0]
        bin_dir = os.path.abspath(os.path.join(trace_path, "../../bin"))
        trace_output_dir = os.path.join(self.output_dir, trace_name, policy_MM, policy_Cache)
        os.makedirs(trace_output_dir, exist_ok=True)

        command = [
            os.path.join(self.scarab_path, "src/scarab"),
            "--frontend", "memtrace",
            "--fetch_off_path_ops", "0",
            f"--cbp_trace_r0={trace_path}",
            f"--warmup={self.warmup_instructions}",
            f"--inst_limit={self.simulation_instructions}",
            f"--memtrace_modules_log={bin_dir}",
            f"--output_dir={trace_output_dir}"
        ]

        print(f"Executing Scarab for {trace_file} with command: {' '.join(command)}")

        self.S1_semaphore.release()
        self.S2_semaphore.release()
        subprocess.run(command)

    def modify_replacement_cache(self, new_policy):
        time.sleep(2)
        self.S1_semaphore.acquire()

        with open(self.param, 'r') as file:
            content = file.read()

        pattern = r"(--(?:l1_cache_repl_policy|icache_repl|dcache_repl)\s+)\S+"
        updated_content = re.sub(pattern, rf"\1{new_policy}", content)

        with open(self.param, 'w') as file:
            file.write(updated_content)

        self.modified_config = {
            'l1_cache_repl_policy': new_policy,
            'icache_repl': new_policy,
            'dcache_repl': new_policy
        }

    def modify_replacement_policy(self, new_policy):
        time.sleep(2)
        self.S2_semaphore.acquire()

        with open(self.param, 'r') as file:
            content = file.read()

        pattern = r"(--ramulator_scheduling_policy\s+)\S+"
        updated_content = re.sub(pattern, rf"\1{new_policy}", content)

        with open(self.param, 'w') as file:
            file.write(updated_content)

        if self.modified_config:
            self.modified_config['ramulator_scheduling_policy'] = new_policy
        else:
            self.modified_config = {'ramulator_scheduling_policy': new_policy}

    def write_file(self):
        output_path = os.path.join(self.scarab_path, "src/PARAMS.in")

        with open(self.param, 'r') as original_file:
            original_content = original_file.read()

        with open(output_path, 'w') as modified_file:
            if self.modified_config:
                for key, value in self.modified_config.items():
                    pattern = rf"(--{key}\s+)\S+"
                    original_content = re.sub(pattern, rf"\1{value}", original_content)

            modified_file.write(original_content)

        print(f"Configuration file written to {output_path}")

    def prepare_execution(self, executor, policy_MM, policy_Cache,trace_folder):
        for trace_file in os.listdir(trace_folder):
            if trace_file.endswith('.trace.gz') or trace_file.endswith('.champsimtrace.xz'):
                print(f"final here, with: {self.trace_dir} and {trace_file}")
                trace_path = os.path.join(trace_folder, trace_file)
                print(f"Submitting trace for processing: {trace_path} with MM = {policy_MM} and Cache = {policy_Cache} replacements")
                executor.submit(self.exec_single_trace, trace_file, trace_path, policy_MM, policy_Cache)

    def execute_all_traces(self):
        os.makedirs(self.output_dir, exist_ok=True)

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for trace_subdir in os.listdir(self.trace_dir):
                full_subdir_path = os.path.join(self.trace_dir, trace_subdir)
            
                if os.path.isdir(full_subdir_path):
                    trace_folder = os.path.join(full_subdir_path, 'trace')
                    if os.path.exists(trace_folder):
                        if len(self.policies) != 0:
                            for policy_MM in self.policies:
                                if len(self.policies_cache) != 0:
                                    for policy_Cache in self.policies_cache:
                                        self.modify_replacement_policy(policy_MM)
                                        self.modify_replacement_cache(policy_Cache)
                                        self.write_file()
                                        self.prepare_execution(executor, policy_MM, policy_Cache,trace_folder)

def is_number(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def main():
    if len(sys.argv) < 7:
        print("Usage: python3 script.py <number_of_threads> <scarab_path> <trace_dir> <output_dir> <simulation_instructions> <warmup> <param>")
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
    simulation_instructions = int(sys.argv[5]) if len(sys.argv) > 5 and is_number(sys.argv[5]) else None
    warmup = sys.argv[6]
    param = sys.argv[7]

    policies = ["FCFS", "FRFCFS", "FRFCFS_Cap", "FRFCFS_PriorHit"]
    policies_Cache = ["REPL_TRUE_LRU", "REPL_RANDOM", "REPL_NOT_MRU", "REPL_ROUND_ROBIN", "REPL_IDEAL", "REPL_ISO_PREF", "REPL_LOW_PREF", "REPL_SHADOW_IDEAL", "NUM_REPL", "REPL_IDEAL_STORAGE", "REPL_MLP", "REPL_PARTITION"]

    scarab_executor = ScarabExecutor(scarab_path, policies, policies_Cache, threads, trace_dir, output_dir, simulation_instructions, warmup, param)
    scarab_executor.execute_all_traces()

if __name__ == "__main__":
    main()
