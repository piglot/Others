import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--array name', metavar='machinespec', nargs='+',help='array names')

args = parser.parse_args()
print args.accumulate(args.integers)
