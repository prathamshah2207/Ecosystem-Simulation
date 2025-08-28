import random
import config
import tui

# Ecosystem variables
args = config.get_args()
grid_width = args.width
grid_height = args.height
total_ticks = args.ticks
render_every = args.render_every
seed = args.seed
regrow_rate = args.regrow

# Rabbit's args
initial_rabbits = args.rabbits
starting_energy = args.energy_start
move_cost = args.move_cost
idle_cost = args.idle_cost
eating_gains = args.eat_gain
reproduction_threshold = args.repro_threshold
reproduction_cost = args.repro_cost
initial_energy = args.infant_energy if args.infant_energy else reproduction_cost

RNG = random.Random(seed)


def init_grid(width, height) -> list[list[int]]:
    """
    Grid generation for simulation
    :param width: width of grid
    :param height: height of grid
    :return: list of lists of ints that store each tile's data
    """
    return [[0 for _ in range(width)] for _ in range(height)]


def place_rabbits(width, height, n, rng, energy) -> list[tuple[int, int]]:
    """
    Random placement of rabbits on the grid
    :param width: width of grid
    :param height: height of grid
    :param n: number of rabbits to place
    :param rng: RNG for random placements
    :param energy: initial energy of all rabbits
    :return: list of tuples of ints made of rabbit coordinates
    """
    cells = [(x, y, energy) for y in range(height) for x in range(width)]
    rabbits = rng.sample(cells, n)
    return rabbits


def grass_count(grid) -> int:
    """
    Counts the total number of cells which has grass on them.
    :param grid: generation grid
    :return: number of grassy cells in the grid
    """
    grasses = 0
    for row in grid:
        for cell in row:
            if cell == 0:
                grasses += 1
    return grasses


def decide_moves(rabbits, width, height, rng, move_cst, idle_cst) -> list[tuple[int, int, int]]:
    """
    For each rabbit, propose target by adding one of [(1,0),(-1,0),(0,1),(0,-1)]. If target is OOB, use current pos (stay).
    :param rabbits: list of rabbit coordinates
    :param width: width of grid
    :param height: height of grid
    :param rng: RNG for random movements
    :param move_cst: cost of energy to potentially move rabbit
    :param idle_cst: cost of energy to potentially stay idle
    :return targets: list of targeted coordinates for rabbits to move
    """
    targets = []
    for coord in rabbits:
        direction_to_move = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        # check if new position is within grid bounds and if not then remain in same position
        if 0 <= coord[0] + direction_to_move[0] < width and 0 <= coord[1] + direction_to_move[1] < height:
            targets.append((coord[0] + direction_to_move[0], coord[1] + direction_to_move[1], coord[2] - move_cst))
        else:
            targets.append((coord[0], coord[1], coord[2] - idle_cst))
    return targets


def apply_moves(rabbits, targets) -> None:
    """
    Overwrite each rabbit’s position with its target.
    :param rabbits: list of rabbit's current position
    :param targets: list of target positions
    :return: None
    """
    for index in range(len(rabbits)):
        rabbits[index] = targets[index]


def eat_cells(grid, rabbits, regrow, energy_gain) -> set[tuple[int, int]]:
    """
    Eats up a cell's grass for all the rabbits and sets the regrow timer for the grass on the cell.
    :param grid: simulation grid
    :param rabbits: list of rabbit's positions
    :param regrow: growth time to be set on eaten tiles
    :param energy_gain: energy to gain after eating grass
    :return: set of tuples of coordinates that have been eaten recently
    """
    newly_eaten = set()
    for index in range(len(rabbits)):
        if grid[rabbits[index][1]][rabbits[index][0]] == 0:
            grid[rabbits[index][1]][rabbits[index][0]] = regrow  # Set new timer for grass to grow again
            rabbits[index] = (rabbits[index][0], rabbits[index][1],
                              rabbits[index][2] + energy_gain)  # Give energy gains to rabbits who have eaten grass
            newly_eaten.add(
                (rabbits[index][0], rabbits[index][1]))  # Save the newly eaten position on grid for later use
    return newly_eaten


def regrow_step(grid, newly_eaten) -> None:
    """
    Decrements the timer of every tile on grid by 1, clamped to 0.
    :param grid: simulation grid.
    :param newly_eaten: Set of tiles to skip the growth.
    :return: None
    """
    H = len(grid)
    W = len(grid[0]) if H else 0
    for i in range(H):
        for j in range(W):
            if (j, i) in newly_eaten:
                continue  # don't decrement the cell we just set to G this tick
            if grid[i][j] > 0:
                grid[i][j] -= 1


