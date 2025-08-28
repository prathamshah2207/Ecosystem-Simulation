import random
import config
import tui

# Ecosystem variables
args = config.get_args()
grid_width = args.width
grid_height = args.height
tile_capacity = args.capacity
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
initial_energy = reproduction_cost if args.infant_energy is None else args.infant_energy

RNG = random.Random(seed)


def init_grid(width, height, cell_cap) -> list[list[list[int, int]]]:
    """
    Grid generation for simulation
    :param width: width of grid
    :param height: height of grid
    :param cell_cap: entity holding capacity
    :return: list that store each tile's data [grass growth level, entity holding capacity]
    """
    return [[[0, cell_cap] for _ in range(width)] for _ in range(height)]


def place_rabbits(grid, n, rng, energy) -> list[list[int, int, int]]:
    """
    Random placement of rabbits on the grid
    :param grid: simulation grid
    :param n: number of rabbits to place
    :param rng: RNG for random placements
    :param energy: initial energy of all rabbits
    :return: list rabbits with their spawning coordinates and initial energy
    """
    cells = [[x, y, energy] for y in range(len(grid)) for x in range(len(grid[0]))]
    rabbits = rng.sample(cells, n)
    for rabbit in rabbits:
        grid[rabbit[1]][rabbit[0]][1] -= 1
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
            if cell[0] == 0:
                grasses += 1
    return grasses


def decide_moves(width, height, rabbits, rng) -> list:
    """
    For each rabbit, propose target by adding one of [(1,0),(-1,0),(0,1),(0,-1)]. If target is OOB(Out of Bounds), use current pos (stay).
    :param rabbits: list of rabbit coordinates
    :param width: width of grid
    :param height: height of grid
    :param rng: RNG for random movements
    :return decisions: list of targeted coordinates for rabbits to move/stay
    """
    decisions = []

    for rabbit in rabbits:
        direction_to_move = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        potential_tile = [rabbit[0] + direction_to_move[0], rabbit[1] + direction_to_move[1]]

        # check if new position is within grid bounds
        if 0 <= potential_tile[0] < width and 0 <= potential_tile[1] < height:
            decisions.append([potential_tile[0], potential_tile[1]])
        else:  # if not then remain in same position
            decisions.append(rabbit[0:2])

    return decisions


def resolve_moves_lottery(rabbits, proposals, tile_cap, rng):
    """

    :param rabbits: list of rabbits
    :param proposals: list of targeted positions proposed by rabbits to move
    :param tile_cap: entity capacity for a tile
    :param rng: RNG randomness generator
    :return final_moves: list of final moves for all rabbits
    """
    target_dictionary = {}
    rabbit_positions = [[x, y] for x, y, _ in rabbits]
    final_moves = rabbit_positions.copy()

    for i in range(len(proposals)):
        target_dictionary[i] = proposals[i]
    target_dictionary_copy = target_dictionary.copy()

    for key, value in target_dictionary.items():
        if key not in target_dictionary_copy:
            continue
        same_rabbit_pos = rabbit_positions.count(value)
        if same_rabbit_pos >= tile_cap:  # check if target value is already max out in original list
            final_moves[key] = rabbit_positions[key]
        elif proposals.count(value) - same_rabbit_pos > tile_cap - same_rabbit_pos:  # Get the position lottery winners
            lottery_appliers = [k for k, v in target_dictionary_copy.items() if v == value]
            lottery_winners = rng.sample(lottery_appliers, tile_cap - same_rabbit_pos)
            for i in lottery_appliers:
                target_dictionary_copy.pop(i)
                if i in lottery_winners:
                    final_moves[i] = value
                else:
                    final_moves[i] = rabbit_positions[i]
        else:
            final_moves[key] = value
    return final_moves


def apply_moves(grid, rabbits, targets, move_cst, idle_cst) -> None:
    """
    Overwrite each rabbit’s position with its target.
    :param grid: simulation grid
    :param rabbits: list of rabbit's current position
    :param targets: list of target positions
    :param move_cst: cost of energy to potentially move rabbit
    :param idle_cst: cost of energy to potentially stay idle
    :return: None
    """
    for index in range(len(rabbits)):
        if rabbits[index][0:2] == targets[index]:  # Rabbit is staying idle on his tile
            rabbits[index][2] -= idle_cst
        else:  # Rabbit has a new target position to move
            # Add empty space to the tile the rabbit is about to leave. It should not exceed the total tile capacity.
            grid[rabbits[index][1]][rabbits[index][0]][1] += 1
            # Move the rabbit
            rabbits[index] = [targets[index][0], targets[index][1], rabbits[index][2] - move_cst]
            # Reduce the new tile's entity cap
            grid[rabbits[index][1]][rabbits[index][0]][1] -= 1


def eat_cells(grid, rabbits, regrow, energy_gain) -> list[list[int, int]]:
    """
    Eats up a cell's grass for all the rabbits and sets the regrow timer for the grass on the cell.
    :param grid: simulation grid
    :param rabbits: list of rabbit's positions
    :param regrow: growth time to be set on eaten tiles
    :param energy_gain: energy to gain after eating grass
    :return: set of tuples of coordinates that have been eaten recently
    """
    newly_eaten = []
    for index in range(len(rabbits)):
        if grid[rabbits[index][1]][rabbits[index][0]][0] == 0:
            grid[rabbits[index][1]][rabbits[index][0]][0] = regrow  # Set new timer for grass to grow again
            rabbits[index][2] += energy_gain  # Give energy gains to rabbits who have eaten grass
            newly_eaten.append(rabbits[index][0:2])  # Save the newly eaten position on grid for later use
    return newly_eaten


