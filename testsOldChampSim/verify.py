import os

output_dir = "sim_outputs"

def verify_files(policies, prefetchs, branchs, sizes):
    list_not_simulated = []
    
    for i in range(1, 5):
        # Construct the directory path
        dir_path = os.path.join(output_dir, f"Sample{i}")
        
        # If the directory doesn't exist, you can decide to skip or log it
        if not os.path.isdir(dir_path):
            print(f"Warning: Directory {dir_path} does not exist.")
            continue
        
        for size in sizes:
            for policy in policies:
                for branch in branchs:
                    for prefetch in prefetchs:
                        # Build the expected filename
                        filename = f"400.perlbench-{size}_pol:{policy}_bra:{branch}_pre:{prefetch}_output_DONE.txt"
                        
                        # Check if that file actually exists
                        full_path = os.path.join(dir_path, filename)
                        if not os.path.isfile(full_path):
                            # Keep track of which file is missing
                            list_not_simulated.append(full_path)
    
    return list_not_simulated

def main():
    policies  = ["bip", "hawkeye", "fifo", "emissary", "pcn", "rlr", "drrip", "lru", "ship", "mockingjay"]
    prefetchs = ["next_line", "ip_stride", "no"]
    branchs   = ["bimodal", "gshare", "tage"]
    sizes     = ["41B", "50B"]  # we include both sizes

    missing_files = verify_files(policies, prefetchs, branchs, sizes)
    
    if missing_files:
        print("Elements not simulated (missing files):")
        for mf in missing_files:
            print(mf)
    else:
        print("All files for all combinations are present!")

if __name__ == "__main__":
    main()
