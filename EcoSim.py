import random

import config

# Ecosystem variables
width = config.get_args().width
height = config.get_args().height
ticks = config.get_args().ticks
render_every = config.get_args().render_every
seed = config.get_args().seed
regrow_rate = config.get_args().regrow
total_rabbits = config.get_args().rabbits

random.seed(seed)

# Grid generation
grid = [[0 for _ in range(width)] for _ in range(height)]
total_cells = width * height

# Random placement of rabbits on the grid
rabbits = [divmod(i, height) for i in random.sample(range(width * height), total_rabbits)]


def grass_count() -> int:
    """
    Counts the total number of cells which has grass on them.
    :return: number of grassy cells in the grid
    """

    grasses = 0
    for row in grid:
        for cell in row:
            if cell == 0:
                grasses += 1
    return grasses


def move_rabbit(coord) -> tuple:
    """
    Moves the rabbit coordinate to a random direction within the grid
    :param coord: coordinate of the rabbit
    :return: new coordinate the rabbit can move to
    """
    direction_to_move = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
    new_pos = coord

    # check if new position is within grid bounds and if not then remain in same position
    if 0 <= coord[0] + direction_to_move[0] < width and 0 <= coord[1] + direction_to_move[1] < height:
        new_pos = (coord[0] + direction_to_move[0], coord[1] + direction_to_move[1])
    return new_pos
