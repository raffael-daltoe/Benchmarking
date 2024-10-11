import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import sys

# You may not need the semaphore unless necessary for resource locking
# S1_replacement = threading.Semaphore(1)

# Function to execute a single trace
def exec_single_trace(trace_file, trace_path, output_dir, 
                      scarab_path, simulation_instructions):
    trace_name = os.path.splitext(trace_file)[0]

    # Compute the path to the 'bin' folder, which is two levels up from trace_path
    bin_dir = os.path.abspath(os.path.join(trace_path, "../../bin"))

    # Create the output directory for this trace_name
    trace_output_dir = os.path.join(output_dir, trace_name)
    if not os.path.exists(trace_output_dir):
        os.makedirs(trace_output_dir)

    # Scarab command to execute
    command = [
        os.path.join(scarab_path, "src/scarab"),
        "--frontend", "memtrace",
        "--fetch_off_path_ops", "0",
        f"--cbp_trace_r0={trace_path}",
        f"--inst_limit={simulation_instructions}",
        f"--memtrace_modules_log={bin_dir}",
        f"--output_dir={trace_output_dir}"  # Ensure this directory is used
    ]

    print(f"Executing Scarab for {trace_file} with command: {' '.join(command)}")

    # If semaphore is used, it should be released after subprocess starts
    # S1_replacement.release()

    subprocess.run(command)
    

# Function to execute traces for all directories in the trace folder
def exec_all_traces(trace_dir, output_dir, scarab_path, 
                    simulation_instructions, threads):
    # Create output directory if not exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create the ThreadPoolExecutor ONCE, outside the loop
    with ThreadPoolExecutor(max_workers=threads) as executor:
        # Iterate through each subdirectory in the trace directory
        for trace_subdir in os.listdir(trace_dir):
            full_subdir_path = os.path.join(trace_dir, trace_subdir)
            
            # Check if it's a directory and contains a 'trace' folder
            if os.path.isdir(full_subdir_path):
                trace_folder = os.path.join(full_subdir_path, 'trace')
                
                # Ensure 'trace' folder exists inside the subdirectory
                if os.path.exists(trace_folder):
                    # Iterate over all trace files inside the 'trace' folder
                    for trace_file in os.listdir(trace_folder):
                        if trace_file.endswith('.trace.gz') or trace_file.endswith('.champsimtrace.xz'):
                            trace_path = os.path.join(trace_folder, trace_file)
                            print(f"Submitting trace for processing: {trace_path}")
                            # Submit the task to the thread pool for parallel execution
                            executor.submit(exec_single_trace, 
                                            trace_file, trace_path, output_dir, 
                                            scarab_path, simulation_instructions)
                            # You can adjust or remove this sleep if necessary
                            time.sleep(0.5)

def is_number(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

# Main function to execute all steps
def main():
    if len(sys.argv) < 5:
        print("Usage: python3 script.py <number_of_threads> <scarab_path> \
              <trace_dir> <output_dir> <simulation_instructions>")
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

    simulation_instructions = int(sys.argv[5]) if len(sys.argv) > 5 \
        and is_number(sys.argv[5]) else None

    exec_all_traces(trace_dir, output_dir, scarab_path, 
                    simulation_instructions, threads)

if __name__ == "__main__":
    main()
