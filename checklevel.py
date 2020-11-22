# checklevel.py
# https://realpython.com/command-line-interfaces-python-argparse/#conclusion
import argparse
import os
import sys
from getNewReading import runCheckAndTweet, checkAndTweet
from datetime import datetime


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

my_parser.add_argument('-a',
                       '--auto',
                       action='store', type=bool, required=False,
                       default=False,
                       help='Automatic starts up and waits till 11:00 then checks every 10m until 12:15 then checks every 2 hours again')



# Execute parse_args()
args = my_parser.parse_args()
myArgs = vars(args)



if myArgs['auto'] is False:
    fre = myArgs['frequency']
    maxT = myArgs['maxtime']
    print(f'Running for {maxT}m, checking every {fre}m ....')
    _, sent, txt = runCheckAndTweet(maxT, fre)

    if sent:
        finMsg = f'Tweet sent: {txt}'
    else:
        finMsg = f'Tweet not sent: {txt}'

    print(finMsg)



else: 
    daysToRun = (0,1,2,3,6)
    now = datetime.now()
    if now.weekday() in daysToRun: #Monday to 
        while now.hour == 11:
            now = datetime.now()
            fre = 10
            maxT = 60
            print(f'Running for {maxT}m, checking every {fre}m ....')
            checkAndTweet(True)
            _, sent, txt = runCheckAndTweet(maxT, fre)
            
        else:
            fre = 30
            maxT = 600
            print(f'Running for {maxT}m, checking every {fre}m ....')
            _, sent, txt = runCheckAndTweet(maxT, fre) 
