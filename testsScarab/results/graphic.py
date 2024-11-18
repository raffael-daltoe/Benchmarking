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
metrics_to_collect = ['IPC', 'L1_HIT_ALL', 'L1_MISS_ALL',
                      'POWER_ICACHE_ACCESS'
                      ]

# Dictionary to store metrics data organized by trace, algorithm, and metric
trace_metrics = {}

# Function to extract general and hit/miss metrics from file content
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
bar_width = 0.18  # Width of each bar within a group

# Plot each metric as a grouped bar chart for each algorithm
for metric in metrics_to_collect:
    plt.figure(figsize=(12, 8))
    
    use_log_scale = metric in ['L1_HIT_ALL', 'L1_MISS_ALL']

    # Use a logarithmic scale for specified metrics
    if use_log_scale:
        plt.yscale('log')

    if metric == 'L1_HIT_ALL':
        total_hit_scale = 5
        position_legend = "upper left"
    elif metric == 'L1_MISS_ALL':
        total_hit_scale = 3
        position_legend = "upper left"
    else:
        total_hit_scale = 1.3
        position_legend = "upper left"

    # Calculate max and min values to set y-axis limits
    all_values = [trace_metrics[trace][algo].get(metric, 0) for trace in trace_metrics for algo in algorithms]
    y_min,x_min = min(all_values) * 0.95, max(all_values) * total_hit_scale

    # Plot bars for each algorithm
    for i, algo in enumerate(algorithms):
        y = [trace_metrics[trace][algo].get(metric, 0) for trace in trace_metrics.keys()]
        plt.bar(x + i * bar_width, y, width=bar_width, label=algo)
        
        # Annotate each bar with its value
        for j, val in enumerate(y):
            annotation_color = 'black'
            font_weight = 'normal'
            font_size = 16

            # Highlight conditions based on metrics
            if metric == 'IPC':
                # Highlight the best IPC in red with bold font
                max_algo = max(trace_metrics[list(trace_metrics.keys())[j]], key=lambda algo: trace_metrics[list(trace_metrics.keys())[j]][algo].get(metric, 0))
                if algo == max_algo:
                    annotation_color = 'limegreen'
                    font_weight = 'bold'
                    font_size = 17
            elif metric == 'L1_HIT_ALL':
                # Highlight the algorithm with the maximum hit rate
                max_hit_algo = max(trace_metrics[list(trace_metrics.keys())[j]], key=lambda algo: trace_metrics[list(trace_metrics.keys())[j]][algo].get(metric, 0))
                if algo == max_hit_algo:
                    annotation_color = 'limegreen'
                    font_weight = 'bold'
                    font_size = 17
            elif metric == 'L1_MISS_ALL':
                # Highlight the algorithm with the minimum miss rate
                min_miss_algo = min(trace_metrics[list(trace_metrics.keys())[j]], key=lambda algo: trace_metrics[list(trace_metrics.keys())[j]][algo].get(metric, float('inf')))
                if algo == min_miss_algo:
                    annotation_color = 'red'
                    font_weight = 'bold'
                    font_size = 17
            elif metric == 'POWER_ICACHE_ACCESS':
                min_power_algo = min(trace_metrics[list(trace_metrics.keys())[j]], key=lambda algo: trace_metrics[list(trace_metrics.keys())[j]][algo].get(metric, float('inf')))
                if algo == min_power_algo:
                    annotation_color = 'limegreen'
                    font_weight = 'bold'
                    font_size = 17

            # Format large numbers with 'K', 'M', or 'B' notation for readability
            if val >= 1e9:
                display_val = f'{val/1e9:.2f}B'  # Convert to billions
            elif val >= 1e6:
                display_val = f'{val/1e6:.2f}M'  # Convert to millions
            elif val >= 1e3:
                display_val = f'{val/1e3:.2f}K'  # Convert to thousands
            else:
                display_val = f'{val:.2f}'  # Use regular two-decimal format
            
            # Adjust the text position slightly above each bar's top and shift it to the right
            current_scale = plt.gca().get_yscale()  # Get the current y-axis scale
            offset_y = val * 0.01 if current_scale == 'log' else 0.005 * max(y)  # Dynamically set y offset based on scale
            offset_x = 0.05  # Shift text slightly to the right

            plt.text(x[j] + i * bar_width + offset_x, val + offset_y, display_val, 
                    ha='center', fontsize=font_size, color=annotation_color, fontweight=font_weight, rotation=55)


    # Set labels, title, and limits
    plt.xticks(x + bar_width * (len(algorithms) - 1) / 2, trace_names, rotation=25, fontsize=14)
    plt.ylim(y_min, x_min)
    plt.xlim(-0.15, len(trace_names) - 0.3)
    plt.xlabel('Traces', fontsize=16)
    plt.ylabel(metric, fontsize=16)
    plt.title(f'{metric} Comparison Across Traces and Main Memory Algorithms', fontsize=18)
    plt.legend(
        title='Main Memory Algorithms',
        fontsize=20,           # Increase the font size of legend text
        title_fontsize=22,      # Increase the font size of the legend title
        borderpad=0.5,          # Increase padding inside the legend box
        labelspacing=0.5,       # Increase the spacing between entries
        handletextpad=0.5,      # Increase space between marker and text
        loc=position_legend,       # Adjust location if needed
    )
    plt.tight_layout()
    plt.show()
