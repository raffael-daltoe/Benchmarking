import os
import re
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.patches as patches  # For drawing rectangles as limiters

#########################################################
#                 EDIT ONLY THIS PART                   #
#########################################################

Sample = '1'
trace = "is.A"
root = f"../sim_outputs/{trace}/Sample{Sample}"

# Data structure remains the same:
# data[trace_name][policy][f"{branch}_{prefetcher}"] = IPC value
data = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

# Walk through the directory tree: branch -> prefetcher -> policy
for branch_dir in os.listdir(root):
    branch_path = os.path.join(root, branch_dir)
    if not os.path.isdir(branch_path):
        continue
    
    for prefetch_dir in os.listdir(branch_path):
        prefetch_path = os.path.join(branch_path, prefetch_dir)
        if not os.path.isdir(prefetch_path):
            continue
        
        for policy_dir in os.listdir(prefetch_path):
            policy_path = os.path.join(prefetch_path, policy_dir)
            if not os.path.isdir(policy_path):
                continue
            
            # Process each text file in the policy directory
            for file_name in os.listdir(policy_path):
                if file_name.endswith(".txt"):
                    full_path = os.path.join(policy_path, file_name)
                    with open(full_path, 'r') as f:
                        content = f.read()
                        # New regex: look for "system.cpu.ipc" followed by the IPC value
                        ipc_match = re.search(r"system\.cpu\.ipc\s+([\d\.]+)", content)
                        if ipc_match:
                            ipc_value = float(ipc_match.group(1))
                            # Store the value; we use 'trace' as a fixed key,
                            # 'policy_dir' as the cache replacement policy,
                            # and combine branch and prefetcher for the key.
                            data[trace][policy_dir][f"{branch_dir}_{prefetch_dir}"] = ipc_value


#########################################################
#           EVERYTHING ELSE (PLOTTING) UNCHANGED        #
#########################################################

def plot_everyone():
    # Generate bar graph for each trace + policy
    all_ipc_values = []

    for trace_name, policies in data.items():
        for policy, branch_prefetchers in policies.items():
            # Sort by IPC value
            sorted_items = sorted(branch_prefetchers.items(), key=lambda x: x[1])
            labels = [item[0] for item in sorted_items]  # these keys are already branch_prefetcher only
            values = [item[1] for item in sorted_items]

            all_ipc_values.extend([(f"{trace_name} | {policy} | {lbl}", val)
                                   for lbl, val in zip(labels, values)])

            plt.figure(figsize=(14, 8))
            bars = plt.bar(labels, values, color=plt.cm.tab20.colors[:len(labels)])

            # Highlight max
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
            plt.title(f'Trace: {trace_name} | Algorithm: {policy}', fontsize=16)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.show()


def plot_10bestIPC():
    # Collect all IPC values globally
    all_ipc_values = []
    for trace_name, policies in data.items():
        for policy, branch_prefetchers in policies.items():
            for bp, ipc_val in branch_prefetchers.items():
                # Remove policy from label: only include trace and branch_prefetcher
                all_ipc_values.append((f"{trace_name} | {bp}", ipc_val))

    # Sort and pick top 10
    all_ipc_values = sorted(all_ipc_values, key=lambda x: x[1], reverse=True)[:10]
    labels = [item[0] for item in all_ipc_values]
    values = [item[1] for item in all_ipc_values]

    plt.figure(figsize=(14, 8))
    bars = plt.bar(labels, values, color=plt.cm.tab10.colors[:len(labels)])

    max_value = max(values)
    for bar, value in zip(bars, values):
        color = 'green' if value == max_value else 'black'
        plt.text(
            bar.get_x() + bar.get_width() / 2.0, value,
            f'{value:.2f}',
            ha='center', va='bottom', fontsize=10, color=color
        )

    plt.xlabel('Trace | Branch_Prefetcher', fontsize=14)
    plt.ylabel('IPC', fontsize=14)
    plt.title('Top 10 IPC Values Across All Traces and Policies', fontsize=16)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()


