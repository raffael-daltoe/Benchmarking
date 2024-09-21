import os
import json
import requests
from bs4 import BeautifulSoup
import subprocess

# Directory where traces will be stored
trace_dir = "../tools/ChampSim/ChampSimTraces"
config_file = "../tools/champsim_config.json"
output_dir = "../tools/ChampSim/SimulationOutputs"

# List of specific URLs to download the traces
trace_urls = [
    "https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/400.perlbench-41B.champsimtrace.xz",
    "https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/400.perlbench-50B.champsimtrace.xz"
]

# Function to download specific trace files
def download_traces():
    subprocess.run(["mkdir", trace_dir])

    # Ensure the directory exists
    os.makedirs(trace_dir, exist_ok=True)

    # Download the trace files specified in the list
    for file_url in trace_urls:
        file_name = file_url.split('/')[-1]
        file_path = os.path.join(trace_dir, file_name)

        # Download each trace file
        print(f"Downloading {file_name} ...")
        with requests.get(file_url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Downloaded {file_name}.")

# Function to modify the replacement policy in the configuration
def modify_replacement_policy(policy):
    with open(config_file, 'r') as file:
        config = json.load(file)

    config['LLC']['replacement'] = policy

    with open(config_file, 'w') as file:
        json.dump(config, file, indent=4)

    print(f"Changed replacement policy to {policy}.")

# Function to execute ChampSim for all traces with a specific replacement policy
def exec_traces_with_policy(policy):
    # Create directory for simulation outputs
    os.makedirs(output_dir, exist_ok=True)

    modify_replacement_policy(policy)
    for trace_file in os.listdir(trace_dir):
        if trace_file.endswith('.champsimtrace.xz'):
            trace_name = os.path.splitext(trace_file)[0]  # Get the trace name without the extension
            trace_path = os.path.join(trace_dir, trace_file)
            output_file = os.path.join(output_dir, f"{trace_name}_{policy}_output.txt")
            
            # Command to execute ChampSim
            command = [
                "./bin/champsim", 
                "--warmup_instructions", "200000000",
                "--simulation_instructions", "500000000",
                trace_path
            ]
            
            # Execute ChampSim and capture output in a specific file for each trace
            print(f"Executing ChampSim for {trace_file} with policy {policy}...")
            with open(output_file, 'w') as outfile:
                subprocess.run(command, stdout=outfile, stderr=outfile)
            
            print(f"Output for {trace_file} with policy {policy} stored in {output_file}")

# Function to execute all policies (drrip, ship, srrip) for all traces
def exec_all_policies():
    policies = ["lru", "drrip", "ship", "srrip"]
    for policy in policies:
        exec_traces_with_policy(policy)

# Main function to execute all steps
def main():
    download_traces()
    exec_all_policies()

if __name__ == "__main__":
    main()
