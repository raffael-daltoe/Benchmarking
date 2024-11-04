import os
import re
import matplotlib.pyplot as plt
import numpy as np

# Base directory where all trace directories are located
base_dir = '../simulations/'

# Algorithms to search for within each trace directory
algorithms = ['FCFS', 'FRFCFS', 'FRFCFS_Cap', 'FRFCFS_PriorHit']

# Output files to look for within each algorithm directory
output_files = [
    'bp.stat.0.out', 'fetch.stat.0.out', 'power.stat.0.out', 'core.stat.0.out', 
    'inst.stat.0.out','memory.stat.0.out', 'pref.stat.0.out','stream.stat.0.out'
]

# Metrics to collect from each file
metrics_to_collect = ['IPC','RET_BLOCKED_L1_ACCESS','RET_BLOCKED_L1_MISS']

# Dictionary to store metrics data organized by trace, algorithm, and metric
trace_metrics = {}

# Function to extract general metrics from file content
def extract_metrics(file_content):
    metrics = {}
    for metric in metrics_to_collect:
        match = re.search(rf'{metric}:?\s*([\d.]+)', file_content)
        if match:
            metrics[metric] = float(match.group(1))
    return metrics

# Traverse through each trace directory and extract metrics for each algorithm
for trace_dir in os.listdir(base_dir):
    trace_path = os.path.join(base_dir, trace_dir)
    
    # Ensure that we're looking at a directory
    if not os.path.isdir(trace_path):
        continue
    
    # Initialize dictionary for each trace
    trace_metrics[trace_dir] = {}
    
    # Traverse each algorithm directory within the trace directory
    for algo in algorithms:
        algo_path = os.path.join(trace_path, algo)
        
        # Ensure that we're looking at a directory
        if not os.path.isdir(algo_path):
            continue
        
        # Initialize dictionary for each algorithm within the trace
        trace_metrics[trace_dir][algo] = {}
        
        # Process each output file within the algorithm directory
        for output_file in output_files:
            file_path = os.path.join(algo_path, output_file)
            
            # Ensure the file exists before reading
            if os.path.isfile(file_path):
                with open(file_path, 'r') as file:
                    file_content = file.read()
                    trace_metrics[trace_dir][algo].update(extract_metrics(file_content))

# Simplify trace names for display
trace_names = [trace.split('.')[1] for trace in trace_metrics.keys()]  # Extract the core part of each trace name
x = np.arange(len(trace_names))  # Position of each trace group
bar_width = 0.1  # Width of each bar within a group

# Plot each metric as a grouped bar chart for each algorithm
for metric in metrics_to_collect:
    plt.figure(figsize=(12, 8))
    
    # Plot bars for each algorithm
    for i, algo in enumerate(algorithms):
        y = [trace_metrics[trace][algo].get(metric, 0) for trace in trace_metrics.keys()]
        plt.bar(x + i * bar_width, y, width=bar_width, label=algo)
        
        # Annotate each bar with its value
        for j, val in enumerate(y):
            annotation_color = 'black'
            font_weight = 'normal'
            font_size = 8

            # Highlight the best IPC in red with bold font
            if metric == 'IPC':
                max_algo = max(trace_metrics[list(trace_metrics.keys())[j]], key=lambda algo: trace_metrics[list(trace_metrics.keys())[j]][algo].get(metric, 0))
                if algo == max_algo:
                    annotation_color = 'red'
                    font_weight = 'bold'
                    font_size = 12

            plt.text(x[j] + i * bar_width, val + 0.005 * max(y), f'{val:.2f}', 
                     ha='center', fontsize=font_size, color=annotation_color, fontweight=font_weight)

    # Set labels, title, and limits
    plt.xticks(x + bar_width * (len(algorithms) - 1) / 2, trace_names, rotation=45, fontsize=14)
    plt.ylim(0, max([max([trace_metrics[trace][algo].get(metric, 0) for algo in algorithms]) for trace in trace_metrics.keys()]) * 1.1)
    plt.xlabel('Traces', fontsize=16)
    plt.ylabel(metric, fontsize=16)
    plt.title(f'{metric} Comparison Across Traces and Cache Algorithms', fontsize=18)
    plt.legend(title='Cache Algorithms', fontsize=12)
    plt.tight_layout()
    plt.show()