def plot_eachtrace():
    for trace_name, policies in data.items():
        # Gather all for this trace
        aggregated_data = {}
        for policy, branch_prefetchers in policies.items():
            for bp, ipc in branch_prefetchers.items():
                # Only keep branch_prefetcher information
                aggregated_data[f"{bp}"] = ipc

        # Sort by IPC
        sorted_items = sorted(aggregated_data.items(), key=lambda x: x[1])
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]

        plt.figure(figsize=(14, 8))
        bars = plt.bar(labels, values, color=plt.cm.tab20.colors[:len(labels)])
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
        plt.title(f'Trace: {trace_name} - IPC Comparison', fontsize=16)
        plt.xticks(rotation=90, ha='right')
        plt.tight_layout()
        plt.show()


def plot_branch_prefetcher_across_policies():
    for trace_name, policies in data.items():
        # group by (branch_prefetcher)
        branch_prefetchers = defaultdict(dict)
        for policy, bp_dict in policies.items():
            for bp, ipc in bp_dict.items():
                branch_prefetchers[bp][policy] = ipc
        
        for bp, ipc_values in branch_prefetchers.items():
            pols = list(ipc_values.keys())
            vals = list(ipc_values.values())
            
            sorted_items = sorted(zip(pols, vals), key=lambda x: x[1])
            sorted_policies = [p for p, _ in sorted_items]
            sorted_values = [v for _, v in sorted_items]

            plt.figure(figsize=(14, 8))
            bars = plt.bar(sorted_policies, sorted_values,
                           color=plt.cm.tab10.colors[:len(sorted_policies)])
            max_value = max(sorted_values)
            for bar, value in zip(bars, sorted_values):
                color = 'green' if value == max_value else 'black'
                plt.text(bar.get_x() + bar.get_width() / 2.0,
                         value, f'{value:.2f}', ha='center', va='bottom',
                         fontsize=10, color=color)
            
            plt.xlabel('Policy', fontsize=14)
            plt.ylabel('IPC', fontsize=14)
            plt.title(f'Trace: {trace_name} | Branch_Prefetcher: {bp}', fontsize=16)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.show()


