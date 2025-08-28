import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--width', default=30, type=int, help="Defines the width of the simulation grid (default: 30).")
parser.add_argument('--height', default=15, type=int, help="Defines the height of the simulation grid (default: 15).")
parser.add_argument('--ticks', default=200, type=int,
                    help="Defines the total simulation ticks/steps to run (default: 200).")
parser.add_argument('--render-every', default=1, type=int, help="Print one status line every K ticks (default: 1).")
parser.add_argument('--rabbits', default=20, type=int,
                    help="Number of rabbits in a simulation at a time (default: 20).")
parser.add_argument('--regrow', default=10, type=int, help="Defines grass regrowth delay in ticks (default: 10).")
parser.add_argument('--seed', default=None, type=int, help="Random seed for random generations (default: None).")
parser.add_argument('--ui', default='curses', choices=['none', 'curses'], type=str,
                    help="Way of how the render would be displayed (default: 'curses').")
parser.add_argument('--fps', default=60.0, type=float, help="frames to display per second (default: 60.0).")
parser.add_argument('--tps', default=8.0, type=float, help="simulation tick rate (ticks per second, default: 8.0)")

# rabbit's args
parser.add_argument('--energy-start', default=5, type=int, help="initial energy for each rabbit (default: 5).")
parser.add_argument('--move-cost', default=1, type=int, help="energy cost when a rabbit moves (N/E/S/W) (default: 1).")
parser.add_argument('--idle-cost', default=0, type=int, help="energy cost if it stays (default: 0).")
parser.add_argument('--eat-gain', default=4, type=int, help="energy gained when eating grass (default: 4).")
parser.add_argument('--repro-threshold', default=10, type=int, help="minimum energy to reproduce (default: 10).")
parser.add_argument('--repro-cost', default=5, type=int,
                    help="energy deducted from parent while giving birth(default: 5).")
parser.add_argument('--infant-energy', default=None, type=int,
                    help="energy given to a newly born child (default: repro_cost if no value passed, None is placeholder for default).")

args = parser.parse_args()

if args.width < 1 or args.height < 1:
    parser.error("The width and height should be greater than or equal to 1.")
if args.rabbits > args.width * args.height:
    parser.error("Number of rabbits should be less than total number of cells.")
if args.regrow < 0:
    parser.error("Regrow rate cannot be negative.")
if args.ticks < 1:
    parser.error("Ticks to simulate cannot be less than 1.")
if args.render_every < 1:
    parser.error("Rendering time cannot be less than 1.")
if args.fps <= 0:
    parser.error("fps must be greater than 0.")
if args.tps <= 0:
    parser.error("tps must be > 0.")
if args.repro_threshold < 0:
    parser.error("reproduction threshold cannot be less than 0.")
if args.repro_cost < 0:
    parser.error("reproduction cost cannot be less than 0.")


def get_args():
    return args
