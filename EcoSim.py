import random
import time

import config

# Ecosystem variables
args = config.get_args()
grid_width = args.width
grid_height = args.height
total_ticks = args.ticks
render_every = args.render_every
seed = args.seed
regrow_rate = args.regrow
total_rabbits = args.rabbits
RNG = random.Random(seed)


def init_grid(width, height) -> list[list[int]]:
    """
    Grid generation for simulation
    :param width: width of grid
    :param height: height of grid
    :return: list of lists of ints that store each tile's data
    """
    return [[0 for _ in range(width)] for _ in range(height)]


def place_rabbits(width, height, n, rng) -> list[tuple[int, int]]:
    """
    Random placement of rabbits on the grid
    :param width: width of grid
    :param height: height of grid
    :param n: number of rabbits to place
    :param rng: RNG for random placements
    :return: list of tuples of ints made of rabbit coordinates
    """
    cells = [(x, y) for y in range(height) for x in range(width)]
    return rng.sample(cells, n)  # distinct positions


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


def decide_moves(rabbits, width, height, rng) -> list[tuple[int, int]]:
    """
    For each rabbit, propose target by adding one of [(1,0),(-1,0),(0,1),(0,-1)]. If target is OOB, use current pos (stay).
    :param rabbits: list of rabbit coordinates
    :param width: width of grid
    :param height: height of grid
    :param rng: RNG for random movements
    :return targets: list of targeted coordinates for rabbits to move
    """
    targets = []
    for coord in rabbits:
        direction_to_move = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        # check if new position is within grid bounds and if not then remain in same position
        if 0 <= coord[0] + direction_to_move[0] < width and 0 <= coord[1] + direction_to_move[1] < height:
            targets.append((coord[0] + direction_to_move[0], coord[1] + direction_to_move[1]))
        else:
            targets.append(coord)
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


def eat_cells(grid, rabbits, regrow) -> set[tuple[int, int]]:
    """
    Eats up a cell's grass for all the rabbits and sets the regrow timer for the grass on the cell.
    :param grid: simulation grid
    :param rabbits: list of rabbit's positions
    :param regrow: growth time to be set on eaten tiles
    :return: set of tuples of coordinates that have been eaten recently
    """
    newly_eaten = set()
    for rabbit_pos in rabbits:
        if grid[rabbit_pos[1]][rabbit_pos[0]] == 0:
            grid[rabbit_pos[1]][rabbit_pos[0]] = regrow
            newly_eaten.add(rabbit_pos)
    return newly_eaten


def regrow_step(grid, newly_eaten) -> None:
    """
    Decrements the timer of every tile on grid by 1, clamped to 0.
    :param grid: simulation grid.
    :param newly_eaten: List of tiles to skip the growth.
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


# Simulation start here

render_counter = 0
sim_ticks = 0
sum_coverage = 0
grid = init_grid(grid_width, grid_height)
list_of_rabbits = place_rabbits(grid_width, grid_height, total_rabbits, RNG)

while sim_ticks < total_ticks:

    # Print status of simulation whenever render_counter hits 0.
    g = grass_count(grid)
    if render_counter == 0:
        print(f"tick={sim_ticks} rabbits={len(list_of_rabbits)} grass={g}/{grid_width * grid_height}")
        render_counter = render_every
    sum_coverage += g / (grid_width * grid_height)

    # Make every rabbit move in a random direction using move_rabbit()
    next_moves = decide_moves(list_of_rabbits, grid_width, grid_height, RNG)
    apply_moves(list_of_rabbits, next_moves)

    # after movement, rabbits can eat grass
    recently_eaten = eat_cells(grid, list_of_rabbits, regrow_rate)
    regrow_step(grid, recently_eaten)

    # Update tick and render counter
    sim_ticks += 1
    render_counter -= 1
    time.sleep(1 / 20)

# Post-simulation summary
print(f"done: ticks={total_ticks} average_grass_coverage = {round(sum_coverage / total_ticks, 2)}")