def plot_policy_group_by_trace():
    """
    For each policy (replacement policy), create a bar chart in black and gray tones,
    using simple hatch patterns (no stars or bubbles).
    
    - Each bar shows its IPC value on top.
    - Bars are grouped by trace, with a dashed black rectangle enclosing each group.
    - The best IPC in each trace group is highlighted by changing its numeric label color/weight.
    - The trace name is placed near the top of the chart area.
    - Rectangles extend outward from the group by half a bar width plus extra spacing.
    - The x-axis labels are formatted as "Branch | Prefetcher" by replacing only the first underscore.
    """
    
    # Collect all policies
    policies_set = set()
    for trace, policies in data.items():
        for policy in policies.keys():
            policies_set.add(policy)
    policies_list = sorted(list(policies_set))
    
    # A small grayscale palette for higher contrast (black -> dark gray -> medium gray -> white)
    grayscale_colors = ['#000000', '#555555', '#AAAAAA', '#FFFFFF']
    
    # Simple hatch patterns (line-based only, no stars or bubbles)
    hatch_patterns = ['', '-', '++', 'xx']
    
    for policy in policies_list:
        x_positions = []    # x positions for each bar
        x_labels = []       # labels (formatted as "Branch | Prefetcher")
        ipcs = []           # IPC values
        group_centers = []  # center x positions for each trace group
        group_indices = []  # indices of bars in each trace group
        
        offset = 0  # starting x position
        
        # Iterate over traces in sorted order
        for trace in sorted(data.keys()):
            if policy not in data[trace]:
                continue
            
            branch_prefetchers = data[trace][policy]
            group_start = offset
            current_group_indices = []
            
            for bp, ipc in branch_prefetchers.items():
                # Replace only the first underscore with " | "
                bp_formatted = bp.replace('_', ' | ', 1)
                
                x_positions.append(offset)
                x_labels.append(bp_formatted)
                ipcs.append(ipc)
                current_group_indices.append(len(ipcs) - 1)
                offset += 1
            
            group_end = offset - 1
            if group_end >= group_start:
                center = (group_start + group_end) / 2.0
                group_centers.append((center, trace))
                group_indices.append(current_group_indices)
            
            # Add spacing between groups
            offset += 1
        
        # Create the figure for the current policy
        plt.figure(figsize=(14, 8))
        
        # Draw bars initially with white fill and black edge
        bars = plt.bar(x_positions, ipcs, color='white', edgecolor='black')
        
        # Assign grayscale colors + hatch patterns to each bar
        for i, bar in enumerate(bars):
            color_index = i % len(grayscale_colors)
            hatch_index = i % len(hatch_patterns)
            bar.set_facecolor(grayscale_colors[color_index])
            bar.set_hatch(hatch_patterns[hatch_index])
            bar.set_edgecolor('black')
        
        # Determine bar width (defaults to 0.8 in Matplotlib)
        bar_width = bars[0].get_width() if len(bars) > 0 else 0.8
        
        # Extra spacing outward for limiter rectangles
        extra_spacing = bar_width / 4.0
        
        # Compute y-axis upper bound
        global_max = max(ipcs) if ipcs else 0
        top_ylim = global_max * 1.2 if global_max > 0 else 1
        plt.ylim(0, top_ylim)
        
        # Margin for placing trace names inside the chart area
        trace_margin = top_ylim * 0.06
        
        # Highlight best IPC numeric label in each trace group
        for group in group_indices:
            group_ipcs = [ipcs[i] for i in group]
            if not group_ipcs:
                continue
            group_max = max(group_ipcs)
            for i in group:
                bar = bars[i]
                if ipcs[i] == group_max:
                    text_color = 'green'
                    font_weight = 'bold'
                else:
                    text_color = 'black'
                    font_weight = 'normal'
                
                plt.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height(),
                    f'{ipcs[i]:.2f}',
                    ha='center',
                    va='bottom',
                    fontsize=10,
                    color=text_color,
                    fontweight=font_weight
                )
        
        # Configure x-axis labels
        plt.xticks(x_positions, x_labels, rotation=45, ha='right', fontsize=10)
        plt.xlabel('Branch | Prefetcher', fontsize=14)
        plt.ylabel('IPC', fontsize=14)
        plt.title(f'Policy: {policy} - IPC Grouped by Trace', fontsize=16)
        
        # Place trace names near the top inside the chart
        for center, trace in group_centers:
            plt.text(
                center,
                top_ylim - trace_margin,
                trace,
                ha='center',
                va='top',
                fontsize=12,
                fontweight='bold',
                color='blue'
            )
        
        # Draw dashed black rectangles around each trace group (outward)
        ax = plt.gca()
        for group in group_indices:
            left_index = group[0]
            right_index = group[-1]
            
            left_bound = x_positions[left_index] - bar_width * 0.5 - extra_spacing
            right_bound = x_positions[right_index] + bar_width * 0.5 + extra_spacing
            width = right_bound - left_bound
            
            rect = patches.Rectangle(
                (left_bound, 0),
                width,
                top_ylim,
                linewidth=1,
                edgecolor='black',
                facecolor='none',
                linestyle='--'
            )
            ax.add_patch(rect)
        
        plt.tight_layout()
        plt.show()


