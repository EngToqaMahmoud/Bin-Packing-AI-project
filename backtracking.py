import time


def is_valid_placement(bins, item, bin_index, bin_capacity):
    """Check if an item can be placed in a specific bin."""
    return bins[bin_index] + item <= bin_capacity


def backtracking_solver(items, bin_capacity):
    """
    Solve the Bin Packing Problem using Backtracking.
    
    Args:
        items: list of item sizes
        bin_capacity: maximum capacity of each bin
    
    Returns:
        best_assignment: list where index = item, value = bin number
        num_bins: number of bins used
        time_taken: time in seconds
        iterations: number of iterations explored
    """

    n = len(items)
    best = {"assignment": None, "num_bins": float("inf")}
    iterations = [0]

    # Sort items in descending order for better pruning
    sorted_items = sorted(range(n), key=lambda i: items[i], reverse=True)
    sorted_sizes = [items[i] for i in sorted_items]

    def backtrack(item_index, bins, assignment, num_bins):
        iterations[0] += 1

        # All items have been placed
        if item_index == n:
            if num_bins < best["num_bins"]:
                best["num_bins"] = num_bins
                best["assignment"] = assignment[:]
            return

        # Pruning: no point continuing if we already use more bins than best
        if num_bins >= best["num_bins"]:
            return

        current_item = sorted_sizes[item_index]

        # Try placing the item in each existing bin
        for b in range(num_bins):
            if is_valid_placement(bins, current_item, b, bin_capacity):
                bins[b] += current_item
                assignment[item_index] = b
                backtrack(item_index + 1, bins, assignment, num_bins)
                bins[b] -= current_item
                assignment[item_index] = -1

        # Try opening a new bin
        if num_bins < n:
            bins[num_bins] += current_item
            assignment[item_index] = num_bins
            backtrack(item_index + 1, bins, assignment, num_bins + 1)
            bins[num_bins] -= current_item
            assignment[item_index] = -1

    start_time = time.time()

    bins = [0] * n
    assignment = [-1] * n
    backtrack(0, bins, assignment, 0)

    time_taken = round(time.time() - start_time, 4)

    # Map assignment back to original item order
    final_assignment = [-1] * n
    for sorted_index, original_index in enumerate(sorted_items):
        final_assignment[original_index] = best["assignment"][sorted_index]

    return final_assignment, best["num_bins"], time_taken, iterations[0]


def get_bins_content(items, assignment, num_bins):
    """
    Organize items into bins based on the assignment.
    
    Returns:
        bins_content: list of lists, each inner list has items in that bin
    """
    bins_content = [[] for _ in range(num_bins)]
    for item_index, bin_index in enumerate(assignment):
        bins_content[bin_index].append(items[item_index])
    return bins_content
