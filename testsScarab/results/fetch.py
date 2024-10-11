import re
import os
import matplotlib.pyplot as plt

# Define the file path
file_path = '../simulations/drmemtrace.macc_matrixrandomaccess.00262.9664.trace/fetch.stat.0.out'

# Initialize a dictionary to store the extracted metrics
metrics = {
    'Cycles': 0,
    'Instructions': 0,
    'Instructions per Cycle': 0,
    'Cache Cycles': 0,
    'Fetch On Path': 0,
    'Total Lost Instructions': 0,
    'Fetch Lost Instructions': 0,
    'ROB Stalls Waiting for DC Miss': 0,
}

# Read the file and extract values using regex
with open(file_path, 'r') as file:
    data = file.read()

    # Use regex to find metrics in the file
    metrics['Cycles'] = int(re.search(r'Cycles:\s+(\d+)', data).group(1))
    metrics['Instructions'] = int(re.search(r'Instructions:\s+(\d+)', data).group(1))
    metrics['Instructions per Cycle'] = float(re.search(r'IPC:\s+([\d.]+)', data).group(1))
    metrics['Cache Cycles'] = int(re.search(r'ICACHE_CYCLE\s+(\d+)', data).group(1))
    metrics['Fetch On Path'] = int(re.search(r'FETCH_ON_PATH\s+(\d+)', data).group(1))
    metrics['Total Lost Instructions'] = int(re.search(r'INST_LOST_TOTAL\s+(\d+)', data).group(1))
    metrics['Fetch Lost Instructions'] = int(re.search(r'INST_LOST_FETCH\s+(\d+)', data).group(1))
    metrics['ROB Stalls Waiting for DC Miss'] = int(re.search(r'INST_LOST_ROB_STALL_WAIT_FOR_DC_MISS\s+(\d+)', data).group(1))

# Plot the metrics using matplotlib
labels = list(metrics.keys())
values = list(metrics.values())

plt.figure(figsize=(10, 6))
bars = plt.bar(labels, values, color='skyblue')

# Add labels above the bars with the metric values
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval, f'{yval}', ha='center', va='bottom')

plt.ylabel('Metric Values (Cycles/Instructions)')
plt.xticks(rotation=15, ha="right")  # Rotate the labels to avoid overlap
plt.title('Benchmarking Metrics from Trace File')
plt.tight_layout()

# Show the plot
plt.show()
