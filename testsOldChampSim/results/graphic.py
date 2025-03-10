import os
import re
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.patches as patches  # For drawing rectangles as limiters

# Define directories and file paths
Sample = '2'
trace_path = 'convolution'
input_dir = f'../sim_outputs/Sample{Sample}/'

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
            prefetcher_match = re.search(r"pre:(.*?)_output_DONE.txt", file_name)
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

def plot_eachtrace():
    for trace, policies in data.items():
        # Collect IPC values across all policies and branch prefetchers for this trace
        aggregated_data = {}
        for policy, branch_prefetchers in policies.items():
            for branch_prefetcher, ipc in branch_prefetchers.items():
                aggregated_data[f"{policy} | {branch_prefetcher}"] = ipc

        # Sort the aggregated data by IPC values
        sorted_items = sorted(aggregated_data.items(), key=lambda x: x[1])
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]

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

        plt.xlabel('Policy | Branch_Prefetcher', fontsize=14)
        plt.ylabel('IPC', fontsize=14)
        plt.title(f'Trace: {trace} - IPC Comparison', fontsize=16)
        plt.xticks(rotation=90, ha='right')
        plt.tight_layout()

        # Show the plot for this trace
        plt.show()

def plot_branch_prefetcher_across_policies():
    for trace, policies in data.items():
        # Organize data by Branch_Prefetcher
        branch_prefetchers = defaultdict(dict)
        
        for policy, branch_prefetcher_dict in policies.items():
            for branch_prefetcher, ipc in branch_prefetcher_dict.items():
                branch_prefetchers[branch_prefetcher][policy] = ipc
        
        # Create plots for each Branch_Prefetcher
        for branch_prefetcher, ipc_values in branch_prefetchers.items():
            policies = list(ipc_values.keys())
            values = list(ipc_values.values())
            
            # Sort policies by IPC values
            sorted_items = sorted(zip(policies, values), key=lambda x: x[1])
            sorted_policies = [item[0] for item in sorted_items]
            sorted_values = [item[1] for item in sorted_items]

            # Create the bar graph
            plt.figure(figsize=(14, 8))
            bars = plt.bar(sorted_policies, sorted_values, color=plt.cm.tab10.colors[:len(sorted_policies)])
            
            # Highlight the highest IPC in green
            max_value = max(sorted_values)
            for bar, value in zip(bars, sorted_values):
                color = 'green' if value == max_value else 'black'
                plt.text(
                    bar.get_x() + bar.get_width() / 2.0, value,
                    f'{value:.2f}',
                    ha='center', va='bottom', fontsize=10, color=color
                )

            plt.xlabel('Policy', fontsize=14)
            plt.ylabel('IPC', fontsize=14)
            plt.title(f'Trace: {trace} | Branch_Prefetcher: {branch_prefetcher}', fontsize=16)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Show the plot
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