def reproduce(rabbits, rng, width, height, threshold, cost, spawn_energy) -> list:
    """
    takes all rabbits and makes it reproduce by cutting some energy and spawning a new rabbit in grid near parent of the rabbit has the reproduction threshold
    :param rabbits: list of rabbits
    :param rng: RNG for randomness
    :param width: width of grid
    :param height: height of grid
    :param threshold: reproduction threshold
    :param cost: reproduction cost of parent
    :param spawn_energy: initial energy of the spawned infant
    :return newly_born: list of newly born rabbits
    """
    spawnable_directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    newly_born = []

    for index in range(len(rabbits)):
        if rabbits[index][2] >= threshold:
            for direction in rng.sample(spawnable_directions, 4):  # goes through all direction for spawnable conditions
                if 0 <= rabbits[index][0] + direction[0] < width and 0 <= rabbits[index][1] + direction[1] < height:
                    spawned_infant = (rabbits[index][0] + direction[0], rabbits[index][1] + direction[1],
                                      spawn_energy)  # spawn one if a direction is valid for spawning
                    rabbits[index] = (rabbits[index][0], rabbits[index][1], rabbits[index][2] - cost)
                    newly_born.append(spawned_infant)
                    break
            else:  # If no adjacent tile is possible to spawn then spawn it on parent's tile
                spawned_infant = (rabbits[index][0], rabbits[index][1],
                                  spawn_energy)  # spawn infant at parent's position if no direction is spawnable
                rabbits[index] = (rabbits[index][0], rabbits[index][1], rabbits[index][2] - cost)
                newly_born.append(spawned_infant)

    return newly_born


def remove_dead_bodies(rabbits) -> None:
    """
    Remove rabbits from grid whose energy levels have reached 0 and so are dead.
    :param rabbits: List of rabbits.
    :return: None
    """
    rabbits[:] = [r for r in rabbits if r[2] > 0]


# Simulation start here
def run_headless():
    """
    Main simulation displayed as reports-only in output.
    :return: None
    """
    render_counter = 0
    sim_ticks = 0
    sum_coverage = 0.0
    min_cov = 1.0
    max_cov = 0.0
    total_cells = grid_width * grid_height
    grid = init_grid(grid_width, grid_height)
    list_of_rabbits = place_rabbits(grid_width, grid_height, initial_rabbits, RNG, starting_energy)

    while sim_ticks < total_ticks:

        # Print status of simulation whenever render_counter hits 0.
        g = grass_count(grid)
        cov = g / total_cells
        sum_coverage += g / total_cells
        min_cov = min(min_cov, cov)
        max_cov = max(max_cov, cov)
        if render_counter == 0:
            print(
                f"tick={sim_ticks} rabbits={len(list_of_rabbits)} grass={g}/{grid_width * grid_height} coverage={(cov * 100):.1f}%")
            render_counter = render_every

        # Make every rabbit move in a random direction using move_rabbit()
        next_moves = decide_moves(list_of_rabbits, grid_width, grid_height, RNG, move_cost, idle_cost)
        apply_moves(list_of_rabbits, next_moves)

        # after movement, rabbits can eat grass
        recently_eaten = eat_cells(grid, list_of_rabbits, regrow_rate, eating_gains)
        regrow_step(grid, recently_eaten)

        # Rabbits can now reproduce if they meet the energy requirement
        new_born = reproduce(list_of_rabbits, RNG, grid_width, grid_height, reproduction_threshold, reproduction_cost,
                             initial_energy)
        list_of_rabbits += new_born

        # clear any dead rabbits whose energy level reaches 0
        remove_dead_bodies(list_of_rabbits)

        # Update tick and render counter
        sim_ticks += 1
        render_counter -= 1
        # time.sleep(1 / 20)

    # Post-simulation summary
    print(
        f"done: ticks={total_ticks} average_grass_coverage = {((sum_coverage / total_ticks) * 100):.1f}% min = {(min_cov * 100):.1f}% max = {(max_cov * 100):.1f}%")


def run_curses():
    grid = init_grid(grid_width, grid_height)
    rabbits = place_rabbits(grid_width, grid_height, initial_rabbits, RNG, starting_energy)
    sim_ticks = 0
    sum_coverage = 0.0
    min_cov = 1.0
    max_cov = 0.0
    total_cells = grid_width * grid_height

    def step_fn():
        nonlocal sim_ticks, sum_coverage, min_cov, max_cov, grid, rabbits
        if sim_ticks < total_ticks:
            next_moves = decide_moves(rabbits, grid_width, grid_height, RNG, move_cost, idle_cost)
            apply_moves(rabbits, next_moves)
            newly = eat_cells(grid, rabbits, regrow_rate, eating_gains)
            regrow_step(grid, newly)
            new_born = reproduce(rabbits, RNG, grid_width, grid_height, reproduction_threshold,
                                 reproduction_cost,
                                 initial_energy)
            rabbits += new_born
            remove_dead_bodies(rabbits)

            g = grass_count(grid)
            cov = g / total_cells
            sum_coverage += cov
            if cov < min_cov: min_cov = cov
            if cov > max_cov: max_cov = cov
            sim_ticks += 1
        return sim_ticks, grid, rabbits

    tui.run_curses_loop(args, step_fn, init_state=(grid, rabbits))
    # After curses exits, print the same summary as headless
    print(
        f"done: ticks={total_ticks} avg={sum_coverage / total_ticks * 100:.1f}% min={(min_cov * 100):.1f}% max={(max_cov * 100):.1f}%")


if args.ui == "curses":
    run_curses()
else:
    run_headless()
