import os
import re
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.patches as patches

# Sample number used for the simulation
sample_number = '2'
root_dir = f"../simulations/Sample{sample_number}"

# data[trace][policy][branch_prefetcher] = IPC
data = defaultdict(lambda: defaultdict(dict))


def parse_trace_name(folder_name):
    """
    Example:
      drmemtrace.bt.A.00031.1720.trace => 'bt.A'
      drmemtrace.convolution.00234.7063.trace => 'convolution'
    Rule: Take the portion after the first '.' and ending before the third '.' from the right.
    """
    parts = folder_name.split('.')
    # Ex: drmemtrace.bt.A.00031.1720.trace
    # parts = [drmemtrace, bt, A, 00031, 1720, trace]
    # We want parts[1]..parts[-3], which becomes 'bt.A' or 'convolution'
    return ".".join(parts[1:-3])


def parse_policy_name(folder_name):
    """
    Receives something like "REPL_TRUE_LRU" and returns "LRU"
    Receives "REPL_ROUND_ROBIN" and returns "ROUND ROBIN (FIFO)"
    Otherwise, it removes underscores, e.g.: "REPL_SOME_POLICY" -> "SOME POLICY"
    """
    if folder_name.startswith("REPL_"):
        name = folder_name[5:]
    else:
        name = folder_name

    # Special cases
    if name == "TRUE_LRU":
        return "LRU"
    elif name == "ROUND_ROBIN":
        return "ROUND ROBIN (FIFO)"

    # Otherwise, simply remove underscores
    return name.replace('_', ' ')


def find_ipc_in_file(path):
    """
    Searches for a line with "IPC: X.XXX" and returns the value as a float if found.
    """
    pattern = re.compile(r"IPC:\s*([\d\.]+)")
    with open(path, "r") as f:
        for line in f:
            m = pattern.search(line)
            if m:
                return float(m.group(1))
    return None


# ----------------------------------------------------------------
# 1) Traverse the directory tree to build the 'data' dictionary
# ----------------------------------------------------------------
for branch_dir in os.listdir(root_dir):
    branch_path = os.path.join(root_dir, branch_dir)
    if not os.path.isdir(branch_path):
        continue

    for prefetcher_dir in os.listdir(branch_path):
        prefetcher_path = os.path.join(branch_path, prefetcher_dir)
        if not os.path.isdir(prefetcher_path):
            continue

        for trace_dir in os.listdir(prefetcher_path):
            trace_path = os.path.join(prefetcher_path, trace_dir)
            if not os.path.isdir(trace_path):
                continue

            trace_name = parse_trace_name(trace_dir)

            for policy_dir in os.listdir(trace_path):
                policy_path = os.path.join(trace_path, policy_dir)
                if not os.path.isdir(policy_path):
                    continue

                policy = parse_policy_name(policy_dir)

                for file_name in os.listdir(policy_path):
                    file_path = os.path.join(policy_path, file_name)
                    if not os.path.isfile(file_path):
                        continue

                    ipc_val = find_ipc_in_file(file_path)
                    if ipc_val is not None:
                        # Compose the key "branch_prefetcher"
                        branch_prefetcher = f"{branch_dir} | {prefetcher_dir}"
                        data[trace_name][policy][branch_prefetcher] = ipc_val