def plot_selected_policies_by_trace(selected_policies,save_path):
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
        #cidx = i % len(colors)
        #hidx = i % len(hatches)
        #bar.set_facecolor(colors[cidx])
        #bar.set_hatch(hatches[hidx])
        #bar.set_edgecolor('black')
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
                    label = f"{policy} | {bp_formatted}"
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
            #policy = bar_policies[i]
            #facecolor, hatch = style_mapping.get(policy, ('#AAAAAA', ''))
            #bar.set_facecolor(facecolor)
            #bar.set_hatch(hatch)
            #bar.set_edgecolor('black')
            cidx = i % len(colors)
            hidx = i % len(hatches)
            bar.set_facecolor(colors[cidx])
            bar.set_hatch(hatches[hidx])
            bar.set_edgecolor('black')

        # -------------------------------------------------------------------
        # NEW LOGIC: Highlight local maximum *within each policy group*.
        # -------------------------------------------------------------------
        for (policy, start_idx, end_idx) in policy_boundaries:
            # Slice out the IPCs for this policy's bars
            group_ipcs = ipcs[start_idx:end_idx + 1]
            local_max = max(group_ipcs)

            # Label each bar, highlighting the group max in green/bold
            for i, bar_idx in enumerate(range(start_idx, end_idx + 1)):
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
        plt.xlabel('Policy | Branch | Prefetcher', fontsize=14)
        plt.ylabel('IPC', fontsize=14)
        plt.title(f"Trace: {trace}", fontsize=16, fontweight='normal')
        plt.ylim(0, new_ylim)

        # Draw vertical dotted lines between policy groups
        for i in range(len(policy_boundaries) - 1):
            current = policy_boundaries[i]
            next_group = policy_boundaries[i + 1]
            # Divider x = midpoint between last bar of current group & first bar of next group
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
        #final_filename = f"{save_path}_{trace}.png"
        #plt.savefig(final_filename)


        #plt.savefig(full_save_path)

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
                # Sort branch/prefetchers for this policy by IPC descending and take only top 5
                sorted_items = sorted(data[trace][policy].items(), key=lambda x: x[1], reverse=True)
                top_items = sorted_items[:4]
                for bp, ipc_val in top_items:
                    bp_formatted = bp.replace('_', ' | ', 1)
                    label = f"{policy} | {bp_formatted}"
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
            # Optionally, you can use the style mapping per policy:
            # policy = bar_policies[i]
            # facecolor, hatch = style_mapping.get(policy, ('#AAAAAA', ''))
            # bar.set_facecolor(facecolor)
            # bar.set_hatch(hatch)
            # bar.set_edgecolor('black')
            # Or use a simple cycling of colors/hatches:
            cidx = i % len(colors)
            hidx = i % len(hatches)
            bar.set_facecolor(colors[cidx])
            bar.set_hatch(hatches[hidx])
            bar.set_edgecolor('black')

        # -------------------------------------------------------------------
        # NEW LOGIC: Highlight local maximum *within each policy group*.
        # -------------------------------------------------------------------
        for (policy, start_idx, end_idx) in policy_boundaries:
            # Slice out the IPCs for this policy's bars
            group_ipcs = ipcs[start_idx:end_idx + 1]
            local_max = max(group_ipcs)
            # Label each bar, highlighting the group max in green/bold
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
        plt.xlabel('Policy | Branch | Prefetcher', fontsize=14)
        plt.ylabel('IPC', fontsize=14)
        plt.title(f"Trace: {trace}", fontsize=16, fontweight='normal')
        plt.ylim(0, new_ylim)

        # Draw vertical dotted lines between policy groups
        for i in range(len(policy_boundaries) - 1):
            current = policy_boundaries[i]
            next_group = policy_boundaries[i + 1]
            # Divider x = midpoint between last bar of current group & first bar of next group
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
        # If you want to save, you can add the trace to the file name here.
        final_filename = f"{save_path}_{trace}.png"
        plt.savefig(final_filename)
        #plt.show()


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
                # We require at least 3 entries to pick Worst, Intermediary and Best.
                if len(data[trace][policy]) < 3:
                    continue

                start_idx = len(ipcs)
                # Sort branch/prefetcher entries for this policy by IPC in ascending order.
                sorted_items = sorted(data[trace][policy].items(), key=lambda x: x[1])
                # Select Worst, Intermediary (median) and Best.
                worst = sorted_items[0]
                best = sorted_items[-1]
                intermediary = sorted_items[len(sorted_items) // 2]
                selected_items = [worst, intermediary, best]
                # (They are already in ascending order: worst -> intermediary -> best.)
                for bp, ipc_val in selected_items:
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

        # Skip if no data for this trace
        if not ipcs:
            continue

        # Compute the y-limit (plus margin at the top for policy labels)
        global_max = max(ipcs)
        top_ylim = global_max * 1.2 if global_max > 0 else 1
        top_margin = top_ylim * 0.2
        new_ylim = top_ylim + top_margin

        # Create a new figure for this trace
        plt.figure(figsize=(28, 11))
        bar_width = 0.8
        extra_spacing = bar_width / 4.0

        # Plot bars
        bars = plt.bar(x_positions, ipcs, width=bar_width, edgecolor='black')
        for i, bar in enumerate(bars):
            # Use the style mapping per policy.
            policy = bar_policies[i]
            facecolor, hatch = style_mapping.get(policy, ('#AAAAAA', ''))
            bar.set_facecolor(facecolor)
            bar.set_hatch(hatch)
            bar.set_edgecolor('black')

        # Highlight the Best (highest IPC) within each policy group.
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

        # X-axis labels and trace title.
        plt.xticks(x_positions, x_labels, rotation=45, ha='right', fontsize=19)
        plt.xlabel('Branch | Prefetcher', fontsize=24)
        plt.ylabel('IPC', fontsize=24)
        plt.title(f"Trace {trace}: Worst, Intermediate, and Best Case Analysis in each Cache Replacement", fontsize=24, fontweight='normal')
        plt.ylim(0, new_ylim)

        # Draw vertical dotted lines between policy groups.
        for i in range(len(policy_boundaries) - 1):
            current = policy_boundaries[i]
            next_group = policy_boundaries[i + 1]
            divider_x = (x_positions[current[2]] + x_positions[next_group[1]]) / 2.0
            plt.vlines(divider_x, 0, new_ylim, colors='black', linestyles='dotted', linewidth=1)

        # Annotate each policy name at the top of its group.
        for (policy, start_idx, end_idx) in policy_boundaries:
            seg_left = x_positions[start_idx] - bar_width * 0.5 - extra_spacing
            seg_right = x_positions[end_idx] + bar_width * 0.5 + extra_spacing
            seg_center = (seg_left + seg_right) / 2.0
            plt.text(seg_center, new_ylim - top_margin / 2,
                     policy, ha='center', va='top',
                     fontsize=24, fontweight='bold', color='blue')

        plt.tight_layout()
        # Construct the final filename with the trace name appended.
        final_filename = f"{save_path}_{trace}.png"
        # Uncomment the next line to save the figure instead of (or in addition to) showing it.
        plt.savefig(final_filename)
        #plt.show()


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
    # First, determine the set (and sorted list) of policies so we can assign each a consistent style.
    policies_set = set()
    for trace in data:
        for policy in data[trace]:
            policies_set.add(policy)
    policies_list = sorted(list(policies_set))
    
    # Define a mapping for policy styles (using grayscale and simple hatch patterns)
    grayscale_colors = ['#000000', '#555555', '#AAAAAA', '#FFFFFF']
    hatch_patterns = ['', '-', '++', 'xx']
    policy_styles = {}
    for i, policy in enumerate(policies_list):
        policy_styles[policy] = {
            'color': grayscale_colors[i % len(grayscale_colors)],
            'hatch': hatch_patterns[i % len(hatch_patterns)]
        }
    
    # Prepare lists that will hold the data for plotting all bars
    x_positions = []      # x position of each bar
    x_labels = []         # labels (will show "Branch | Prefetcher (Policy)")
    ipcs = []             # IPC value for each bar
    bar_policies = []     # the policy associated with each bar (for styling)
    group_centers = []    # (center, trace) for each trace group (used to put the trace name)
    group_indices = []    # list of lists, each containing indices of bars belonging to a trace group
    offset = 0            # running x position counter

    # Process each trace (group) in sorted order
    for trace in sorted(data.keys()):
        bars_in_trace = []
        # For each policy in the trace, add its branch/prefetcher entries
        for policy, bp_data in data[trace].items():
            for bp, ipc in bp_data.items():
                bars_in_trace.append((policy, bp, ipc))
        
        if not bars_in_trace:
            continue
        
        # Sort all bars in this trace by IPC in descending order and take the top 3.
        bars_in_trace.sort(key=lambda x: x[2], reverse=True)
        top_bars = bars_in_trace[:3]
        
        # Record indices for this trace’s bars
        group_start_index = len(x_positions)
        for policy, bp, ipc in top_bars:
            # Format the branch/prefetcher label: replace the first underscore with " | "
            bp_formatted = bp.replace('_', ' | ', 1)
            # Also include the policy in the label so that it is clear which result came from which policy.
            label = f'{bp_formatted}\n({policy})'
            x_positions.append(offset)
            x_labels.append(label)
            ipcs.append(ipc)
            bar_policies.append(policy)
            offset += 1
        group_end_index = len(x_positions) - 1
        # Compute the group center (using the x positions of the first and last bar in the group)
        group_center = (x_positions[group_start_index] + x_positions[group_end_index]) / 2.0
        group_centers.append((group_center, trace))
        group_indices.append(list(range(group_start_index, len(x_positions))))
        # Add extra spacing between trace groups
        offset += 1

    # Create the figure
    plt.figure(figsize=(14, 8))
    
    # Plot bars with a default white fill and black edges.
    bars = plt.bar(x_positions, ipcs, color='white', edgecolor='black')
    
    # Now update each bar’s appearance based on its associated policy.
    for i, bar in enumerate(bars):
        policy = bar_policies[i]
        style = policy_styles.get(policy, {'color': 'gray', 'hatch': ''})
        bar.set_facecolor(style['color'])
        bar.set_hatch(style['hatch'])
        bar.set_edgecolor('black')
    
    # Get the default bar width (default is 0.8)
    bar_width = bars[0].get_width() if bars else 0.8
    extra_spacing = bar_width / 4.0  # extra margin for the dashed rectangles
    
    # Set y-axis limit: 20% above the highest IPC value.
    global_max = max(ipcs) if ipcs else 0
    top_ylim = global_max * 1.2 if global_max > 0 else 1
    plt.ylim(0, top_ylim)
    
    # A margin from the top for writing the trace name
    trace_margin = top_ylim * 0.06
    
    # For each trace group, annotate each bar with its IPC value.
    # Highlight the highest value in each group (green and bold).
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
    
    # Set x-axis labels with a 45° rotation for readability.
    plt.xticks(x_positions, x_labels, rotation=45, ha='right', fontsize=10)
    plt.xlabel('Branch | Prefetcher (Policy)', fontsize=14)
    plt.ylabel('IPC', fontsize=14)
    plt.title('Top 3 Branch/Prefetcher Combinations by IPC for Each Trace', fontsize=16)
    
    # Write each trace name near the top of its group.
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
    
    # Draw dashed rectangles around each trace group.
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
    
    # Determinar o conjunto de policies e associar estilos (cor e hatch) para cada uma
    policies_set = set()
    for trace in data:
        for policy in data[trace]:
            policies_set.add(policy)
    policies_list = sorted(list(policies_set))
    
    # Paleta de cores em tons de cinza e hatch patterns simples
    grayscale_colors = ['#000000', '#555555', '#AAAAAA', '#FFFFFF']
    hatch_patterns = ['', '-', '++', 'xx']
    policy_styles = {}
    for i, policy in enumerate(policies_list):
        policy_styles[policy] = {
            'color': grayscale_colors[i % len(grayscale_colors)],
            'hatch': hatch_patterns[i % len(hatch_patterns)]
        }
    
    # Listas para acumular os dados de todas as barras
    x_positions = []      # posição x de cada barra
    x_labels = []         # rótulo de cada barra (formato "Branch | Prefetcher (Policy)")
    ipcs = []             # valor do IPC de cada barra
    bar_policies = []     # policy associada a cada barra (para estilo)
    group_centers = []    # (centro, trace) para cada grupo, para posicionar o nome do trace
    group_indices = []    # lista de índices de barras que pertencem a cada trace
    offset = 0            # contador de posição x
    
    # Processa cada trace (em ordem alfabética)
    for trace in sorted(data.keys()):
        # Agregar todas as entradas do trace: cada entrada é (policy, branch_prefetcher, ipc)
        entradas = []
        for policy, bp_data in data[trace].items():
            for bp, ipc in bp_data.items():
                entradas.append((policy, bp, ipc))
                
        # Se não houver pelo menos 4 entradas, pule este trace
        if len(entradas) < 4:
            continue
        
        # Ordena as entradas pelo IPC (do menor para o maior)
        entradas.sort(key=lambda x: x[2])
        
        # Seleciona o pior (primeiro) e o melhor (último)
        pior = entradas[0]
        melhor = entradas[-1]
        
        # Seleciona os candidatos intermediários (excluindo pior e melhor)
        intermediarios = entradas[1:-1]
        
        # Calcula um valor mediano (usando o IPC do elemento central dos intermediários)
        mediana = intermediarios[len(intermediarios)//2][2]
        # Ordena os intermediários pela distância em módulo do valor mediano
        intermediarios_ordenados = sorted(intermediarios, key=lambda x: abs(x[2] - mediana))
        
        # Seleciona dois candidatos intermediários com policies diferentes
        candidatos = []
        policies_usadas = set()
        for candidato in intermediarios_ordenados:
            if candidato[0] not in policies_usadas:
                candidatos.append(candidato)
                policies_usadas.add(candidato[0])
            if len(candidatos) == 2:
                break
        
        # Se não foram encontrados dois candidatos com policies diferentes, pula o trace
        if len(candidatos) < 2:
            continue
        
        # Agrupa as 4 entradas: pior, os 2 candidatos e o melhor
        entradas_final = [pior, candidatos[0], candidatos[1], melhor]
        # Ordena as 4 entradas em ordem crescente de IPC para melhor visualização
        entradas_final.sort(key=lambda x: x[2])
        
        # Registra as entradas deste trace
        group_start_index = len(x_positions)
        for policy, bp, ipc in entradas_final:
            # Formata o rótulo: substitui apenas o primeiro underscore por " | "
            bp_formatado = bp.replace('_', ' | ', 1)
            label = f'{bp_formatado} | {policy}'
            x_positions.append(offset)
            x_labels.append(label)
            ipcs.append(ipc)
            bar_policies.append(policy)
            offset += 1
        group_end_index = len(x_positions) - 1
        center = (x_positions[group_start_index] + x_positions[group_end_index]) / 2.0
        group_centers.append((center, trace))
        group_indices.append(list(range(group_start_index, len(x_positions))))
        # Espaçamento extra entre os grupos
        offset += 1
        
    # Cria a figura
    plt.figure(figsize=(25, 11))
    
    # Plota as barras inicialmente com preenchimento branco e borda preta
    barras = plt.bar(x_positions, ipcs, color='white', edgecolor='black')
    
    # Ajusta o estilo de cada barra de acordo com sua policy
    for i, barra in enumerate(barras):
        policy = bar_policies[i]
        estilo = policy_styles.get(policy, {'color': 'gray', 'hatch': ''})
        barra.set_facecolor(estilo['color'])
        barra.set_hatch(estilo['hatch'])
        barra.set_edgecolor('black')
    
    # Determina a largura da barra (padrão é 0.8)
    largura_barra = barras[0].get_width() if barras else 0.8
    extra_spacing = largura_barra / 4.0
    
    # Ajusta o limite do eixo y (20% acima do maior valor)
    max_global = max(ipcs) if ipcs else 0
    top_ylim = max_global * 1.2 if max_global > 0 else 1
    plt.ylim(0, top_ylim)
    
    # Margem para posicionar o nome do trace na parte superior
    trace_margin = top_ylim * 0.06
    
    # Para cada grupo (trace), anota o valor do IPC sobre cada barra e destaca o melhor (verde, negrito)
    for grupo in group_indices:
        # O melhor é a barra com maior IPC neste grupo
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
    
    # Configura os rótulos do eixo x
    plt.xticks(x_positions, x_labels, rotation=45, ha='right', fontsize=18)
    plt.xlabel('Branch | Prefetcher | Policy', fontsize=24)
    plt.ylabel('IPC', fontsize=24)
    plt.title('In each Trace: Worst, 2 Intermediate IPCs and Best', fontsize=24)
    
    ax = plt.gca()
    # Posiciona o nome de cada trace na parte superior de seu grupo
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
    
    # Desenha retângulos tracejados ao redor de cada grupo (trace)
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
    
    # Construct the final filename with the trace name appended
    #final_filename = f"{path}_{trace}.png"
    plt.savefig(path)
    
    plt.show()



group1 = {
                "bip",
                "hawkeye",
                "fifo",
                "emissary",
                "pcn",
                "rlr",
                "drrip",
                "lru",
                "ship",
                "mockingjay",
                "random"
}

algos = "_".join(sorted(group1))      
path = f"/mnt/c/Users/Raffael/Desktop/Results_Report/Champsim/Sample{Sample}/{trace_path}"

#plot_selected_policies_by_trace_top3(group1,path)

'''
# Group 2: policies "lru", "fifo", "random", "bip drrip", "ship"
group2 = {"lru", "fifo", "random", "bip", "drrip", "ship"}
algos = "_".join(sorted(group2))      
path = f"/mnt/c/Users/Raffael/Desktop/ChampSim_Outputs/CHAMPSIM_{trace_path}/Sample{Sample}/{algos}"
plot_selected_policies_by_trace(group2,path)

# Group 3: All remaining policies (those not in group2)
all_policies = set()
for trace, policies in data.items():
    for pol in policies.keys():
        all_policies.add(pol)
group3 = all_policies - group2  # subtracting the policies already plotted in group 2
algos = "_".join(sorted(group3))   
path = f"/mnt/c/Users/Raffael/Desktop/ChampSim_Outputs/CHAMPSIM_{trace_path}/Sample{Sample}/{algos}"   
plot_selected_policies_by_trace(group3,path)
'''
#plot_policy_group_by_trace()

path = f"/mnt/c/Users/Raffael/Desktop/Results_Report/Champsim/Sample{Sample}/{trace_path}"
#plot_4ipc_by_trace(path)
# Call the function to generate the plots
#plot_branch_prefetcher_across_policies()

#plot_eachtrace()
plot_everyone()
#plot_10bestIPC()