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

@dataclass
class CacheConfig:
    sets: int
    ways: int
    latency: int

class ChampSimRunner:
    def __init__(self, champ_sim_path, trace_dir, config_file, output_dir, 
                 policies, prefetchs, branchs, threads, 
                 warmup_instructions=None, simulation_instructions=None,
                 L1I_Config=None, L1D_Config=None, L2_Config=None,
                 LLC_Config=None):
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
        self.SGlobal        = threading.Semaphore(threads)
        self.modified_config = None  # Holds the updated configuration parameter
        self.json_config_name = None
        self.json_directory = 'json_files/'
        self.L1I_Config = L1I_Config 
        self.L1D_Config = L1D_Config
        self.L2_Config = L2_Config
        self.LLC_Config = LLC_Config
        self.Samples = list(zip(L1I_Config, L1D_Config, L2_Config, LLC_Config))

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
        time.sleep(0.2)
        self.S1_replacement.acquire()
        self.modified_config['LLC']['replacement'] = policy

    def modify_prefetcher(self,prefetch):
        time.sleep(0.3)
        self.S2_replacement.acquire()
        self.modified_config['LLC']['prefetcher'] = prefetch
        
    def modify_branch(self,branch):
        time.sleep(0.35)
        self.S3_replacement.acquire()
        self.modified_config['ooo_cpu'][0]['branch_predictor'] = branch
    
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

    def exec_single_trace(self, trace_file, trace_path, policy, branch, prefetch):
        trace_name = os.path.splitext(trace_file)[0]
        temp_output_file = os.path.join(self.output_dir, 
            f"{trace_name}_pol:{policy}_bra:{branch}_pre:{prefetch}_output.txt")
        final_output_file = os.path.join(self.output_dir, 
            f"{trace_name}_pol:{policy}_bra:{branch}_pre:{prefetch}_output_DONE.txt")

        bin = 'bin/' + self.config_bin_name

        command = [os.path.join(self.champ_sim_path, bin)]

        if self.warmup_instructions:
            command.extend(["--warmup-instructions", str(self.warmup_instructions)])
        if self.simulation_instructions:
            command.extend(["--simulation-instructions", str(self.simulation_instructions)])
        command.append(trace_path)

        print(f"Executing ChampSim for {trace_file} with policy {policy} "
            f"branch {branch} and prefetch {prefetch}...")
        self.S1_replacement.release()
        self.S2_replacement.release()
        self.S3_replacement.release()

        try:
            with open(temp_output_file, 'w') as outfile:
                subprocess.run(command, stdout=outfile, stderr=outfile, check=True)
            # Rename the output file to include '_DONE' after successful execution
            os.rename(temp_output_file, final_output_file)
            print(f"Output for {trace_file} with policy {policy} "
                f"branch {branch} and prefetch {prefetch} "
                f"stored in {final_output_file}")
            print("1Realeasing Sglobal!")
            self.SGlobal.release()
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while executing ChampSim for {trace_file}: {e}")
            print("2Realeasing Sglobal!")
            self.SGlobal.release()
        


    def prepare_execution(self, executor, policy, branch, prefetch):
        for trace_file in os.listdir(self.trace_dir):
            if trace_file.endswith('.champsimtrace') or trace_file.endswith('.xz'):
                # Remove the extensions .xz or .champsimtrace
                if trace_file.endswith('.xz'):
                    clean_trace_file = trace_file[:-3]
                    clean_trace_file = os.path.splitext(clean_trace_file)[0]
                elif trace_file.endswith('.champsimtrace'):
                    clean_trace_file = trace_file[:-13]
                    clean_trace_file = os.path.splitext(clean_trace_file)[0]
                
                #print(f"1)S1:{self.S1_replacement._value} S2:{self.S2_replacement._value} S3:{self.S3_replacement._value}")
                    
                   # trace_name = os.path.splitext(trace_file)[0]
                if self.verify_already_executed(policy, prefetch, branch, clean_trace_file):
                    self.S2_replacement.release()
                    self.S1_replacement.release()
                    self.S3_replacement.release()
                    #print(f"2)S1:{self.S1_replacement._value} S2:{self.S2_replacement._value} S3:{self.S3_replacement._value}")
                    
                    return
                    #continue
                else:
                    #print(f"3)SG: {self.SGlobal._value} S1:{self.S1_replacement._value} S2:{self.S2_replacement._value} S3:{self.S3_replacement._value}")
               
                    trace_path = os.path.join(self.trace_dir, trace_file)
                    self.SGlobal.acquire()
                    # Pass the cleaned trace file without extensions
                    executor.submit(self.exec_single_trace, clean_trace_file, trace_path, 
                                    policy, branch, prefetch)
                    #print(f"4)SG: {self.SGlobal._value} S1:{self.S1_replacement._value} S2:{self.S2_replacement._value} S3:{self.S3_replacement._value}")
               
                                                            
    def modify_size_cache(self, L1I, L1D, L2, LLC):
        with open(self.config_file, 'r') as file:
            config = json.load(file)

        config['L1I']['sets'] = L1I.sets
        config['L1I']['ways'] = L1I.ways
        config['L1I']['latency'] = L1I.latency

        config['L1D']['sets'] = L1D.sets
        config['L1D']['ways'] = L1D.ways
        config['L1D']['latency'] = L1D.latency

        config['L2C']['sets'] = L2.sets
        config['L2C']['ways'] = L2.ways
        config['L2C']['latency'] = L2.latency

        config['LLC']['sets'] = LLC.sets
        config['LLC']['ways'] = LLC.ways
        config['LLC']['latency'] = LLC.latency

        self.modified_config = config  
        
    def modify_hawkeye_algorithm(self, LLC):
            # Construct the file path
        file_path = os.path.join(self.champ_sim_path, 'replacement', 'hawkeye', 'hawkeye_algorithm.cc')

        # Check if file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read the file content
        with open(file_path, 'r') as file:
            content = file.read()

        # Replace the value for LLC_SETS (2048)
        sets_pattern = r"#define\s+LLC_SETS\s+NUM_CORE\*2048"
        sets_replacement = f"#define LLC_SETS NUM_CORE*{LLC.sets}"
        content = re.sub(sets_pattern, sets_replacement, content)

        # Replace the value for LLC_WAYS (16)
        ways_pattern = r"#define\s+LLC_WAYS\s+16"
        ways_replacement = f"#define LLC_WAYS {LLC.ways}"
        content = re.sub(ways_pattern, ways_replacement, content)

        # Write the updated content back to the file
        with open(file_path, 'w') as file:
            file.write(content)
            
    def modify_mockingjay(self, LLC):
            # Construct the file path
        file_path = os.path.join(self.champ_sim_path, 'replacement', 'mockingjay', 'mockingjay.cc')

        # Check if file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read the file content
        with open(file_path, 'r') as file:
            content = file.read()

        # Replace the value for LLC_SET
        set_pattern = r"#define\s+LLC_SET\s+\d+"
        set_replacement = f"#define LLC_SET {LLC.sets}"
        content = re.sub(set_pattern, set_replacement, content)

        # Replace the value for LLC_WAY
        way_pattern = r"#define\s+LLC_WAY\s+\d+"
        way_replacement = f"#define LLC_WAY {LLC.ways}"
        content = re.sub(way_pattern, way_replacement, content)

        # Write the updated content back to the file
        with open(file_path, 'w') as file:
            file.write(content)

    def verify_already_executed(self,policy, prefetch, branch,trace_name):
        try:
            if not os.path.exists(self.output_dir):
                raise UnboundLocalError
            file_name = f"{trace_name}_pol:{policy}_bra:{branch}_pre:{prefetch}_output_DONE.txt"
            for name in os.listdir(self.output_dir):
                #print(f"file_name = {file_name} and name = {name}")
                if name == file_name:
                    print(f"File {file_name} already executed")
                    return True
            return False
        except UnboundLocalError:
            print(f"Directory not found: {self.output_dir}")
            sys.exit(1)
    
    def execute_all_policies(self, trace_urls):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.download_traces(trace_urls)
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for index, sample in enumerate(self.Samples, start=1):
                L1I, L1D, L2, LLC = sample
                
                sample_folder = os.path.join(self.output_dir, f"Sample{index}")
                self.output_dir = str(sample_folder)
                if not os.path.exists(sample_folder):
                    os.makedirs(sample_folder)
                
                self.modify_size_cache(L1I, L1D, L2, LLC)
                self.modify_hawkeye_algorithm(LLC)  
                self.modify_mockingjay(LLC)
                
                if len(self.policies) != 0:
                    for policy in self.policies:
                        if len(self.prefetchs) != 0:
                            for prefetch in self.prefetchs:
                                if len(self.branchs) != 0:
                                    for branch in self.branchs:
                                        self.modify_replacement_policy(policy)
                                        self.modify_prefetcher(prefetch)
                                        self.modify_branch(branch)
                                        self.modify_name_file(policy, prefetch, 
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
        #"https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/401.bzip2-226B.champsimtrace.xz",
        #"https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/401.bzip2-277B.champsimtrace.xz",
        #"https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/401.bzip2-7B.champsimtrace.xz",
        "https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/400.perlbench-50B.champsimtrace.xz",
        "https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/403.gcc-16B.champsimtrace.xz",
        #"https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/401.bzip2-38B.champsimtrace.xz"
    ]
    
    policies = ["bip","hawkeye","fifo","emissary","pcn","rlr","drrip","lru",
                                              "ship","srrip","mockingjay","lfu"]
    
    prefetchs = ["va_ampm_lite","spp_dev","next_line","ip_stride","no"]

    branchs = ["bimodal", "gshare", "hashed_perceptron", "perceptron","tage"]
    
    L1I_config = [  CacheConfig(64,8,4),
                    #CacheConfig(64,8,4),
                    #CacheConfig(64,8,4),
                    #CacheConfig(64,8,4),
                    #CacheConfig(64,8,4),
                 ]
    
    L1D_config = [  CacheConfig(64,8,4),
                    #CacheConfig(64,12,5),
                    #CacheConfig(64,8,4),
                    #CacheConfig(64,8,4),
                    #CacheConfig(64,12,4),
                 ]
    
    L2_config = [   CacheConfig(512,8,8),
                    #CacheConfig(820,8,8),
                    #CacheConfig(512,8,8),
                    #CacheConfig(512,8,8),
                    #CacheConfig(1024,8,15),
                 ]
    
    LLC_Config = [  CacheConfig(2048,16,20),
                    #CacheConfig(2048,16,22),
                    #CacheConfig(4096,16,21),
                    #CacheConfig(8192,16,22),
                    #CacheConfig(2048,16,45),
                 ]
    

    
    
    champ_sim_runner = ChampSimRunner(champ_sim_path, trace_dir, config_file, 
                                      output_dir, policies, prefetchs, branchs,
                                      threads, warmup_instructions, 
                                      simulation_instructions, L1I_config, 
                                      L1D_config, L2_config, LLC_Config)
    
    champ_sim_runner.execute_all_policies(trace_urls)


if __name__ == "__main__":
    main()
