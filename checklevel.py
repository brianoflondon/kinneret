# checklevel.py
# https://realpython.com/command-line-interfaces-python-argparse/#conclusion
import argparse
import os
import sys
from getNewReading import runCheckAndTweet, checkAndTweet
from datetime import datetime, timedelta
import time


def timeInRange(start, end, x):
    """Return true if x is in the range [start, end] for datetime objects"""
    if start.time() <= end.time():
        return start.time() <= x.time() <= end.time()
    else:
        return start.time() <= x.time() or x.time() <= end.time()
    
def githubUpdate():
    """ Git Commit and update after running """
    datestamp = datetime.now()
    comMes = f'Auto Commit {datestamp}'
    dirname = os.path.dirname(__file__)
    os.chdir(dirname)
    os.system(f'git commit -a -m "{comMes}"')
    os.system(f'git push')

def printTimeNow(msg = ''):
    """ prints the time now """
    if len(msg) > 0:
        msg = ' - ' + msg
    datestamp = datetime.now()
    comMes = f'The time now is: {datestamp}{msg}'
    print(comMes)

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
                       action='store_true', required=False,
                       default=True,
                       help='Automatic starts up and waits till 11:00 then checks every 10m until 12:15 then checks every 2 hours again')

my_parser.add_argument('-c',
                       '--commit',
                       action='store_true', required=False,
                       default=False,
                       help='Run a Git Commit and Git Push and nothing else')

my_parser.add_argument('-t',
                       '--time',
                       action='store_true', required=False,
                       default=False,
                       help='prints out the time')


# my_parser.add_argument('-h',
#                        '--help',
#                        action='help',
#                        help='Shows Help')

printTimeNow('Starting')
# Execute parse_args()
args = my_parser.parse_args()
myArgs = vars(args)

if myArgs['commit'] is True:
    githubUpdate()
    quit()
    
if myArgs['time'] is True:
    printTimeNow()
    quit()

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
    sent = False
    weekDays = ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
    while True:
        daysToRun = (0,1,2,3,4,6)
        fre = 10
        freTD = timedelta(minutes=fre)
        now = datetime.now()
        printTimeNow()

        startChecks = now.replace(hour=11, minute=0)
        endChecks = now.replace(hour=13, minute=19)
        
        maxTdelta = endChecks - datetime.now()
        if now >= endChecks:
            print(f'No point running after {endChecks:%H:%M on %Y-%m-%d}')
            printTimeNow('End')
            quit()
        
        if now.weekday() in daysToRun: #Monday to 
            if (timeInRange(startChecks,endChecks,now)):
                maxTdelta = endChecks - now
                maxT = maxTdelta.total_seconds() / 60
                fre = 10
                _, sent, txt = runCheckAndTweet(maxT, fre)

                if sent:
                    githubUpdate()
                    printTimeNow('End')
                    quit()

            elif now < startChecks:
                now = datetime.now()
                fre = 60
                maxTdelta = startChecks - now
                maxT = maxTdelta.total_seconds() / 60
                if maxT < fre:
                    fre = maxT - 1
                _, sent, txt = runCheckAndTweet(maxT, fre)
                if sent:
                    githubUpdate()
                    printTimeNow('End')
                    quit()
            elif now >= endChecks:
                print(f'No point running after {endChecks:%H:%M on %Y-%m-%d}')
                printTimeNow('End')
                quit()

            
        else:
            dayText = weekDays[now.weekday()]
            print(f'Not Running on {dayText}')
            break