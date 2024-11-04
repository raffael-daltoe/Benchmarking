import os
import json
import requests
import subprocess
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import sys

class ChampSimRunner:
    def __init__(self, champ_sim_path, trace_dir, config_file, output_dir, policies, threads, warmup_instructions=None, simulation_instructions=None):
        self.champ_sim_path = champ_sim_path
        self.trace_dir = trace_dir
        self.config_file = config_file
        self.output_dir = output_dir
        self.policies = policies
        self.threads = threads
        self.warmup_instructions = warmup_instructions
        self.simulation_instructions = simulation_instructions
        self.S1_replacement = threading.Semaphore(1)
        self.modified_config = None  # Holds the updated configuration parameters

    def download_traces(self, trace_urls):
        if not os.path.exists(self.trace_dir):
            os.makedirs(self.trace_dir)

        for file_url in trace_urls:
            file_name = file_url.split('/')[-1]
            file_path = os.path.join(self.trace_dir, file_name)

            if os.path.exists(file_path):
                print(f"File {file_name} already downloaded.")
            else:
                print(f"Downloading {file_name} ...")
                with requests.get(file_url, stream=True) as r:
                    r.raise_for_status()
                    with open(file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                print(f"Downloaded {file_name}.")

    def modify_replacement_policy(self, policy):
        self.S1_replacement.acquire()
        with open(self.config_file, 'r') as file:
            config = json.load(file)
        config['LLC']['replacement'] = policy

        self.modified_config = config  # Save the updated configuration in the class

    def write_file(self, file_path):
        if self.modified_config:
            with open(file_path, 'w') as file:
                json.dump(self.modified_config, file, indent=4)

            # Copy the configuration file to the ChampSim path and prepare for compilation
            subprocess.run(['cp', '-r', file_path, self.champ_sim_path])
            subprocess.run(["./config.sh", "champsim_config.json"], cwd=self.champ_sim_path)
            subprocess.run(["make", f"-j{self.threads}"], cwd=self.champ_sim_path, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        else:
            print("No configuration changes to write.")

    def exec_single_trace(self, trace_file, trace_path, policy):
        trace_name = os.path.splitext(trace_file)[0]
        output_file = os.path.join(self.output_dir, f"{trace_name}_{policy}_output.txt")
        command = [os.path.join(self.champ_sim_path, "bin/champsim")]

        if self.warmup_instructions:
            command.extend(["--warmup-instructions", str(self.warmup_instructions)])
        if self.simulation_instructions:
            command.extend(["--simulation-instructions", str(self.simulation_instructions)])
        command.append(trace_path)

        print(f"Executing ChampSim for {trace_file} with policy {policy}...")
        with open(output_file, 'w') as outfile:
            self.S1_replacement.release()
            subprocess.run(command, stdout=outfile, stderr=outfile)
        print(f"Output for {trace_file} with policy {policy} stored in {output_file}")

    def prepare_execution(self, executor, policy):
        for trace_file in os.listdir(self.trace_dir):
            if trace_file.endswith('.champsimtrace') or trace_file.endswith('.xz'):
                trace_path = os.path.join(self.trace_dir, trace_file)
                executor.submit(self.exec_single_trace, trace_file, trace_path, policy)

    def execute_all_policies(self, trace_urls):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.download_traces(trace_urls)

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for policy in self.policies:
                self.modify_replacement_policy(policy)
                self.write_file(self.config_file)
                self.prepare_execution(executor, policy)


def main():
    if len(sys.argv) < 6:
        print("Usage: python3 script.py <number_of_threads> <champsim_path> <trace_dir> <config_file> <output_dir> <warmup_instructions> <simulation_instructions>")
        sys.exit(1)

    try:
        threads = int(sys.argv[1])
        if threads < 1:
            raise ValueError
    except ValueError:
        print("Please provide a valid number of threads.")
        sys.exit(1)

    champ_sim_path = sys.argv[2]
    trace_dir = sys.argv[3]
    config_file = sys.argv[4]
    output_dir = sys.argv[5]

    warmup_instructions = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6].isdigit() else None
    simulation_instructions = int(sys.argv[7]) if len(sys.argv) > 7 and sys.argv[7].isdigit() else None

    trace_urls = [
        #"https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/400.perlbench-41B.champsimtrace.xz"
        #"https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/400.perlbench-50B.champsimtrace.xz"
    ]

    policies = ["lru", "drrip", "ship", "srrip", "hawkeye"]

    champ_sim_runner = ChampSimRunner(champ_sim_path, trace_dir, config_file, output_dir, policies, threads, warmup_instructions, simulation_instructions)
    champ_sim_runner.execute_all_policies(trace_urls)


if __name__ == "__main__":
    main()
