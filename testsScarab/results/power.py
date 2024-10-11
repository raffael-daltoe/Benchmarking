import re
import os
import matplotlib.pyplot as plt

# Define the file path
file_path = '../simulations/drmemtrace.macc_matrixrandomaccess.00262.9664.trace/power.stat.0.out'

# Initialize a dictionary to store the extracted metrics
metrics = {
    'Cycles': 0,
    'Instructions': 0,
    'Instructions per Cycle (IPC)': 0,
    'Power Cycles': 0,
    'ICACHE Access': 0,
    'DCACHE Read Access': 0,
    'DCACHE Write Access': 0,
    'LLC Read Access': 0,
    'LLC Write Access': 0,
    'ROB Read Access': 0,
    'ROB Write Access': 0,
}

# Read the file and extract values using regex
with open(file_path, 'r') as file:
    data = file.read()

    # Use regex to find metrics in the file
    metrics['Cycles'] = int(re.search(r'Cycles:\s+(\d+)', data).group(1))
    metrics['Instructions'] = int(re.search(r'Instructions:\s+(\d+)', data).group(1))
    metrics['Instructions per Cycle (IPC)'] = float(re.search(r'IPC:\s+([\d.]+)', data).group(1))
    metrics['Power Cycles'] = int(re.search(r'POWER_CYCLE\s+(\d+)', data).group(1))
    metrics['ICACHE Access'] = int(re.search(r'POWER_ICACHE_ACCESS\s+(\d+)', data).group(1))
    metrics['DCACHE Read Access'] = int(re.search(r'POWER_DCACHE_READ_ACCESS\s+(\d+)', data).group(1))
    metrics['DCACHE Write Access'] = int(re.search(r'POWER_DCACHE_WRITE_ACCESS\s+(\d+)', data).group(1))
    metrics['LLC Read Access'] = int(re.search(r'POWER_LLC_READ_ACCESS\s+(\d+)', data).group(1))
    metrics['LLC Write Access'] = int(re.search(r'POWER_LLC_WRITE_ACCESS\s+(\d+)', data).group(1))
    metrics['ROB Read Access'] = int(re.search(r'POWER_ROB_READ\s+(\d+)', data).group(1))
    metrics['ROB Write Access'] = int(re.search(r'POWER_ROB_WRITE\s+(\d+)', data).group(1))

# Plot the metrics using matplotlib
labels = list(metrics.keys())
values = list(metrics.values())

plt.figure(figsize=(12, 8))
bars = plt.bar(labels, values, color='green')

# Add labels above the bars with the metric values
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval, f'{yval}', ha='center', va='bottom')

plt.ylabel('Metric Values')
plt.xticks(rotation=45, ha="right")  # Rotate the labels to avoid overlap
plt.title('Benchmarking Power Metrics from Trace File')
plt.tight_layout()

# Show the plot
plt.show()
