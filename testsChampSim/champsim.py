import os
import json
import requests
import subprocess
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import sys

class ChampSimRunner:
    def __init__(self, champ_sim_path, trace_dir, config_file, output_dir, 
                 policies, prefetchs, branchs, threads, 
                 warmup_instructions=None, simulation_instructions=None):
        self.champ_sim_path = champ_sim_path
        self.trace_dir = trace_dir
        self.config_file = config_file
        self.config_bin_name = 'champsim'
        self.output_dir = output_dir
        self.policies = policies
        self.prefetchs = prefetchs
        self.branchs = branchs
        self.threads = threads
        self.warmup_instructions = warmup_instructions
        self.simulation_instructions = simulation_instructions
        self.S1_replacement = threading.Semaphore(1)
        self.S2_replacement = threading.Semaphore(1)
        self.S3_replacement = threading.Semaphore(1)
        self.SGlobal        = threading.Semaphore(32)
        self.modified_config = None  # Holds the updated configuration parameter
        self.json_config_name = None
        self.json_directory = 'json_files/'

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
        time.sleep(0.5)
        self.S1_replacement.acquire()
        with open(self.config_file, 'r') as file:
            config = json.load(file)
        config['LLC']['replacement'] = policy

        self.modified_config = config  
        
    def modify_prefetcher(self,prefetch):
        time.sleep(0.5)
        self.S2_replacement.acquire()

        self.modified_config['L1I']['prefetcher'] = prefetch
        self.modified_config['L1D']['prefetcher'] = prefetch
        self.modified_config['L2C']['prefetcher'] = prefetch
        self.modified_config['LLC']['prefetcher'] = prefetch
        

       # self.modified_config = config  
        
    def modify_branch(self,branch):
        time.sleep(0.5)
        self.S3_replacement.acquire()
        self.modified_config['ooo_cpu'][0]['branch_predictor'] = branch

       # self.modified_config = config  
    
    def modify_name_file(self,policy,prefetch,branch):
        updated_config = self.modified_config.copy()
        updated_config['executable_name'] = f'champsim_{policy}_{prefetch}_{branch}'
        self.config_bin_name = f'champsim_{policy}_{prefetch}_{branch}'
        self.modified_config = updated_config
        

    def write_file(self, file_path):
        if self.modified_config:
            with open(file_path, 'w') as file:
                json.dump(self.modified_config, file, indent=4)

            subprocess.run(['mkdir', '-p', f"{self.json_directory}"], 
                                                        cwd=self.champ_sim_path)

            self.json_name_file = (self.champ_sim_path + '/' +                
                                   self.json_directory + 
                                   self.config_bin_name + '.json'
                                   )
                            
            json_to_config = (self.json_directory + 
                              self.config_bin_name + 
                              '.json' )

            # Copy the configuration file to the ChampSim path
            subprocess.run(['cp', '-r', file_path, self.json_name_file])
            subprocess.run(["./config.sh", json_to_config], 
                                                        cwd=self.champ_sim_path)
            subprocess.run(["make", f"-j{self.threads}"], 
                            cwd=self.champ_sim_path, stdout=subprocess.DEVNULL, 
                                                       stderr=subprocess.STDOUT)
        else:
            print("No configuration changes to write.")

    def exec_single_trace(self, trace_file, trace_path, policy, branch,
                                                                      prefetch):
        trace_name = os.path.splitext(trace_file)[0]
        output_file = os.path.join(self.output_dir, 
                        f"{trace_name}_pol:{policy}_bra:{branch}_pre:{prefetch}_output.txt")

        bin = 'bin/' + self.config_bin_name

        command = [os.path.join(self.champ_sim_path, bin)]

        if self.warmup_instructions:
            command.extend(["--warmup-instructions", 
                                                 str(self.warmup_instructions)])
        if self.simulation_instructions:
            command.extend(["--simulation-instructions", 
                                             str(self.simulation_instructions)])
        command.append(trace_path)

        with open(output_file, 'w') as outfile:
            print(f"Executing ChampSim for {trace_file} with policy {policy}, \
              branch {branch} and prefetch {prefetch}...")
            #print(f"executing : {command}")
            self.S1_replacement.release()
            self.S2_replacement.release()
            self.S3_replacement.release()
            subprocess.run(command, stdout=outfile, stderr=outfile)
        print(f"Output for {trace_file} with policy {policy} \
                branch {branch} and prefetch {prefetch} \
                                                       stored in {output_file}")
        self.SGlobal.release()

    def prepare_execution(self, executor, policy, branch, prefetch):
        for trace_file in os.listdir(self.trace_dir):
            if (trace_file.endswith('.champsimtrace') or 
                                                    trace_file.endswith('.xz')):
                
                trace_path = os.path.join(self.trace_dir, trace_file)
                self.SGlobal.acquire()
                executor.submit(self.exec_single_trace, trace_file, trace_path, 
                                                                policy, branch,
                                                                prefetch )

    def execute_all_policies(self, trace_urls):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        #self.download_traces(trace_urls)

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            if len(self.policies) != 0:
                for policy in self.policies:
                    if len(self.prefetchs) != 0:
                        for prefetch in self.prefetchs:
                            if len(self.branchs) != 0:
                                for branch in self.branchs:
                                    self.modify_replacement_policy(policy)
                                    self.modify_prefetcher(prefetch)
                                    self.modify_branch(branch)
                                    self.modify_name_file(policy,prefetch,
                                                                        branch)
                                    self.write_file(self.config_file)
                                    self.prepare_execution(executor, policy,
                                                           branch, prefetch)
            else:
                self.prepare_execution(executor, None)


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

    champ_sim_path = sys.argv[2]
    trace_dir = sys.argv[3]
    config_file = sys.argv[4]
    output_dir = sys.argv[5]

    warmup_instructions = (int(sys.argv[6]) if len(sys.argv) > 6 and 
                                                sys.argv[6].isdigit() else None)
    simulation_instructions = (int(sys.argv[7]) if len(sys.argv) > 7 and 
                                                sys.argv[7].isdigit() else None)

    trace_urls = [
        "https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/400.perlbench-41B.champsimtrace.xz",
        "https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/401.bzip2-226B.champsimtrace.xz",
        "https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/401.bzip2-277B.champsimtrace.xz",
        "https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/401.bzip2-7B.champsimtrace.xz",
        "https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/400.perlbench-50B.champsimtrace.xz",
        "https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/403.gcc-16B.champsimtrace.xz",
        "https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/401.bzip2-38B.champsimtrace.xz"
    ]

    policies = ["hawkeye", "ship" ,"lru", "drrip", "srrip"]
    prefetchs = ["next_line_instr", "no","no_instr", "ip_stride", "next_line", "spp_dev", "va_ampm_lite"]

    branchs = ["bimodal", "gshare" ,"hashed_perceptron", "perceptron"]
    
    champ_sim_runner = ChampSimRunner(champ_sim_path, trace_dir, config_file, 
                                      output_dir, policies, prefetchs, branchs,
                                      threads, warmup_instructions, 
                                      simulation_instructions)
    
    champ_sim_runner.execute_all_policies(trace_urls)


if __name__ == "__main__":
    main()
