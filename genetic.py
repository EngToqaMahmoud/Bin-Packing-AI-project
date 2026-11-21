import random
import time


# ── GA Parameters ──────────────────────────────────────────────
POPULATION_SIZE = 100
GENERATIONS     = 200
MUTATION_RATE   = 0.1
CROSSOVER_RATE  = 0.8
TOURNAMENT_SIZE = 5


# ── Chromosome Representation ──────────────────────────────────
# A chromosome is a list of length n (number of items).
# Each gene is a bin index (0 to n-1) representing which bin that item goes to.
# Example: [0, 1, 0, 2, 1] means item 0 -> bin 0, item 1 -> bin 1, etc.


def is_valid_chromosome(chromosome, items, bin_capacity):
    """Check that no bin exceeds capacity in this chromosome."""
    bin_loads = {}
    for item_index, bin_index in enumerate(chromosome):
        bin_loads[bin_index] = bin_loads.get(bin_index, 0) + items[item_index]
        if bin_loads[bin_index] > bin_capacity:
            return False
    return True


def repair_chromosome(chromosome, items, bin_capacity):
    """
    Fix a chromosome that violates bin capacity constraints.
    Overflowing items are moved to a new bin.
    """
    bin_loads = {}
    repaired = chromosome[:]

    for item_index, bin_index in enumerate(repaired):
        bin_loads[bin_index] = bin_loads.get(bin_index, 0) + items[item_index]
        if bin_loads[bin_index] > bin_capacity:
            # Move item to a new bin
            bin_loads[bin_index] -= items[item_index]
            new_bin = max(bin_loads.keys()) + 1
            repaired[item_index] = new_bin
            bin_loads[new_bin] = items[item_index]

    return repaired


def fitness(chromosome, items, bin_capacity):
    """
    Fitness function: fewer bins = better.
    Returns a score where higher is better.
    Also penalises invalid chromosomes.
    """
    if not is_valid_chromosome(chromosome, items, bin_capacity):
        return 0  # Invalid solution gets worst score

    num_bins = len(set(chromosome))

    # Bonus: reward bins that are well filled (reduces wasted space)
    bin_loads = {}
    for item_index, bin_index in enumerate(chromosome):
        bin_loads[bin_index] = bin_loads.get(bin_index, 0) + items[item_index]

    fill_ratio = sum(bin_loads.values()) / (num_bins * bin_capacity)

    # Lower bins = higher fitness, fill ratio breaks ties
    return (1 / num_bins) + (0.1 * fill_ratio)


def normalize_chromosome(chromosome):
    """
    Rename bin indices to be consecutive starting from 0.
    e.g. [0, 3, 3, 7] -> [0, 1, 1, 2]
    This keeps bin numbering clean.
    """
    mapping = {}
    counter = 0
    result = []
    for gene in chromosome:
        if gene not in mapping:
            mapping[gene] = counter
            counter += 1
        result.append(mapping[gene])
    return result


# ── Population Initialization ──────────────────────────────────

def create_individual(items, bin_capacity):
    """
    Create one valid random chromosome using a greedy random approach.
    Each item is randomly assigned to a bin that still has room.
    """
    n = len(items)
    chromosome = [-1] * n
    bin_loads = {}

    # Shuffle item order for randomness
    order = list(range(n))
    random.shuffle(order)

    for item_index in order:
        item_size = items[item_index]
        placed = False

        # Try a random existing bin first
        existing_bins = list(bin_loads.keys())
        random.shuffle(existing_bins)

        for b in existing_bins:
            if bin_loads[b] + item_size <= bin_capacity:
                chromosome[item_index] = b
                bin_loads[b] += item_size
                placed = True
                break

        if not placed:
            new_bin = len(bin_loads)
            chromosome[item_index] = new_bin
            bin_loads[new_bin] = item_size

    return chromosome


def create_population(items, bin_capacity):
    """Create the initial population of chromosomes."""
    return [create_individual(items, bin_capacity) for _ in range(POPULATION_SIZE)]


# ── Selection ──────────────────────────────────────────────────

def tournament_selection(population, items, bin_capacity):
    """
    Pick the best individual out of a random tournament group.
    Simple and effective selection method.
    """
    tournament = random.sample(population, TOURNAMENT_SIZE)
    return max(tournament, key=lambda c: fitness(c, items, bin_capacity))


# ── Crossover ──────────────────────────────────────────────────

def crossover(parent1, parent2, items, bin_capacity):
    """
    Single-point crossover.
    Split both parents at a random point and combine their halves.
    Repair the offspring if constraints are violated.
    """
    if random.random() > CROSSOVER_RATE:
        return parent1[:], parent2[:]

    point = random.randint(1, len(parent1) - 1)

    child1 = parent1[:point] + parent2[point:]
    child2 = parent2[:point] + parent1[point:]

    # Repair if invalid
    child1 = repair_chromosome(child1, items, bin_capacity)
    child2 = repair_chromosome(child2, items, bin_capacity)

    return child1, child2


# ── Mutation ───────────────────────────────────────────────────

def mutate(chromosome, items, bin_capacity):
    """
    Randomly move an item to a different bin.
    Either an existing bin with room, or a new bin.
    """
    mutated = chromosome[:]

    for item_index in range(len(mutated)):
        if random.random() < MUTATION_RATE:
            item_size = items[item_index]

            # Calculate current bin loads excluding this item
            bin_loads = {}
            for i, b in enumerate(mutated):
                if i != item_index:
                    bin_loads[b] = bin_loads.get(b, 0) + items[i]

            # Find bins that can fit this item
            valid_bins = [b for b, load in bin_loads.items()
                          if load + item_size <= bin_capacity]

            if valid_bins:
                mutated[item_index] = random.choice(valid_bins)
            else:
                # Open a new bin
                mutated[item_index] = max(bin_loads.keys(), default=-1) + 1

    return mutated


# ── Main GA Loop ───────────────────────────────────────────────

def genetic_solver(items, bin_capacity):
    """
    Solve the Bin Packing Problem using a Genetic Algorithm.

    Args:
        items: list of item sizes
        bin_capacity: maximum capacity of each bin

    Returns:
        best_assignment: list where index = item, value = bin number
        num_bins: number of bins used
        time_taken: time in seconds
        best_fitness_per_gen: fitness score per generation (for plotting)
    """
    start_time = time.time()

    population = create_population(items, bin_capacity)
    best_individual = max(population, key=lambda c: fitness(c, items, bin_capacity))
    best_fitness_per_gen = []

    for generation in range(GENERATIONS):
        new_population = []

        # Elitism: carry the best individual directly to next generation
        new_population.append(best_individual[:])

        while len(new_population) < POPULATION_SIZE:
            parent1 = tournament_selection(population, items, bin_capacity)
            parent2 = tournament_selection(population, items, bin_capacity)

            child1, child2 = crossover(parent1, parent2, items, bin_capacity)
            child1 = mutate(child1, items, bin_capacity)
            child2 = mutate(child2, items, bin_capacity)

            new_population.append(child1)
            if len(new_population) < POPULATION_SIZE:
                new_population.append(child2)

        population = new_population

        # Track best this generation
        current_best = max(population, key=lambda c: fitness(c, items, bin_capacity))
        if fitness(current_best, items, bin_capacity) > fitness(best_individual, items, bin_capacity):
            best_individual = current_best[:]

        best_fitness_per_gen.append(len(set(best_individual)))

    time_taken = round(time.time() - start_time, 4)

    best_individual = normalize_chromosome(best_individual)
    num_bins = len(set(best_individual))

    return best_individual, num_bins, time_taken, best_fitness_per_gen


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
