import os
import re
import matplotlib.pyplot as plt
import numpy as np

# Base directory
base_dir = '../simulations/'

# Main memory algorithms
algorithms = ['FCFS', 'FRFCFS', 'FRFCFS_Cap', 'FRFCFS_PriorHit']

# Cache replacement policies
cache_replacements = [
    'REPL_LOW_PREF','REPL_NOT_MRU','REPL_RANDOM','REPL_ROUND_ROBIN',
    'REPL_SHADOW_IDEAL','REPL_TRUE_LRU'
]

# Output files
output_files = [
    'bp.stat.0.out', 'fetch.stat.0.out', 'power.stat.0.out', 'core.stat.0.out',
    'inst.stat.0.out','memory.stat.0.out', 'pref.stat.0.out','stream.stat.0.out'
]

# Metrics
metrics_to_collect = [
    'IPC',
    'L1_HIT_ALL',
    'L1_MISS_ALL',
    'POWER_ICACHE_ACCESS'
]

trace_metrics = {}

def extract_metrics(file_content):
    """Extract the specified metrics from the file content."""
    metrics = {}
    for metric in metrics_to_collect:
        match = re.search(rf'{metric}:?\s*([\d.]+)', file_content)
        if match:
            metrics[metric] = float(match.group(1))
    return metrics

#
# Data Gathering
#
for trace_dir in os.listdir(base_dir):
    trace_path = os.path.join(base_dir, trace_dir)
    if not os.path.isdir(trace_path):
        continue

    trace_metrics[trace_dir] = {}

    for algo in algorithms:
        algo_path = os.path.join(trace_path, algo)
        if not os.path.isdir(algo_path):
            continue

        for repl in cache_replacements:
            algo_repl_key = f"{algo} | {repl}"
            algo_repl_path = os.path.join(algo_path, repl)

            if not os.path.isdir(algo_repl_path):
                continue

            trace_metrics[trace_dir][algo_repl_key] = {}

            for output_file in output_files:
                file_path = os.path.join(algo_repl_path, output_file)
                if os.path.isfile(file_path):
                    with open(file_path, 'r') as f:
                        file_content = f.read()
                    trace_metrics[trace_dir][algo_repl_key].update(
                        extract_metrics(file_content)
                    )

#
# Plotting
#
for trace_dir, combo_dict in trace_metrics.items():
    for metric in metrics_to_collect:

        combos = list(combo_dict.keys())
        if not combos:
            continue

        # Sort combos by ascending metric value
        combos_sorted = sorted(combos, key=lambda c: combo_dict[c].get(metric, 0))
        y_values_sorted = [combo_dict[c].get(metric, 0) for c in combos_sorted]

        if len(y_values_sorted) == 0:
            continue

        plt.figure(figsize=(14, 8))
        x_positions = np.arange(len(combos_sorted))

        # Colors
        cm = plt.cm.get_cmap('tab20')
        bar_colors = [cm(i % 20 / 20.0) for i in range(len(x_positions))]

        # Plot initial bars
        bars = plt.bar(x_positions, y_values_sorted, color=bar_colors)

        #
        # Pass 1: Compress bars above threshold
        #
        max_val = max(y_values_sorted)
        threshold_fraction = 0.90  # Adjust: 90% of max
        compression_factor = 0.5   # portion above threshold is shrunk by 50%

        threshold = threshold_fraction * max_val

        for bar in bars:
            original_height = bar.get_height()
            if original_height > threshold:
                portion_above = original_height - threshold
                compressed_portion = compression_factor * portion_above
                new_height = threshold + compressed_portion
                bar.set_height(new_height)

        #
        # Identify best/worst bar index for highlight
        #
        if metric == 'IPC':
            best_idx = np.argmax(y_values_sorted)  # highest is best
        elif metric == 'L1_HIT_ALL':
            best_idx = np.argmax(y_values_sorted)
        elif metric == 'L1_MISS_ALL':
            best_idx = np.argmin(y_values_sorted)
        elif metric == 'POWER_ICACHE_ACCESS':
            best_idx = np.argmin(y_values_sorted)
        else:
            best_idx = None

        #
        # Pass 2: Label each bar at its compressed height
        #
        for i, bar in enumerate(bars):
            real_val = y_values_sorted[i]     # The *true* metric
            comp_height = bar.get_height()    # The *compressed* bar height

            # Format large numbers
            if real_val >= 1e9:
                disp_val = f'{real_val / 1e9:.2f}B'
            elif real_val >= 1e6:
                disp_val = f'{real_val / 1e6:.2f}M'
            elif real_val >= 1e3:
                disp_val = f'{real_val / 1e3:.2f}K'
            else:
                disp_val = f'{real_val:.2f}'

            annotation_color = 'black'
            if best_idx is not None and i == best_idx:
                if metric in ['IPC', 'L1_HIT_ALL', 'POWER_ICACHE_ACCESS']:
                    annotation_color = 'limegreen'
                elif metric == 'L1_MISS_ALL':
                    annotation_color = 'red'

            # We offset from the *compressed* bar height so the text sits just above it
            offset = 0.01 * max_val
            plt.text(
                x_positions[i],
                comp_height + offset,
                disp_val,
                ha='center',
                rotation=55,
                fontsize=10,
                fontweight='bold',
                color=annotation_color
            )

        #
        # X-axis
        #
        plt.xticks(x_positions, combos_sorted, rotation=45, ha='right', fontsize=9)

        # Title and axes
        try:
            trace_name = trace_dir.split('.')[1]
        except IndexError:
            trace_name = trace_dir
        plt.title(f'Trace: {trace_name} - {metric} (Ascending)', fontsize=16)
        plt.xlabel('Algorithm | Replacement', fontsize=14)
        plt.ylabel(metric, fontsize=14)

        if metric in ['L1_HIT_ALL', 'L1_MISS_ALL']:
            plt.yscale('log')

        plt.legend([])
        plt.tight_layout()
        plt.show()
