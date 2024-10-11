import re
import matplotlib.pyplot as plt

# Define the file path
file_path = '../sim_outputs/drmemtrace.macc_matrixrandomaccess.00262.9664.trace_lru_output.txt'  # Replace this with your file path

# Initialize a dictionary to store the extracted metrics
metrics = {
    'Warmup IPC': 0,
    'Simulation IPC': 0,
    'LLC Misses': 0,
    'DTLB Misses': 0,
    'ITLB Misses': 0,
    'L1D Misses': 0,
    'L2 Misses': 0,
    'LLC Average Miss Latency (cycles)': 0,
    'DTLB Average Miss Latency (cycles)': 0,
    'L1I Average Miss Latency (cycles)': 0,
    'DRAM Row Buffer Hits': 0,
    'DRAM Row Buffer Misses': 0,
}

# Read the file and extract values using regex
with open(file_path, 'r') as file:
    data = file.read()

    # Extract metrics using regex
    metrics['Warmup IPC'] = float(re.search(r'Warmup finished.*IPC:\s+([\d.]+)', data).group(1))
    metrics['Simulation IPC'] = float(re.search(r'Simulation finished.*IPC:\s+([\d.]+)', data).group(1))
    
    metrics['LLC Misses'] = int(re.search(r'LLC TOTAL\s+ACCESS:.*MISS:\s+(\d+)', data).group(1))
    metrics['DTLB Misses'] = int(re.search(r'cpu0_DTLB TOTAL\s+ACCESS:.*MISS:\s+(\d+)', data).group(1))
    metrics['ITLB Misses'] = int(re.search(r'cpu0_ITLB TOTAL\s+ACCESS:.*MISS:\s+(\d+)', data).group(1))
    metrics['L1D Misses'] = int(re.search(r'cpu0_L1D TOTAL\s+ACCESS:.*MISS:\s+(\d+)', data).group(1))
    metrics['L2 Misses'] = int(re.search(r'cpu0_L2C TOTAL\s+ACCESS:.*MISS:\s+(\d+)', data).group(1))

    metrics['LLC Average Miss Latency (cycles)'] = float(re.search(r'LLC AVERAGE MISS LATENCY:\s+([\d.]+)', data).group(1))
    metrics['DTLB Average Miss Latency (cycles)'] = float(re.search(r'cpu0_DTLB AVERAGE MISS LATENCY:\s+([\d.]+)', data).group(1))
    metrics['L1I Average Miss Latency (cycles)'] = float(re.search(r'cpu0_L1I AVERAGE MISS LATENCY:\s+([\d.]+)', data).group(1))

    metrics['DRAM Row Buffer Hits'] = int(re.search(r'ROW_BUFFER_HIT:\s+(\d+)', data).group(1))
    metrics['DRAM Row Buffer Misses'] = int(re.search(r'ROW_BUFFER_MISS:\s+(\d+)', data).group(1))

# Plot the metrics using matplotlib
labels = list(metrics.keys())
values = list(metrics.values())

plt.figure(figsize=(12, 8))
bars = plt.bar(labels, values, color='lightgreen')

# Add labels above the bars with the metric values
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval, f'{yval}', ha='center', va='bottom')

plt.ylabel('Metric Values')
plt.xticks(rotation=45, ha="right")  # Rotate the labels to avoid overlap
plt.title('ChampSim Benchmarking Metrics')
plt.tight_layout()

# Show the plot
plt.show()