def plot_selected_policies_by_trace(selected_policies, save_path):
    """
    For each trace in the data that has at least one policy in 'selected_policies',
    create a separate figure. The figure’s title is the trace name.

    Within each figure:
      - Bars are grouped by policy.
      - Each policy’s bars use a distinct non-black grayscale color + a hatch (texture).
      - Vertical dotted lines separate policy groups.
      - The policy name is written at the top in black (not bold).
      - Each bar is labeled with its IPC value (the highest bar *within each policy group* 
        is highlighted in green/bold).
    """
    # A small set of grayscale colors (not pure black or white) plus some hatch patterns.
    colors = ['#666666', '#888888', '#AAAAAA', '#CCCCCC', '#999999', '#BBBBBB']
    hatches = ['////', '\\\\', 'xx', '..', '++', '--']

    # Sort policies to ensure consistent order
    sorted_policies = sorted(selected_policies)

    # Build a style map: each policy -> (color, hatch)
    style_mapping = {}
    for i, pol in enumerate(sorted_policies):
        style_mapping[pol] = (
            colors[i % len(colors)],
            hatches[i % len(hatches)]
        )

    # Loop over each trace in the data
    for trace in sorted(data.keys()):
        # Collect bars for the current trace
        x_positions = []
        x_labels = []
        ipcs = []
        bar_policies = []

        # We'll store (policy, first_idx, last_idx) to draw dividers & labels
        policy_boundaries = []

        offset = 0.0
        for policy in sorted_policies:
            if policy in data[trace]:
                start_idx = len(ipcs)
                # Sort branch/prefetchers for consistent ordering
                for bp, ipc_val in sorted(data[trace][policy].items()):
                    bp_formatted = bp.replace('_', ' | ', 1)
                    # Remove the policy portion from the label
                    label = bp_formatted
                    x_positions.append(offset)
                    x_labels.append(label)
                    ipcs.append(ipc_val)
                    bar_policies.append(policy)
                    offset += 1
                end_idx = len(ipcs) - 1
                if end_idx >= start_idx:
                    policy_boundaries.append((policy, start_idx, end_idx))

        # Skip if no data for this trace
        if not ipcs:
            continue

        # Compute the y-limit (plus margin at the top for policy labels)
        global_max = max(ipcs)
        top_ylim = global_max * 1.2 if global_max > 0 else 1
        top_margin = top_ylim * 0.2
        new_ylim = top_ylim + top_margin

        # Create a new figure for this trace
        plt.figure(figsize=(24, 14))
        bar_width = 0.8
        extra_spacing = bar_width / 4.0

        # Plot bars
        bars = plt.bar(x_positions, ipcs, width=bar_width, edgecolor='black')
        for i, bar in enumerate(bars):
            cidx = i % len(colors)
            hidx = i % len(hatches)
            bar.set_facecolor(colors[cidx])
            bar.set_hatch(hatches[hidx])
            bar.set_edgecolor('black')

        # Highlight local maximum *within each policy group*.
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
                    fontsize=10,
                    color=txt_color,
                    fontweight=fw
                )

        # X-axis labels, trace title
        plt.xticks(x_positions, x_labels, rotation=45, ha='right', fontsize=10)
        plt.xlabel('Branch | Prefetcher', fontsize=14)
        plt.ylabel('IPC', fontsize=14)
        plt.title(f"Trace: {trace}", fontsize=16, fontweight='normal')
        plt.ylim(0, new_ylim)

        # Draw vertical dotted lines between policy groups
        for i in range(len(policy_boundaries) - 1):
            current = policy_boundaries[i]
            next_group = policy_boundaries[i + 1]
            divider_x = (x_positions[current[2]] + x_positions[next_group[1]]) / 2.0
            plt.vlines(divider_x, 0, new_ylim, colors='black', linestyles='dotted', linewidth=1)

        # Annotate each policy name in black (not bold) at the top of its segment
        for (policy, start_idx, end_idx) in policy_boundaries:
            seg_left = x_positions[start_idx] - bar_width * 0.5 - extra_spacing
            seg_right = x_positions[end_idx] + bar_width * 0.5 + extra_spacing
            seg_center = (seg_left + seg_right) / 2.0
            plt.text(seg_center, new_ylim - top_margin / 2,
                     policy, ha='center', va='top',
                     fontsize=14, fontweight='normal', color='black')

        plt.tight_layout()
        final_filename = f"{save_path}{trace}.png"
        plt.savefig(final_filename)
        plt.show()


