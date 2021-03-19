import argparse
from time import sleep
from village.world.structs import GameMap
from village.engine import *
from village.simulation import *

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--verbose', '-v', action='store_true', help='verbose mode')
parser.add_argument('--slow', '-s', action='store_true', help='verbose mode')
args = parser.parse_args()

big = SimulationManager()
big.sim_log.set_live()

RED='\u001b[31m'
YELLOW='\u001b[33m'
GREEN='\u001b[32m'
RESET='\u001b[0m'
STD=''

for _ in range(1000):
    big.tick()

    if args.verbose:
        for e in big.sim_log.get_events():
            if 'INFO' in e:
                print(e.replace('INFO', GREEN + 'INFO' + RESET))
            if 'DEBUG' in e:
                print(e.replace('INFO', YELLOW + 'DEBUG' + RESET))
            if 'WARNING' in e:
                print(e.replace('INFO', RED + 'WARNING' + RESET))

    if args.slow:
        sleep(0.5)