# ----------------------------------------------------------------
# 2) Function that plots 3 bars (Worst, Median, Best) for each policy and trace
# ----------------------------------------------------------------
def plot_selected_policies_by_trace_top3(selected_policies, save_path):
    """
    For each trace in 'data' that contains at least one policy from 'selected_policies',
    creates a figure with 3 bars per policy:
       - The worst (lowest IPC)
       - An intermediate (median) value
       - The best (highest IPC)

    Bars for each policy are grouped and separated by dotted lines.
    The highest IPC in each policy group is highlighted in green and bold.
    The policy name is displayed at the top of its group.
    """

    # Grayscale colors (except pure black) and hatching patterns
    colors = ['#666666', '#888888', '#AAAAAA', '#CCCCCC', '#999999', '#BBBBBB']
    hatches = ['////', '\\\\', 'xx', '..', '++', '--']

    # Ensure consistent order for policies
    sorted_policies = sorted(selected_policies)

    # Map a style (color, hatch) for each policy
    style_mapping = {}
    for i, pol in enumerate(sorted_policies):
        style_mapping[pol] = (
            colors[i % len(colors)],
            hatches[i % len(hatches)]
        )

    # Process each trace in alphabetical order
    for trace in sorted(data.keys()):
        x_positions = []
        x_labels = []
        ipcs = []
        bar_policies = []

        # For group boundaries and annotations
        policy_boundaries = []

        offset = 0.0

        # Check if at least one of the selected policies exists for this trace
        any_policy_found = False
        for policy in sorted_policies:
            if policy in data[trace]:
                # Skip if there are not at least 3 entries (for worst, median, best)
                if len(data[trace][policy]) < 3:
                    continue
                any_policy_found = True

        if not any_policy_found:
            # Skip creating a figure if no policy is found
            continue

        for policy in sorted_policies:
            # Process only if the policy exists and has >= 3 entries
            if policy not in data[trace]:
                continue
            if len(data[trace][policy]) < 3:
                continue

            start_idx = len(ipcs)

            # Sort branch_prefetcher entries by IPC value (ascending)
            sorted_items = sorted(data[trace][policy].items(), key=lambda x: x[1])
            # Select Worst, Median, Best
            worst = sorted_items[0]
            best = sorted_items[-1]
            intermediary = sorted_items[len(sorted_items) // 2]
            selected_items = [worst, intermediary, best]

            for bp, ipc_val in selected_items:
                # Format label as "branch | prefetcher" (you may adjust formatting as needed)
                bp_formatted = bp.replace('_', ' | ', 1)
                label = bp_formatted

                x_positions.append(offset)
                x_labels.append(label)
                ipcs.append(ipc_val)
                bar_policies.append(policy)

                offset += 1

            end_idx = len(ipcs) - 1
            if end_idx >= start_idx:
                policy_boundaries.append((policy, start_idx, end_idx))

        if not ipcs:
            continue

        # Determine the Y-axis limit
        global_max = max(ipcs)
        top_ylim = global_max * 1.2 if global_max > 0 else 1
        # Reserve extra top margin for writing the policy name
        top_margin = top_ylim * 0.2
        new_ylim = top_ylim + top_margin

        plt.figure(figsize=(28, 11))
        bar_width = 0.8
        extra_spacing = bar_width / 4.0

        # Draw the bars
        bars = plt.bar(x_positions, ipcs, width=bar_width, edgecolor='black')
        for i, bar in enumerate(bars):
            pol = bar_policies[i]
            facecolor, hatch = style_mapping.get(pol, ('#AAAAAA', ''))
            bar.set_facecolor(facecolor)
            bar.set_hatch(hatch)
            bar.set_edgecolor('black')

        # Highlight the highest IPC in each policy group in green
        for (policy, start_idx, end_idx) in policy_boundaries:
            group_ipcs = ipcs[start_idx:end_idx + 1]
            local_max = max(group_ipcs)
            for bar_idx in range(start_idx, end_idx + 1):
                bar = bars[bar_idx]
                val = ipcs[bar_idx]
                if val == local_max:
                    txt_color = 'green'
                    fw = 'bold'
                else:
                    txt_color = 'black'
                    fw = 'normal'
                plt.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height(),
                    f"{val:.2f}",
                    ha='center',
                    va='bottom',
                    fontsize=14,
                    color=txt_color,
                    fontweight=fw
                )

        # X-axis labels and title
        plt.xticks(x_positions, x_labels, rotation=45, ha='right', fontsize=19)
        plt.xlabel('Branch | Prefetcher', fontsize=24)
        plt.ylabel('IPC', fontsize=24)
        plt.title(f"Trace {trace}: Worst, Intermediate, and Best IPC in each Cache Replacement Policy",
                  fontsize=24, fontweight='normal')
        plt.ylim(0, new_ylim)

        # Dotted lines to separate policy groups
        for i in range(len(policy_boundaries) - 1):
            current = policy_boundaries[i]
            next_group = policy_boundaries[i + 1]
            divider_x = (x_positions[current[2]] + x_positions[next_group[1]]) / 2.0
            plt.vlines(divider_x, 0, new_ylim, colors='black', linestyles='dotted', linewidth=1)

        # Write the policy name at the top of each group
        for (policy, start_idx, end_idx) in policy_boundaries:
            seg_left = x_positions[start_idx] - bar_width * 0.5 - extra_spacing
            seg_right = x_positions[end_idx] + bar_width * 0.5 + extra_spacing
            seg_center = (seg_left + seg_right) / 2.0
            plt.text(
                seg_center,
                new_ylim - top_margin / 2,
                policy,
                ha='center',
                va='top',
                fontsize=24,
                fontweight='bold',
                color='blue'
            )

        plt.tight_layout()
        final_filename = f"{save_path}_{trace}.png"
        # Save the figure; uncomment the next line to save the image
        #plt.savefig(final_filename)
        plt.show()  # Uncomment to display the plot