def plot_selected_policies_by_trace_top5(selected_policies, save_path):
    """
    For each trace in the data that has at least one policy in 'selected_policies',
    create a separate figure that plots only the top 5 IPC values (per policy).
    
    Within each figure:
      - Bars are grouped by policy.
      - Each policy's bars use a distinct non-black grayscale color + a hatch (texture).
      - Vertical dotted lines separate policy groups.
      - The policy name is written at the top in black (not bold).
      - Each bar is labeled with its IPC value (the highest bar within each policy group is highlighted in green/bold).
    """
    colors = ['#666666', '#888888', '#AAAAAA', '#CCCCCC', '#999999', '#BBBBBB']
    hatches = ['////', '\\\\', 'xx', '..', '++', '--']

    sorted_policies = sorted(selected_policies)

    style_mapping = {}
    for i, pol in enumerate(sorted_policies):
        style_mapping[pol] = (
            colors[i % len(colors)],
            hatches[i % len(hatches)]
        )

    for trace in sorted(data.keys()):
        x_positions = []
        x_labels = []
        ipcs = []
        bar_policies = []
        policy_boundaries = []

        offset = 0.0
        for policy in sorted_policies:
            if policy in data[trace]:
                start_idx = len(ipcs)
                sorted_items = sorted(data[trace][policy].items(), key=lambda x: x[1], reverse=True)
                top_items = sorted_items[:4]
                for bp, ipc_val in top_items:
                    bp_formatted = bp.replace('_', ' | ', 1)
                    # Remove the policy portion from the label:
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

        global_max = max(ipcs)
        top_ylim = global_max * 1.2 if global_max > 0 else 1
        top_margin = top_ylim * 0.2
        new_ylim = top_ylim + top_margin

        plt.figure(figsize=(24, 14))
        bar_width = 0.8
        extra_spacing = bar_width / 4.0

        bars = plt.bar(x_positions, ipcs, width=bar_width, edgecolor='black')
        for i, bar in enumerate(bars):
            cidx = i % len(colors)
            hidx = i % len(hatches)
            bar.set_facecolor(colors[cidx])
            bar.set_hatch(hatches[hidx])
            bar.set_edgecolor('black')

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
                    fontsize=10,
                    color=txt_color,
                    fontweight=fw
                )

        plt.xticks(x_positions, x_labels, rotation=45, ha='right', fontsize=10)
        plt.xlabel('Branch | Prefetcher', fontsize=14)
        plt.ylabel('IPC', fontsize=14)
        plt.title(f"Trace: {trace}", fontsize=16, fontweight='normal')
        plt.ylim(0, new_ylim)

        for i in range(len(policy_boundaries) - 1):
            current = policy_boundaries[i]
            next_group = policy_boundaries[i + 1]
            divider_x = (x_positions[current[2]] + x_positions[next_group[1]]) / 2.0
            plt.vlines(divider_x, 0, new_ylim, colors='black', linestyles='dotted', linewidth=1)

        for (policy, start_idx, end_idx) in policy_boundaries:
            seg_left = x_positions[start_idx] - bar_width * 0.5 - extra_spacing
            seg_right = x_positions[end_idx] + bar_width * 0.5 + extra_spacing
            seg_center = (seg_left + seg_right) / 2.0
            plt.text(seg_center, new_ylim - top_margin / 2,
                     policy, ha='center', va='top',
                     fontsize=14, fontweight='normal', color='black')

        plt.tight_layout()
        final_filename = f"{save_path}_{trace}.png"
        plt.savefig(final_filename)
        plt.show()


