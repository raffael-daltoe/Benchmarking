import os
import re
import matplotlib.pyplot as plt
import numpy as np

# Define paths, algorithms, and metrics
output_dir = '../sim_outputs/'
algorithms = set()
metrics_to_collect = ['CPU 0 cumulative IPC']

# List of metric prefixes with ACCESS, HIT, and MISS patterns
access_hit_miss_metrics = ['cpu0_L1D TOTAL']  # You can add more prefixes here as needed

# Function to extract ACCESS, HIT, MISS metrics based on the prefixes list
def extract_access_hit_miss_metrics(file_content):
    metrics = {}
    for metric_prefix in access_hit_miss_metrics:
        # Use regex to match ACCESS, HIT, MISS values for each metric prefix
        match = re.search(rf'{re.escape(metric_prefix)}\s+ACCESS:\s+(\d+)\s+HIT:\s+(\d+)\s+MISS:\s+(\d+)', file_content)
        if match:
            #metrics[f'{metric_prefix} ACCESS'] = int(match.group(1))
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
    algo = trace_file.split('_')[1]
    algorithms.add(algo)

    trace_name = trace_file.split('_')[0]
    parts = trace_name.split('.')
    if len(parts) > 1:
        # If there are at least two parts, join the first two
        trace_name = ".".join(parts[:2])
    else:
        # If there's only one part, use it as-is
        trace_name = parts[0]

    if trace_name not in trace_metrics:
        trace_metrics[trace_name] = {}
            
    # Read the file and extract metrics
    with open(os.path.join(output_dir, trace_file), 'r') as f:
        file_content = f.read()
        trace_metrics[trace_name][algo] = extract_metrics(file_content)

# Prepare data for a grouped bar plot
all_metrics = metrics_to_collect + [f'{prefix} {suffix}' for prefix in access_hit_miss_metrics for suffix in ['HIT', 'MISS']]

for metric in all_metrics:
    plt.figure(figsize=(12, 8))
    trace_names = list(trace_metrics.keys())
    x = np.arange(len(trace_names))  # Position of each trace group
    bar_width = 0.18  # Width of each bar within a group
    
    # Use logarithmic scale if there’s a large range in values
    use_log_scale = metric in ['cpu0_L1D TOTAL MISS', 'cpu0_L1D TOTAL HIT']

    if metric == 'cpu0_L1D TOTAL MISS':
        total_hit_scale = 5
        position_legend = "upper right"
    elif metric == 'cpu0_L1D TOTAL HIT':
        total_hit_scale = 1.5
        position_legend = "upper left"
    else:
        total_hit_scale = 1.1
        position_legend = "upper left"

    # Calculate max and min values to set y-axis limits
    all_values = [trace_metrics[trace][algo].get(metric, 0) for trace in trace_metrics for algo in algorithms]
    y_min,x_min = min(all_values) * 0.95, max(all_values) * total_hit_scale

    
    if use_log_scale:
        plt.yscale('log')

    # Plot bars for each algorithm
    for i, algo in enumerate(algorithms):
        y = [trace_metrics[trace][algo].get(metric, 0) for trace in trace_names]
        plt.bar(x + i * bar_width, y, width=bar_width, label=algo)
        
        # Annotate each bar with its value
        for j, val in enumerate(y):
            # Default annotation color and style for non-best IPC
            annotation_color = 'black'
            font_weight = 'normal'
            font_size = 16

            # Highlight the best IPC in red with bold font
            if metric == 'CPU 0 cumulative IPC':
                max_algo = max(trace_metrics[trace_names[j]], key=lambda algo: trace_metrics[trace_names[j]][algo].get(metric, 0))
                if algo == max_algo:
                    annotation_color = 'limegreen'
                    font_weight = 'bold'
                    font_size = 17
            # Highlight the best values in red for HIT and MISS metrics
            elif metric == 'cpu0_L1D TOTAL HIT':
                max_hit_algo = max(trace_metrics[trace_names[j]], key=lambda algo: trace_metrics[trace_names[j]][algo].get(metric, 0))
                if algo == max_hit_algo:
                    annotation_color = 'limegreen'
                    font_weight = 'bold'
                    font_size = 17
            elif metric == 'cpu0_L1D TOTAL MISS':
                min_miss_algo = min(trace_metrics[trace_names[j]], key=lambda algo: trace_metrics[trace_names[j]][algo].get(metric, float('inf')))
                if algo == min_miss_algo:
                    annotation_color = 'red'
                    font_weight = 'bold'
                    font_size = 17
            
            
            # Format large numbers with 'K' or 'M' notation for readability
            if val >= 1e9:
                display_val = f'{val/1e9:.2f}B'  # Convert to millions
            elif val >= 1e6:
                display_val = f'{val/1e6:.2f}M'  # Convert to thousands
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
    plt.xlim(-0.15, len(trace_names) - 0.13)
    plt.xlabel('Traces', fontsize=16)
    plt.ylabel(metric, fontsize=16)
    plt.title(f'{metric} Comparison Across Traces and Cache Algorithms', fontsize=18)
    plt.legend(
        title='Cache Algorithms',
        fontsize=20,           # Increase the font size of legend text
        title_fontsize=22,      # Increase the font size of the legend title
        borderpad=0.5,          # Increase padding inside the legend box
        labelspacing=0.5,       # Increase the spacing between entries
        handletextpad=0.5,      # Increase space between marker and text
        loc=position_legend,       # Adjust location if needed
    )
    plt.tight_layout()
    plt.show()