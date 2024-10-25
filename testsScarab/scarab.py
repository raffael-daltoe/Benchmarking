import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import sys

class ScarabExecutor:
    def __init__(self, scarab_path, policies):
        self.scarab_path = scarab_path
        self.policies = policies
        self.semaphore = threading.Semaphore(1)
        self.modified_content = []

    def exec_single_trace(self, trace_file, trace_path, output_dir, simulation_instructions, policy):
        trace_name = os.path.splitext(trace_file)[0]

        # Compute the path to the 'bin' folder, which is two levels up from trace_path
        bin_dir = os.path.abspath(os.path.join(trace_path, "../../bin"))

        # Create the output directory for this trace_name and policy
        trace_output_dir = os.path.join(output_dir, trace_name, policy)
        os.makedirs(trace_output_dir, exist_ok=True)

        # Scarab command to execute
        command = [
            os.path.join(self.scarab_path, "src/scarab"),
            "--frontend", "memtrace",
            "--fetch_off_path_ops", "0",
            f"--cbp_trace_r0={trace_path}",
            f"--inst_limit={simulation_instructions}",
            f"--memtrace_modules_log={bin_dir}",
            f"--output_dir={trace_output_dir}"  # Ensure this directory is used
        ]

        print(f"Executing Scarab for {trace_file} with command: {' '.join(command)}")

        # Release the semaphore before starting the subprocess
        self.semaphore.release()
        subprocess.run(command)

    def modify_replacement_policy(self, config_file, policy):
        time.sleep(0.5)
        self.semaphore.acquire()

        with open(config_file, 'r') as file:
            lines = file.readlines()

        self.modified_content = [
            f"--ramulator_scheduling_policy\t{policy}\n" if line.startswith("--ramulator_scheduling_policy") else line
            for line in lines
        ]

        # Return the path where the new file will be saved
        #return os.path.join(self.scarab_path, 'src', os.path.basename(config_file))
        return config_file

    def write_file(self, file_path):
        param_scarab = os.path.join(self.scarab_path, 'src', os.path.basename(file_path))

        with open(param_scarab, 'w') as new_file:
            new_file.writelines(self.modified_content)
        print(f"File written to: {param_scarab}")

        parent_dir_path = os.path.join(os.path.dirname(file_path), "..", os.path.basename(file_path))
        parent_dir_path = os.path.abspath(parent_dir_path)

        with open(parent_dir_path, 'w') as parent_file:
            parent_file.writelines(self.modified_content)

    def prepare_execution(self, executor, output_dir, simulation_instructions, trace_folder, policy):
        for trace_file in os.listdir(trace_folder):
            if trace_file.endswith('.trace.gz') or trace_file.endswith('.champsimtrace.xz'):
                trace_path = os.path.join(trace_folder, trace_file)
                print(f"Submitting trace for processing: {trace_path} with {policy}")
                executor.submit(
                    self.exec_single_trace, trace_file, trace_path, output_dir,
                    simulation_instructions, policy
                )

    def modify_params(self, param, executor, output_dir, simulation_instructions, trace_folder):
        for policy in self.policies:
            file_to_be_written = self.modify_replacement_policy(param, policy)
            self.write_file(file_to_be_written)
            self.prepare_execution(executor, output_dir, simulation_instructions, trace_folder, policy)


def execute_all_traces(scarab_executor, trace_dir, output_dir, simulation_instructions, threads, param):
    # Create output directory if not exists
    os.makedirs(output_dir, exist_ok=True)

    with ThreadPoolExecutor(max_workers=threads) as executor:
        for trace_subdir in os.listdir(trace_dir):
            full_subdir_path = os.path.join(trace_dir, trace_subdir)
            
            if os.path.isdir(full_subdir_path):
                trace_folder = os.path.join(full_subdir_path, 'trace')
                
                if os.path.exists(trace_folder):
                    scarab_executor.modify_params(param, executor, output_dir, simulation_instructions, trace_folder)


def is_number(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def main():
    if len(sys.argv) < 7:
        print("Usage: python3 script.py <number_of_threads> <scarab_path> <trace_dir> <output_dir> <simulation_instructions> <param>")
        sys.exit(1)

    try:
        threads = int(sys.argv[1])
        if threads < 1:
            raise ValueError
    except ValueError:
        print("Please provide a valid number of threads.")
        sys.exit(1)

    # Get paths and instructions from command line arguments
    scarab_path = sys.argv[2]
    trace_dir = sys.argv[3]
    output_dir = sys.argv[4]
    simulation_instructions = int(sys.argv[5]) if len(sys.argv) > 5 and is_number(sys.argv[5]) else None
    param = sys.argv[6]

    policies = ["FCFS", "FRFCFS", "FRFCFS_Cap", "FRFCFS_PriorHit"]

    # Create an instance of the ScarabExecutor
    scarab_executor = ScarabExecutor(scarab_path, policies)

    execute_all_traces(scarab_executor, trace_dir, output_dir, simulation_instructions, threads, param)


if __name__ == "__main__":
    main()