def plot_selected_policies_by_trace_top3(selected_policies, save_path):
    """
    For each trace in the data that has at least one policy in 'selected_policies',
    create a separate figure that plots 3 selected IPC values per policy:
      - The Worst (lowest) IPC,
      - An Intermediary (median) IPC,
      - The Best (highest) IPC.
    
    Within each figure:
      - Bars are grouped by policy.
      - Each policy's bars use a distinct non-black grayscale color + a hatch (texture).
      - Vertical dotted lines separate policy groups.
      - The policy name is written at the top in black (not bold).
      - Each bar is labeled with its IPC value; the Best value (highest) within each policy group is highlighted in green and bold.
    """
    colors = ['#666666', '#888888', '#AAAAAA', '#CCCCCC', '#999999', '#BBBBBB']
    hatches = ['////', '\\\\', 'xx', '..', '++', '--']

    sorted_policies = sorted(selected_policies)

    style_mapping = {}
    for i, pol in enumerate(sorted_policies):
        style_mapping[pol] = (
            colors[i % len(colors)],
            hatches[i % len(hatches)]
        )

    for trace in sorted(data.keys()):
        x_positions = []
        x_labels = []
        ipcs = []
        bar_policies = []
        policy_boundaries = []

        offset = 0.0
        for policy in sorted_policies:
            if policy in data[trace]:
                if len(data[trace][policy]) < 3:
                    continue

                start_idx = len(ipcs)
                sorted_items = sorted(data[trace][policy].items(), key=lambda x: x[1])
                worst = sorted_items[0]
                best = sorted_items[-1]
                intermediary = sorted_items[len(sorted_items) // 2]
                selected_items = [worst, intermediary, best]
                for bp, ipc_val in selected_items:
                    bp_formatted = bp.replace('_', ' | ', 1)
                    # Remove policy from label:
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

        global_max = max(ipcs)
        top_ylim = global_max * 1.2 if global_max > 0 else 1
        top_margin = top_ylim * 0.2
        new_ylim = top_ylim + top_margin

        plt.figure(figsize=(28, 11))
        bar_width = 0.8
        extra_spacing = bar_width / 4.0

        bars = plt.bar(x_positions, ipcs, width=bar_width, edgecolor='black')
        for i, bar in enumerate(bars):
            policy = bar_policies[i]
            facecolor, hatch = style_mapping.get(policy, ('#AAAAAA', ''))
            bar.set_facecolor(facecolor)
            bar.set_hatch(hatch)
            bar.set_edgecolor('black')

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

        plt.xticks(x_positions, x_labels, rotation=45, ha='right', fontsize=19)
        plt.xlabel('Branch | Prefetcher', fontsize=24)
        plt.ylabel('IPC', fontsize=24)
        plt.title(f"Trace {trace}: Worst, Intermediate, and Best Case Analysis in each Cache Replacement", fontsize=24, fontweight='normal')
        plt.ylim(0, new_ylim)

        for i in range(len(policy_boundaries) - 1):
            current = policy_boundaries[i]
            next_group = policy_boundaries[i + 1]
            divider_x = (x_positions[current[2]] + x_positions[next_group[1]]) / 2.0
            plt.vlines(divider_x, 0, new_ylim, colors='black', linestyles='dotted', linewidth=1)

        for (policy, start_idx, end_idx) in policy_boundaries:
            seg_left = x_positions[start_idx] - bar_width * 0.5 - extra_spacing
            seg_right = x_positions[end_idx] + bar_width * 0.5 + extra_spacing
            seg_center = (seg_left + seg_right) / 2.0
            plt.text(seg_center, new_ylim - top_margin / 2,
                     policy, ha='center', va='top',
                     fontsize=24, fontweight='bold', color='blue')

        plt.tight_layout()
        final_filename = f"{save_path}{trace}.png"
        #plt.savefig(final_filename)
        plt.show()


def plot_top3_by_trace():
    """
    For each trace:
      - Collect all branch/prefetcher results from all policies.
      - Sort them in descending order by IPC.
      - Keep only the top three results.
    Then plot all traces in one figure:
      - Each trace group is separated by extra spacing and enclosed in a dashed rectangle.
      - Each bar shows its IPC value on top, and the best in each group is highlighted (green, bold).
      - The x-axis label shows "Branch | Prefetcher (Policy)".
      - The trace name is placed at the top of its group.
    """
    policies_set = set()
    for trace in data:
        for policy in data[trace]:
            policies_set.add(policy)
    policies_list = sorted(list(policies_set))
    
    grayscale_colors = ['#000000', '#555555', '#AAAAAA', '#FFFFFF']
    hatch_patterns = ['', '-', '++', 'xx']
    policy_styles = {}
    for i, policy in enumerate(policies_list):
        policy_styles[policy] = {
            'color': grayscale_colors[i % len(grayscale_colors)],
            'hatch': hatch_patterns[i % len(hatch_patterns)]
        }
    
    x_positions = []
    x_labels = []
    ipcs = []
    bar_policies = []
    group_centers = []
    group_indices = []
    offset = 0

    for trace in sorted(data.keys()):
        bars_in_trace = []
        for policy, bp_data in data[trace].items():
            for bp, ipc in bp_data.items():
                bars_in_trace.append((policy, bp, ipc))
        
        if not bars_in_trace:
            continue
        
        bars_in_trace.sort(key=lambda x: x[2], reverse=True)
        top_bars = bars_in_trace[:3]
        
        group_start_index = len(x_positions)
        for policy, bp, ipc in top_bars:
            bp_formatted = bp.replace('_', ' | ', 1)
            # Remove the policy portion so the label is only branch/prefetcher:
            label = bp_formatted
            x_positions.append(offset)
            x_labels.append(label)
            ipcs.append(ipc)
            bar_policies.append(policy)
            offset += 1
        group_end_index = len(x_positions) - 1
        group_center = (x_positions[group_start_index] + x_positions[group_end_index]) / 2.0
        group_centers.append((group_center, trace))
        group_indices.append(list(range(group_start_index, len(x_positions))))
        offset += 1

    plt.figure(figsize=(14, 8))
    
    bars = plt.bar(x_positions, ipcs, color='white', edgecolor='black')
    
    for i, bar in enumerate(bars):
        policy = bar_policies[i]
        style = policy_styles.get(policy, {'color': 'gray', 'hatch': ''})
        bar.set_facecolor(style['color'])
        bar.set_hatch(style['hatch'])
        bar.set_edgecolor('black')
    
    bar_width = bars[0].get_width() if bars else 0.8
    extra_spacing = bar_width / 4.0
    global_max = max(ipcs) if ipcs else 0
    top_ylim = global_max * 1.2 if global_max > 0 else 1
    plt.ylim(0, top_ylim)
    
    trace_margin = top_ylim * 0.06
    
    for group in group_indices:
        group_ipcs = [ipcs[i] for i in group]
        if not group_ipcs:
            continue
        group_max = max(group_ipcs)
        for i in group:
            bar = bars[i]
            if ipcs[i] == group_max:
                text_color = 'green'
                font_weight = 'bold'
            else:
                text_color = 'black'
                font_weight = 'normal'
            plt.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height(),
                f'{ipcs[i]:.2f}',
                ha='center',
                va='bottom',
                fontsize=10,
                color=text_color,
                fontweight=font_weight
            )
    
    plt.xticks(x_positions, x_labels, rotation=45, ha='right', fontsize=10)
    plt.xlabel('Branch | Prefetcher', fontsize=14)
    plt.ylabel('IPC', fontsize=14)
    plt.title('Top 3 Branch/Prefetcher Combinations by IPC for Each Trace', fontsize=16)
    
    for center, trace in group_centers:
        plt.text(
            center,
            top_ylim - trace_margin,
            trace,
            ha='center',
            va='top',
            fontsize=12,
            fontweight='bold',
            color='blue'
        )
    
    ax = plt.gca()
    for group in group_indices:
        left_index = group[0]
        right_index = group[-1]
        left_bound = x_positions[left_index] - bar_width * 0.5 - extra_spacing
        right_bound = x_positions[right_index] + bar_width * 0.5 + extra_spacing
        width = right_bound - left_bound
        rect = patches.Rectangle(
            (left_bound, 0),
            width,
            top_ylim,
            linewidth=1,
            edgecolor='black',
            facecolor='none',
            linestyle='--'
        )
        ax.add_patch(rect)
    
    plt.tight_layout()
    plt.show()


