import os
import re
import matplotlib.pyplot as plt
import numpy as np

# Define paths, algorithms, and metrics
output_dir = '../sim_outputs/'
algorithms = ['drrip', 'hawkeye', 'lru', 'ship', 'srrip']
metrics_to_collect = ['CPU 0 cumulative IPC', 'Branch Prediction Accuracy', 'MPKI']

# List of metric prefixes with ACCESS, HIT, and MISS patterns
access_hit_miss_metrics = ['cpu0_L1D TOTAL']  # You can add more prefixes here as needed

# Function to extract ACCESS, HIT, MISS metrics based on the prefixes list
def extract_access_hit_miss_metrics(file_content):
    metrics = {}
    for metric_prefix in access_hit_miss_metrics:
        # Use regex to match ACCESS, HIT, MISS values for each metric prefix
        match = re.search(rf'{re.escape(metric_prefix)}\s+ACCESS:\s+(\d+)\s+HIT:\s+(\d+)\s+MISS:\s+(\d+)', file_content)
        if match:
            metrics[f'{metric_prefix} ACCESS'] = int(match.group(1))
            metrics[f'{metric_prefix} HIT'] = int(match.group(2))
            metrics[f'{metric_prefix} MISS'] = int(match.group(3))
    return metrics

# Function to extract general metrics from file content
def extract_metrics(file_content):
    # Start with ACCESS, HIT, MISS metrics
    metrics = extract_access_hit_miss_metrics(file_content)
    # Add other general metrics
    for metric in metrics_to_collect:
        match = re.search(rf'{metric}:?\s*([\d.]+)', file_content)
        if match:
            metrics[metric] = float(match.group(1))
    return metrics

# Collect metrics for each trace and algorithm
trace_metrics = {}
for trace_file in os.listdir(output_dir):
    # Check if the file corresponds to a known trace and algorithm
    for algo in algorithms:
        if trace_file.endswith(f'_{algo}_output.txt'):
            trace_name = trace_file.split('_')[0]
            if trace_name not in trace_metrics:
                trace_metrics[trace_name] = {}
            
            # Read the file and extract metrics
            with open(os.path.join(output_dir, trace_file), 'r') as f:
                file_content = f.read()
                trace_metrics[trace_name][algo] = extract_metrics(file_content)

# Prepare data for a grouped bar plot
all_metrics = metrics_to_collect + [f'{prefix} {suffix}' for prefix in access_hit_miss_metrics for suffix in ['ACCESS', 'HIT', 'MISS']]

for metric in all_metrics:
    plt.figure(figsize=(12, 8))
    trace_names = list(trace_metrics.keys())
    x = np.arange(len(trace_names))  # Position of each trace group
    bar_width = 0.15  # Width of each bar within a group
    
    # Calculate max and min values to set y-axis limits
    all_values = [trace_metrics[trace][algo].get(metric, 0) for trace in trace_metrics for algo in algorithms]
    y_min, y_max = min(all_values) * 0.95, max(all_values) * 1.05  # Add some padding
    
    # Plot bars for each algorithm
    for i, algo in enumerate(algorithms):
        y = [trace_metrics[trace][algo].get(metric, 0) for trace in trace_names]
        plt.bar(x + i * bar_width, y, width=bar_width, label=algo)
        
        # Annotate each bar with its value
        for j, val in enumerate(y):
            # Default annotation color and style for non-best IPC
            annotation_color = 'black'
            font_weight = 'normal'
            font_size = 8

            # Highlight the best IPC in red with bold font
            if metric == 'CPU 0 cumulative IPC':
                max_algo = max(trace_metrics[trace_names[j]], key=lambda algo: trace_metrics[trace_names[j]][algo].get(metric, 0))
                if algo == max_algo:
                    annotation_color = 'red'
                    font_weight = 'bold'
                    font_size = 12

            plt.text(x[j] + i * bar_width, val + 0.005 * y_max, f'{val:.2f}', 
                     ha='center', fontsize=font_size, color=annotation_color, fontweight=font_weight)

    # Set labels, title, and limits
    plt.xticks(x + bar_width * (len(algorithms) - 1) / 2, trace_names, rotation=45, fontsize=14)
    plt.ylim(y_min, y_max)
    plt.xlabel('Traces', fontsize=16)
    plt.ylabel(metric, fontsize=16)
    plt.title(f'{metric} Comparison Across Traces for Each Algorithm', fontsize=18)
    plt.legend(title='Cache Algorithms', fontsize=12)
    plt.tight_layout()
    plt.show()