# -------------------------------------------------------------------------
# 3) Other existing functions:
#    (a) plot_hpc_per_policy
#    (b) plot_convolution_grouped_by_policy
# -------------------------------------------------------------------------
HPC_TRACES = ["bt.A", "is.A", "lu.A", "sp.A"]  # HPC trace set
CONV_TRACE = "convolution"


def plot_hpc_per_policy():
    """
    For each cache policy, creates a graph with 4 groups (bt.A, is.A, lu.A, sp.A).
    Within each group, displays the available bars (branch_prefetcher).
    The bar with the highest IPC in each group is highlighted in green.
    """
    # Discover all available policies
    all_policies = set()
    for tname, pol_dict in data.items():
        for pol in pol_dict:
            all_policies.add(pol)
    all_policies = sorted(list(all_policies))

    # Grayscale palette and hatching patterns
    grayscale_colors = ['#666666', '#888888', '#AAAAAA', '#CCCCCC', '#999999', '#BBBBBB']
    hatch_patterns = ['////', '\\\\', 'xx', '..', '++', '--']

    # For each policy, generate one figure
    for policy in all_policies:
        x_positions = []
        x_labels = []
        ipcs = []
        group_centers = []  # To center each trace group for labeling
        group_indices = []  # Indices of the bars for each trace group

        offset = 0

        # Process each trace in the desired HPC_TRACES order
        for trace in HPC_TRACES:
            if trace not in data or policy not in data[trace]:
                # Skip if this trace/policy does not exist
                continue

            bp_dict = data[trace][policy]
            group_start = offset
            current_indices = []

            for bp_pref, val in sorted(bp_dict.items()):
                x_positions.append(offset)
                x_labels.append(bp_pref)
                ipcs.append(val)
                current_indices.append(len(ipcs) - 1)
                offset += 1

            group_end = offset - 1
            if group_end >= group_start:
                center = (group_start + group_end) / 2.0
                group_centers.append((center, trace))
                group_indices.append(current_indices)

            # Extra space to separate groups
            offset += 1

        if not ipcs:
            continue

        plt.figure(figsize=(14, 8))
        bars = plt.bar(x_positions, ipcs, color='white', edgecolor='black')

        for i, bar in enumerate(bars):
            cidx = i % len(grayscale_colors)
            hidx = i % len(hatch_patterns)
            bar.set_facecolor(grayscale_colors[cidx])
            bar.set_hatch(hatch_patterns[hidx])
            bar.set_edgecolor('black')

        global_max = max(ipcs)
        top_ylim = global_max * 1.2 if global_max > 0 else 1
        plt.ylim(0, top_ylim)

        trace_margin = top_ylim * 0.06

        # Highlight the highest IPC in each group
        for group in group_indices:
            local_ipcs = [ipcs[idx] for idx in group]
            if not local_ipcs:
                continue
            local_max = max(local_ipcs)
            for idx in group:
                val = ipcs[idx]
                bar = bars[idx]
                if val == local_max:
                    text_color = 'green'
                    fw = 'bold'
                else:
                    text_color = 'black'
                    fw = 'normal'

                plt.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    val,
                    f"{val:.2f}",
                    ha='center', va='bottom',
                    fontsize=10, color=text_color, fontweight=fw
                )

        plt.xticks(x_positions, x_labels, rotation=45, ha='right', fontsize=10)
        plt.xlabel("Branch | Prefetcher", fontsize=14)
        plt.ylabel("IPC", fontsize=14)
        plt.title(f"Policy: {policy} - IPC Grouped by Trace", fontsize=16)

        ax = plt.gca()
        bar_width = bars[0].get_width() if bars else 0.8
        extra_spacing = bar_width / 4.0

        for center, trace_name in group_centers:
            plt.text(
                center,
                top_ylim - trace_margin,
                trace_name,
                ha='center',
                va='top',
                fontsize=12,
                fontweight='bold',
                color='blue'
            )

        for group in group_indices:
            left_idx = group[0]
            right_idx = group[-1]
            left_bound = x_positions[left_idx] - bar_width * 0.5 - extra_spacing
            right_bound = x_positions[right_idx] + bar_width * 0.5 + extra_spacing
            w = right_bound - left_bound
            rect = patches.Rectangle(
                (left_bound, 0), w, top_ylim,
                linewidth=1, edgecolor='black', facecolor='none', linestyle='--'
            )
            ax.add_patch(rect)

        plt.tight_layout()
        plt.show()


