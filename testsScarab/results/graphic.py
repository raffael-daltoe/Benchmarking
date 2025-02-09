import os
import re
import matplotlib.pyplot as plt
import numpy as np

# Base directory
base_dir = '../simulations/'

# Output files
output_files = [
    'bp.stat.0.out', 'fetch.stat.0.out', 'power.stat.0.out', 'core.stat.0.out',
    'inst.stat.0.out', 'memory.stat.0.out', 'pref.stat.0.out', 'stream.stat.0.out'
]

# Metrics to collect
metrics_to_collect = ['IPC']

trace_metrics = {}

def extract_metrics(file_content):
    """Extract the specified metrics from the file content."""
    metrics = {}
    for metric in metrics_to_collect:
        match = re.search(rf'{metric}:?\s*([\d.]+)', file_content)
        if match:
            metrics[metric] = float(match.group(1))
    return metrics

def extract_trace_name(trace_folder):
    """Extracts the trace name from the full trace string."""
    match = re.search(r'drmemtrace\.(\w+)\.', trace_folder)
    return match.group(1) if match else trace_folder

def extract_replacement_name(repl_folder):
    """Extracts the replacement policy name from 'REPL_*'."""
    return repl_folder.replace('REPL_', '')

# Data Gathering
all_samples = sorted(
    [d for d in os.listdir(base_dir) if d.startswith("Sample")],
    key=lambda x: int(re.search(r'\d+', x).group())
)

for sample_dir in all_samples:
    sample_path = os.path.join(base_dir, sample_dir)
    sample_index = sample_dir.replace("Sample", "")
    trace_metrics[sample_index] = {}
    
    for branch_dir in os.listdir(sample_path):
        branch_path = os.path.join(sample_path, branch_dir)
        if not os.path.isdir(branch_path):
            continue

        for prefetch_dir in os.listdir(branch_path):
            prefetch_path = os.path.join(branch_path, prefetch_dir)
            if not os.path.isdir(prefetch_path):
                continue

            for trace_dir in os.listdir(prefetch_path):
                trace_path = os.path.join(prefetch_path, trace_dir)
                if not os.path.isdir(trace_path):
                    continue
                
                trace_name = extract_trace_name(trace_dir)
                trace_metrics[sample_index].setdefault(branch_dir, {}).setdefault(prefetch_dir, {})
                
                for repl_dir in os.listdir(trace_path):
                    repl_path = os.path.join(trace_path, repl_dir)
                    if not os.path.isdir(repl_path):
                        continue
                    
                    repl_name = extract_replacement_name(repl_dir)
                    trace_metrics[sample_index][branch_dir][prefetch_dir][repl_name] = {}
                    
                    for output_file in output_files:
                        file_path = os.path.join(repl_path, output_file)
                        if os.path.isfile(file_path):
                            with open(file_path, 'r') as f:
                                file_content = f.read()
                            trace_metrics[sample_index][branch_dir][prefetch_dir][repl_name].update(
                                extract_metrics(file_content)
                            )

# Plotting
for sample_index, branch_dict in trace_metrics.items():
    plt.figure(figsize=(14, 8))
    
    bar_positions = []
    bar_labels = []
    bar_values = []
    colors = []
    annotations = []
    
    color_map = ['gray', 'dimgray', 'darkgray', 'lightgray']
    position = 0
    
    dividers = []
    prev_branch = None
    prev_prefetch = None
    
    for branch, prefetch_dict in branch_dict.items():
        for prefetch, repl_dict in prefetch_dict.items():
            subgroup_start = position  # Store initial position of the subgroup
            
            for repl, metric_dict in repl_dict.items():
                y_value = metric_dict.get('IPC', 0)
                bar_positions.append(position)  # Append adjusted position
                bar_labels.append(f'{repl}')
                bar_values.append(y_value)
                colors.append(color_map[int(position) % len(color_map)])  # FIXED: Convert to int
                position += 1  # Reduce spacing between bars

            annotations.append((subgroup_start, f'Branch: {branch}\nPrefetcher: {prefetch}'))
            dividers.append(position - 0.6)  # Adjust divider position slightly


    
    plt.bar(bar_positions, bar_values, color=colors, width=0.4)
    
    for i, value in enumerate(bar_values):
        plt.text(bar_positions[i], value + 0.02, f'{value:.4f}', ha='center', fontsize=10, fontweight='bold')
    
    for divider in dividers[:-1]:  # Remove last divider
        plt.axvline(x=divider, color='black', linestyle='--', linewidth=1)
    
    for start, text in annotations:
        plt.text(start - 0.4, max(bar_values) + 0.7, text, 
                ha='left', va='top', fontsize=14, fontweight='bold',
                bbox=dict(facecolor='black', edgecolor='black', boxstyle='round,pad=0.3'),
                color='white')

    
    plt.xticks(bar_positions, bar_labels, rotation=0, ha='center', fontsize=9)
    plt.title(f'Cache Sample {sample_index} - IPC Analysis', fontsize=16)
    plt.xlabel('Configurations', fontsize=14)
    plt.ylabel('IPC', fontsize=14)
    plt.ylim(0, max(bar_values) + 1 if bar_values else 5)
    plt.tight_layout()
    plt.show()
