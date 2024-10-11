import os
import json
import requests
import subprocess
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import sys

# List of policies allowed in ChampSim
policies = ["lru", "drrip", "ship", "srrip"]

S1_replacement = threading.Semaphore(1)

# Function to download specific trace files
def download_traces(trace_dir, trace_urls):
    # Command to create the folder
    if not os.path.exists(trace_dir):
        os.makedirs(trace_dir)

    # Download the trace files specified in the list
    for file_url in trace_urls:
        file_name = file_url.split('/')[-1]
        file_path = os.path.join(trace_dir, file_name)

        if os.path.exists(file_path):
            print(f"File {file_name} already downloaded.")
        else:
            # Download each trace file
            print(f"Downloading {file_name} ...")
            with requests.get(file_url, stream=True) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"Downloaded {file_name}.")

# Function to modify the replacement policy in the configuration
def modify_replacement_policy(policy, config_file, champ_sim_path, threads):
    S1_replacement.acquire()

    with open(config_file, 'r') as file:
        config = json.load(file)

    config['LLC']['replacement'] = policy

    with open(config_file, 'w') as file:
        json.dump(config, file, indent=4)

    subprocess.run(["./config.sh", "champsim_config.json"], cwd=champ_sim_path)

    subprocess.run(["make", f"-j{threads}"], cwd=champ_sim_path, 
                    stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    print(f"Changed replacement policy to {policy}.")

# Function to execute a single trace with a specific replacement policy
def exec_single_trace_with_policy(trace_file, policy, trace_dir, output_dir, 
                champ_sim_path, warmup_instructions, simulation_instructions):
    trace_name = os.path.splitext(trace_file)[0]
    trace_path = os.path.join(trace_dir, trace_file)
    output_file = os.path.join(output_dir, f"{trace_name}_{policy}_output.txt")

   # Base command to execute ChampSim
    command = [os.path.join(champ_sim_path, "bin/champsim")]

    # Add warmup_instructions if provided
    if warmup_instructions:
        command.extend(["--warmup_instructions", str(warmup_instructions)])
    
    # Add simulation_instructions if provided
    if simulation_instructions:
        command.extend(["--simulation_instructions", 
                                                str(simulation_instructions)])
    
    # Always add the trace path at the end
    command.append(trace_path)

    # Execute ChampSim and capture output in a specific file for each trace
    print(f"Executing ChampSim for {trace_file} with policy {policy}...")
    with open(output_file, 'w') as outfile:
        S1_replacement.release()
        subprocess.run(command, stdout=outfile, stderr=outfile)
    
    print(f"Output: {trace_file} with policy {policy} stored in {output_file}")

# Function to execute all policies (drrip, ship, srrip) for all traces
def exec_all_policies(trace_dir, output_dir, champ_sim_path, config_file, 
            trace_urls, warmup_instructions, simulation_instructions, threads):
    # Create output directory if not exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    download_traces(trace_dir, trace_urls)

    # Create a thread pool and submit tasks
    with ThreadPoolExecutor(max_workers=threads) as executor:
        for policy in policies:
            modify_replacement_policy(policy, config_file, champ_sim_path, 
                                                                        threads)
            for trace_file in os.listdir(trace_dir):
                executor.submit(exec_single_trace_with_policy, 
                                trace_file, policy, trace_dir, output_dir, 
                                champ_sim_path, warmup_instructions, 
                                simulation_instructions)
                time.sleep(0.5)

def is_number(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

# Main function to execute all steps
def main():
    if len(sys.argv) < 6:
        print("Usage: python3 script.py <number_of_threads> <champsim_path> \
              <trace_dir> <config_file> <output_dir> <warmup_instructions> \
              <simulation_instructions>")
        sys.exit(1)

    try:
        threads = int(sys.argv[1])
        if threads < 1:
            raise ValueError
    except ValueError:
        print("Please provide a valid number of threads.")
        sys.exit(1)

    # Get paths and instructions from command line arguments
    champ_sim_path = sys.argv[2]
    trace_dir = sys.argv[3]
    config_file = sys.argv[4]
    output_dir = sys.argv[5]

    warmup_instructions = int(sys.argv[6]) if len(sys.argv) > 6 \
        and is_number(sys.argv[6]) else None
    simulation_instructions = int(sys.argv[7]) if len(sys.argv) > 7 \
        and is_number(sys.argv[7]) else None

    # Define the list of trace URLs to download
    trace_urls = [
        #"https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/400.perlbench-41B.champsimtrace.xz"
        #"https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/400.perlbench-50B.champsimtrace.xz"
    ]

    exec_all_policies(trace_dir, output_dir, champ_sim_path, config_file, 
                      trace_urls, warmup_instructions, simulation_instructions, 
                      threads)

if __name__ == "__main__":
    main()