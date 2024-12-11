import os
import re
import matplotlib.pyplot as plt
from collections import defaultdict

# Define directories and file paths
input_dir = '../sim_outputs/'

# Initialize data structure to store results
data = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # {trace: {policy: {branch_prefetcher: IPC value}}}

# Parse files
for file_name in os.listdir(input_dir):
    if file_name.endswith(".txt"):
        with open(os.path.join(input_dir, file_name), 'r') as file:
            content = file.read()

            # Extract trace name
            trace_match = re.search(r"(.*?)_pol:", file_name)
            if not trace_match:
                continue
            trace = trace_match.group(1)

            # Extract policy
            policy_match = re.search(r"pol:(.*?)_bra:", file_name)
            if not policy_match:
                continue
            policy = policy_match.group(1)

            # Extract branch predictor
            branch_match = re.search(r"bra:(.*?)_pre:", file_name)
            if not branch_match:
                continue
            branch = branch_match.group(1)

            # Extract prefetcher
            prefetcher_match = re.search(r"pre:(.*?)_output.txt", file_name)
            if not prefetcher_match:
                continue
            prefetcher = prefetcher_match.group(1)

            # Extract IPC value
            ipc_match = re.search(r"CPU 0 cumulative IPC: ([\d\.]+)", content)
            if ipc_match:
                ipc = float(ipc_match.group(1))
                data[trace][policy][f"{branch}_{prefetcher}"] = ipc

def plot_everyone():
        
    # Generate bar graph for each trace + policy
    all_ipc_values = []
    #plt.clf()

    for trace, policies in data.items():
        for policy, branch_prefetchers in policies.items():
            # Sort the branch_prefetchers by IPC value
            sorted_items = sorted(branch_prefetchers.items(), key=lambda x: x[1])
            labels = [item[0] for item in sorted_items]
            values = [item[1] for item in sorted_items]

            # Store IPC values for global top 10
            all_ipc_values.extend([(f"{trace} | {policy} | {label}", value) for label, value in zip(labels, values)])

            # Create the bar graph
            plt.figure(figsize=(14, 8))
            bars = plt.bar(labels, values, color=plt.cm.tab20.colors[:len(labels)])

            # Highlight the highest IPC in green
            max_value = max(values)
            for bar, value in zip(bars, values):
                color = 'green' if value == max_value else 'black'
                plt.text(
                    bar.get_x() + bar.get_width() / 2.0, value,
                    f'{value:.2f}',
                    ha='center', va='bottom', fontsize=10, color=color
                )

            plt.xlabel('Branch_Prefetcher', fontsize=14)
            plt.ylabel('IPC', fontsize=14)
            plt.title(f'Trace: {trace} | Algorithm: {policy}', fontsize=16)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            # Show or save the plot
            plt.show()

def plot_10bestIPC():
    # Create a graph for the top 10 IPC values globally
    all_ipc_values = []
    #plt.close()
    #plt.clf()

    for trace, policies in data.items():
        for policy, branch_prefetchers in policies.items():
            # Collect IPC values for global top 10
            all_ipc_values.extend([(f"{trace} | {policy} | {label}", value) for label, value in branch_prefetchers.items()])

    # Sort and filter the top 10 IPC values
    all_ipc_values = sorted(all_ipc_values, key=lambda x: x[1], reverse=True)[:10]
    labels = [item[0] for item in all_ipc_values]
    values = [item[1] for item in all_ipc_values]

    # Plot the top 10 IPC values
    plt.figure(figsize=(14, 8))
    bars = plt.bar(labels, values, color=plt.cm.tab10.colors[:len(labels)])

    # Highlight the highest IPC in green
    max_value = max(values)
    for bar, value in zip(bars, values):
        color = 'green' if value == max_value else 'black'
        plt.text(
            bar.get_x() + bar.get_width() / 2.0, value,
            f'{value:.2f}',
            ha='center', va='bottom', fontsize=10, color=color
        )

    plt.xlabel('Trace | Policy | Branch_Prefetcher', fontsize=14)
    plt.ylabel('IPC', fontsize=14)
    plt.title('Top 10 IPC Values Across All Traces and Policies', fontsize=16)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Show the final top 10 graph
    plt.show()



#plot_everyone()
plot_10bestIPC()