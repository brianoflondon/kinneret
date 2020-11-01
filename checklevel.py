# checklevel.py
# https://realpython.com/command-line-interfaces-python-argparse/#conclusion
import argparse
import os
import sys
from getNewReading import runCheckAndTweet

# Create the parser
my_parser = argparse.ArgumentParser(prog='checklevel',
                                    usage='%(prog)s [options]',
                                    description='Periodically check the level of the Kinneret page')

my_parser = argparse.ArgumentParser(fromfile_prefix_chars='@')

my_parser.add_argument('-m',
                       '--maxtime',
                       action='store', type=int, required=False,
                       default=120,
                       help='Maximum time in minutes to keep running')

my_parser.add_argument('-f',
                       '--frequency',
                       action='store', type=int, required=False,
                       default=10,
                       help='Frequency of checks: minutes between checks')

my_parser.add_argument('-v',
                       '--verbose',
                       action='store_true',
                       help='an optional argument')

# Execute parse_args()
args = my_parser.parse_args()
myArgs = vars(args)

fre = myArgs['frequency']
maxT = myArgs['maxtime']
print(f'Running for {maxT}s, checking every {fre}s ....')
_, sent, txt = runCheckAndTweet(maxT, fre)

if sent:
    finMsg = f'Tweet sent: {txt}'
else:
    finMsg = f'Tweet not sent: {txt}'

print(finMsg)