def regrow_step(grid, width, height, newly_eaten) -> None:
    """
    Decrements the timer of every tile on grid by 1, clamped to 0.
    :param grid: simulation grid.
    :param width: width of grid
    :param height: height of grid
    :param newly_eaten: List of tiles to skip the growth.
    :return: None
    """
    for i in range(height):
        for j in range(width):
            if [j, i] in newly_eaten:
                continue  # don't decrement the cell we just set to G this tick
            if grid[i][j][0] > 0:
                grid[i][j][0] -= 1


def reproduce(grid, rabbits, rng, width, height, threshold, cost, spawn_energy) -> list:
    """
    takes all rabbits and makes it reproduce by cutting some energy and spawning a new rabbit in grid near parent of the rabbit has the reproduction threshold
    :param grid: simulation grid
    :param rabbits: list of rabbits
    :param rng: RNG for randomness
    :param width: width of grid
    :param height: height of grid
    :param threshold: reproduction threshold
    :param cost: reproduction cost of parent
    :param spawn_energy: initial energy of the spawned infant
    :return newly_born: list of newly born rabbits
    """
    spawnable_directions = [[1, 0], [-1, 0], [0, 1], [0, -1]]
    newly_born = []

    for index in range(len(rabbits)):
        if rabbits[index][2] >= threshold:
            rabbits[index][2] -= cost  # drain energy if either it successfully gives birth or fails
            directions = rng.sample(spawnable_directions, 4)
            for direction in directions:  # goes through all direction for spawnable conditions
                potential_tile = [rabbits[index][0] + direction[0], rabbits[index][1] + direction[1]]

                # Only spawn child if the potential tile is within grid bounds and the tile has space for entity
                if 0 <= potential_tile[0] < width and 0 <= potential_tile[1] < height and \
                        grid[potential_tile[1]][potential_tile[0]][1] > 0:
                    spawned_infant = [potential_tile[0], potential_tile[1],
                                      spawn_energy]  # spawn one if a direction is valid for spawning
                    grid[potential_tile[1]][potential_tile[0]][1] -= 1  # consume 1 free slot
                    newly_born.append(spawned_infant)
                    break
            else:  # If no adjacent tile is possible to spawn then spawn it on parent's tile if there is space for entity
                if grid[rabbits[index][1]][rabbits[index][0]][1] > 0:
                    spawned_infant = (rabbits[index][0], rabbits[index][1],
                                      spawn_energy)  # spawn infant at parent's position if no direction is spawnable
                    grid[rabbits[index][1]][rabbits[index][0]][1] -= 1  # consume 1 free slot
                    newly_born.append(spawned_infant)

    return newly_born


def remove_dead_bodies(grid, rabbits) -> None:
    """
    Remove rabbits from grid whose energy levels have reached 0 and so are dead.
    :param grid: simulation grid
    :param rabbits: List of rabbits.
    :return: None
    """
    for i in range(len(rabbits)):
        if rabbits[i][2] <= 0:
            grid[rabbits[i][1]][rabbits[i][0]][1] += 1
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
    grid = init_grid(grid_width, grid_height, tile_capacity)
    list_of_rabbits = place_rabbits(grid, initial_rabbits, RNG, starting_energy)

    while sim_ticks < total_ticks:

        # Make every rabbit move in a random possible direction
        next_moves_proposal = decide_moves(grid_width, grid_height, list_of_rabbits, RNG)
        next_final_moves = resolve_moves_lottery(list_of_rabbits, next_moves_proposal, tile_capacity, RNG)
        apply_moves(grid, list_of_rabbits, next_final_moves, move_cost, idle_cost)

        # after movement, rabbits can eat grass
        recently_eaten = eat_cells(grid, list_of_rabbits, regrow_rate, eating_gains)
        regrow_step(grid, grid_width, grid_height, recently_eaten)

        # Rabbits can now reproduce if they meet the energy requirement
        new_born = reproduce(grid, list_of_rabbits, RNG, grid_width, grid_height, reproduction_threshold,
                             reproduction_cost,
                             initial_energy)
        list_of_rabbits += new_born

        # clear any dead rabbits whose energy level reaches 0
        remove_dead_bodies(grid, list_of_rabbits)

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

        # Update tick and render counter
        sim_ticks += 1
        render_counter -= 1
        # time.sleep(1 / 20)

    # Post-simulation summary
    print(
        f"done: ticks={total_ticks} average_grass_coverage = {((sum_coverage / total_ticks) * 100):.1f}% min = {(min_cov * 100):.1f}% max = {(max_cov * 100):.1f}%")


def run_curses():
    grid = init_grid(grid_width, grid_height, tile_capacity)
    rabbits = place_rabbits(grid, initial_rabbits, RNG, starting_energy)
    sim_ticks = 0
    sum_coverage = 0.0
    min_cov = 1.0
    max_cov = 0.0
    total_cells = grid_width * grid_height

    def step_fn():
        nonlocal sim_ticks, sum_coverage, min_cov, max_cov, grid, rabbits
        if sim_ticks < total_ticks:
            next_moves_proposal = decide_moves(grid_width, grid_height, rabbits, RNG)
            next_final_moves = resolve_moves_lottery(rabbits, next_moves_proposal, tile_capacity, RNG)
            apply_moves(grid, rabbits, next_final_moves, move_cost, idle_cost)
            newly = eat_cells(grid, rabbits, regrow_rate, eating_gains)
            regrow_step(grid, grid_width, grid_height, newly)
            new_born = reproduce(grid, rabbits, RNG, grid_width, grid_height, reproduction_threshold, reproduction_cost,
                                 initial_energy)
            rabbits += new_born
            remove_dead_bodies(grid, rabbits)

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