def plot_4ipc_by_trace(path):
    """
    Para cada trace:
      - Seleciona 4 IPC's:
          * O pior (menor IPC);
          * O melhor (maior IPC);
          * Dois intermediários (dos IPC's médios) escolhidos de modo que suas
            replacement policies sejam diferentes.
    Em seguida, todos os traces são plotados em um único gráfico,
    onde cada grupo (trace) é separado por um espaçamento e envolvido por um retângulo tracejado.
    
    As barras exibem o valor do IPC sobre elas, e a barra com o melhor IPC em cada trace é destacada (verde, negrito).
    
    Os rótulos do eixo x são formatados como "Branch | Prefetcher (Policy)" 
    (onde a formatação de "Branch | Prefetcher" é feita substituindo somente o primeiro underscore).
    """
    
    policies_set = set()
    for trace in data:
        for policy in data[trace]:
            policies_set.add(policy)
    policies_list = sorted(list(policies_set))
    
    grayscale_colors = ['#000000', '#555555', '#AAAAAA', '#FFFFFF']
    hatch_patterns = ['', '-', '++', 'xx']
    policy_styles = {}
    for i, policy in enumerate(policies_list):
        policy_styles[policy] = {
            'color': grayscale_colors[i % len(grayscale_colors)],
            'hatch': hatch_patterns[i % len(hatch_patterns)]
        }
    
    x_positions = []
    x_labels = []
    ipcs = []
    bar_policies = []
    group_centers = []
    group_indices = []
    offset = 0
    
    for trace in sorted(data.keys()):
        entradas = []
        for policy, bp_data in data[trace].items():
            for bp, ipc in bp_data.items():
                entradas.append((policy, bp, ipc))
                
        if len(entradas) < 4:
            continue
        
        entradas.sort(key=lambda x: x[2])
        pior = entradas[0]
        melhor = entradas[-1]
        intermediarios = entradas[1:-1]
        mediana = intermediarios[len(intermediarios)//2][2]
        intermediarios_ordenados = sorted(intermediarios, key=lambda x: abs(x[2] - mediana))
        
        candidatos = []
        policies_usadas = set()
        for candidato in intermediarios_ordenados:
            if candidato[0] not in policies_usadas:
                candidatos.append(candidato)
                policies_usadas.add(candidato[0])
            if len(candidatos) == 2:
                break
        
        if len(candidatos) < 2:
            continue
        
        entradas_final = [pior, candidatos[0], candidatos[1], melhor]
        entradas_final.sort(key=lambda x: x[2])
        
        group_start_index = len(x_positions)
        for policy, bp, ipc in entradas_final:
            bp_formatado = bp.replace('_', ' | ', 1)
            # Remove the policy portion from the label:
            label = bp_formatado
            x_positions.append(offset)
            x_labels.append(label)
            ipcs.append(ipc)
            bar_policies.append(policy)
            offset += 1
        group_end_index = len(x_positions) - 1
        center = (x_positions[group_start_index] + x_positions[group_end_index]) / 2.0
        group_centers.append((center, trace))
        group_indices.append(list(range(group_start_index, len(x_positions))))
        offset += 1
        
    plt.figure(figsize=(25, 11))
    
    barras = plt.bar(x_positions, ipcs, color='white', edgecolor='black')
    
    for i, barra in enumerate(barras):
        policy = bar_policies[i]
        estilo = policy_styles.get(policy, {'color': 'gray', 'hatch': ''})
        barra.set_facecolor(estilo['color'])
        barra.set_hatch(estilo['hatch'])
        barra.set_edgecolor('black')
    
    largura_barra = barras[0].get_width() if barras else 0.8
    extra_spacing = largura_barra / 4.0
    
    max_global = max(ipcs) if ipcs else 0
    top_ylim = max_global * 1.2 if max_global > 0 else 1
    plt.ylim(0, top_ylim)
    
    trace_margin = top_ylim * 0.06
    
    for grupo in group_indices:
        grupo_ipcs = [ipcs[i] for i in grupo]
        grupo_melhor = max(grupo_ipcs)
        for i in grupo:
            barra = barras[i]
            if ipcs[i] == grupo_melhor:
                cor_texto = 'green'
                peso_fonte = 'bold'
            else:
                cor_texto = 'black'
                peso_fonte = 'normal'
            plt.text(
                barra.get_x() + barra.get_width() / 2.0,
                barra.get_height(),
                f'{ipcs[i]:.2f}',
                ha='center',
                va='bottom',
                fontsize=14,
                color=cor_texto,
                fontweight=peso_fonte
            )
    
    plt.xticks(x_positions, x_labels, rotation=45, ha='right', fontsize=18)
    plt.xlabel('Branch | Prefetcher', fontsize=24)
    plt.ylabel('IPC', fontsize=24)
    plt.title('In each Trace: Worst, 2 Intermediate IPCs and Best', fontsize=24)
    
    ax = plt.gca()
    for center, trace in group_centers:
        plt.text(
            center,
            top_ylim - trace_margin,
            trace,
            ha='center',
            va='top',
            fontsize=24,
            fontweight='bold',
            color='blue'
        )
    
    for grupo in group_indices:
        left_index = grupo[0]
        right_index = grupo[-1]
        left_bound = x_positions[left_index] - largura_barra * 0.5 - extra_spacing
        right_bound = x_positions[right_index] + largura_barra * 0.5 + extra_spacing
        width = right_bound - left_bound
        rect = patches.Rectangle(
            (left_bound, 0),
            width,
            top_ylim,
            linewidth=1,
            edgecolor='black',
            facecolor='none',
            linestyle='--'
        )
        ax.add_patch(rect)
    
    plt.tight_layout()
    plt.savefig(path)
    plt.show()


#########################################################
#                 EXAMPLE USAGE                         #
#########################################################

# Example: If you want to call the function that plots top3 combos per trace:
group1 = {"BIPRP", "DRRIP", "FIFORP", "LRURP", "RandomRP", "SHiPMemRP"}
path = f"/mnt/c/Users/Raffael/Desktop/Results_Report/GEM5/Sample{Sample}/"

plot_selected_policies_by_trace_top3(group1, path)

# Or just call plot_everyone, plot_eachtrace, etc., as you like.
# plot_everyone()
# plot_10bestIPC()
