import os
import json
import requests
from bs4 import BeautifulSoup
import subprocess
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import sys

# Directory where traces will be stored
PATH_ChampSim = "../tools/ChampSim/"
trace_dir = PATH_ChampSim + "ChampSimTraces/"
config_file = PATH_ChampSim + "champsim_config.json"
output_dir = PATH_ChampSim + "SimulationOutputs"

# List of specific URLs to download the traces
trace_urls = [
    "https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/400.perlbench-41B.champsimtrace.xz"
]

# List of policies allowed in ChampSim
policies = ["lru", "drrip", "ship", "srrip"]

S1_replacement = threading.Semaphore(1)

# Function to download specific trace files
def download_traces():
    # Command to create the folder
    if not (os.path.exists(trace_dir)):
        subprocess.run(["mkdir", trace_dir])

    # Download the trace files specified in the list
    for file_url in trace_urls:
        file_name = file_url.split('/')[-1]
        file_path = os.path.join(trace_dir, file_name)

        if os.path.exists(trace_dir + file_name):
            print("File already downloaded")
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
def modify_replacement_policy(policy,threads):
    
    S1_replacement.acquire()
    
    with open(config_file, 'r') as file:
        config = json.load(file)

    config['LLC']['replacement'] = policy

    with open(config_file, 'w') as file:
        json.dump(config, file, indent=4)

    subprocess.run(["./config.sh", "champsim_config.json"], cwd=PATH_ChampSim)

    subprocess.run(["make", f"-j{threads}"], cwd=PATH_ChampSim, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    S1_replacement.release()

    print(f"Changed replacement policy to {policy}.")

# Function to execute a single trace with a specific replacement policy
def exec_single_trace_with_policy(trace_file, policy):
    trace_name = os.path.splitext(trace_file)[0]  
    trace_path = os.path.join(trace_dir, trace_file)
    output_file = os.path.join(output_dir, f"{trace_name}_{policy}_output.txt")

    # Command to execute ChampSim
    command = [
        "./" + PATH_ChampSim + "bin/champsim", 
        "--warmup_instructions", "200000000",
        "--simulation_instructions", "500000000",
        trace_path
    ]

    # Execute ChampSim and capture output in a specific file for each trace
    print(f"Executing ChampSim for {trace_file} with policy {policy}...")
    with open(output_file, 'w') as outfile:
        subprocess.run(command, stdout=outfile, stderr=outfile)
    
    print(f"Output: {trace_file} with policy {policy} stored in {output_file}")

# Function to execute all policies (drrip, ship, srrip) for all traces
def exec_all_policies(threads):
    # Create a thread pool and submit tasks
    with ThreadPoolExecutor(max_workers=threads) as executor:
        for policy in policies:
            modify_replacement_policy(policy,threads)  # Modify config for each policy
            for trace_file in os.listdir(trace_dir):
                if trace_file.endswith('.champsimtrace.xz'):
                    executor.submit(exec_single_trace_with_policy, 
                                    trace_file, policy)

# Main function to execute all steps
def main(threads):
    download_traces()
    exec_all_policies(threads)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 script.py <number_of_threads>")
        sys.exit(1)
    try:
        threads = int(sys.argv[1])
        if threads < 1:
            raise ValueError
    except ValueError:
        print("Please provide a valid number of threads.")
        sys.exit(1)
main(threads)