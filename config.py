import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--width', default=30, type=int, help="Defines the width of the simulation grid (default: 30).")
parser.add_argument('--height', default=15, type=int, help="Defines the height of the simulation grid (default: 15).")
parser.add_argument('--ticks', default=200, type=int,
                    help="Defines the total simulation ticks/steps to run (default: 200).")
parser.add_argument('--render-every', default=10, type=int, help="Print one status line every K ticks (default: 10).")
parser.add_argument('--rabbits', default=20, type=int,
                    help="Number of rabbits in a simulation at a time (default: 20).")
parser.add_argument('--regrow', default=5, type=int, help="Defines grass regrowth delay in ticks (default: 5).")
parser.add_argument('--seed', default=None, help="Random seed for random generations (default: None).")

args = parser.parse_args()