def plot_convolution_grouped_by_policy():
    """
    Generates a single graph for the 'convolution' trace.
    Groups the bars by policy (each policy is a separate block).
    Highlights the bar with the highest IPC in each block.
    """
    trace = CONV_TRACE
    if trace not in data:
        print("No data for convolution!")
        return

    all_policies = sorted(data[trace].keys())
    if not all_policies:
        print("No policies for convolution!")
        return

    grayscale_colors = ['#000000', '#555555', '#AAAAAA', '#FFFFFF']
    hatch_patterns = ['', '-', '++', 'xx']

    x_positions = []
    x_labels = []
    ipcs = []
    group_centers = []
    group_indices = []
    offset = 0.0

    for policy in all_policies:
        bp_dict = data[trace][policy]
        if not bp_dict:
            continue

        group_start = offset
        current_indices = []

        for bp, val in sorted(bp_dict.items()):
            x_positions.append(offset)
            x_labels.append(f"{bp}")
            ipcs.append(val)
            current_indices.append(len(ipcs) - 1)
            offset += 1

        group_end = offset - 1
        if group_end >= group_start:
            center = (group_start + group_end) / 2.0
            group_centers.append((center, policy))
            group_indices.append(current_indices)

        offset += 1

    if not ipcs:
        print("No IPC values found for convolution!")
        return

    plt.figure(figsize=(14, 8))
    bars = plt.bar(x_positions, ipcs, color='white', edgecolor='black')

    for i, bar in enumerate(bars):
        cidx = i % len(grayscale_colors)
        hidx = i % len(hatch_patterns)
        bar.set_facecolor(grayscale_colors[cidx])
        bar.set_hatch(hatch_patterns[hidx])

    global_max = max(ipcs)
    top_ylim = global_max * 1.2 if global_max > 0 else 1
    plt.ylim(0, top_ylim)

    for group in group_indices:
        local_ipcs = [ipcs[idx] for idx in group]
        if not local_ipcs:
            continue
        local_max = max(local_ipcs)
        for idx in group:
            val = ipcs[idx]
            bar = bars[idx]
            if val == local_max:
                txt_color = 'green'
                fw = 'bold'
            else:
                txt_color = 'black'
                fw = 'normal'
            plt.text(
                bar.get_x() + bar.get_width() / 2.0,
                val,
                f"{val:.2f}",
                ha='center', va='bottom',
                color=txt_color, fontweight=fw
            )

    plt.xticks(x_positions, x_labels, rotation=45, ha='right', fontsize=10)
    plt.xlabel("Branch | Prefetcher", fontsize=14)
    plt.ylabel("IPC", fontsize=14)
    plt.title("Trace: Convolution", fontsize=16, fontweight='normal')

    ax = plt.gca()
    bar_width = bars[0].get_width() if bars else 0.8
    extra_spacing = bar_width / 4.0
    policy_margin = top_ylim * 0.06

    for center, policy_name in group_centers:
        plt.text(
            center,
            top_ylim - policy_margin,
            policy_name,
            ha='center',
            va='top',
            fontsize=14,
            color='black',
            fontweight='normal'
        )

    for group in group_indices:
        if not group:
            continue
        left_idx = group[0]
        right_idx = group[-1]
        left_bound = x_positions[left_idx] - bar_width * 0.5 - extra_spacing
        right_bound = x_positions[right_idx] + bar_width * 0.5 + extra_spacing
        w = right_bound - left_bound
        rect = patches.Rectangle(
            (left_bound, 0), w, top_ylim,
            linewidth=1, edgecolor='black', facecolor='none', linestyle='--'
        )
        ax.add_patch(rect)

    plt.tight_layout()
    plt.show()


# -------------------------------------------------------------------------
# 4) Example usage of the 3-bar plot (Worst, Median, Best) for selected policies.
#    Simply call the function with the list of desired policies and a file prefix.
#
# Example:
#    plot_selected_policies_by_trace_top3(['LRU', 'ROUND ROBIN (FIFO)'], 'TOP3')
# This will create a PNG image for each trace corresponding to these policies,
# named as: "TOP3_<trace>.png".
#
# plot_selected_policies_by_trace_top3(['LRU', 'ROUND ROBIN (FIFO)'], 'TOP3')

save_path = f"/mnt/c/Users/Raffael/Desktop/Results_Report/Scarab/Sample{sample_number}/"

plot_selected_policies_by_trace_top3(['LRU', 'ROUND ROBIN (FIFO)', 'RANDOM'], save_path)

#################################################################################
# End of Script
#################################################################################
