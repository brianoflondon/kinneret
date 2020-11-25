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
                       default=False,
                       help='Automatic starts up and waits till 11:00 then checks every 10m until 12:15 then checks every 2 hours again')

# my_parser.add_argument('-h',
#                        '--help',
#                        action='help',
#                        help='Shows Help')


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
    sent = False
    weekDays = ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
    while True:
        daysToRun = (0,1,2,3,6)
        fre = 10
        freTD = timedelta(minutes=fre)
        now = datetime.now()
        print(now.time())

        startChecks = now.replace(hour=11, minute=0)
        endChecks = now.replace(hour=12, minute=15)
        
        maxTdelta = endChecks - now
        if now.weekday() in daysToRun: #Monday to 
            if (timeInRange(startChecks,endChecks,now)):
                maxTdelta = endChecks - now
                maxT = maxTdelta.total_seconds() / 60
                fre = 10
                _, sent, txt = runCheckAndTweet(maxT, fre)
                # while True:
                #     now = datetime.now()
                #     maxT = endChecks - now
                #     if maxT<freTD:
                #         break
                #     print(f'Running for {maxT}m, checking every {fre}m ....')
                #     _, sent, txt = checkAndTweet(True)
                if sent:
                    quit()
                    # time.sleep(fre*60)
            elif now < startChecks:
                now = datetime.now()
                fre = 60
                maxTdelta = startChecks - now
                maxT = maxTdelta.total_seconds() / 60
                if maxT < fre:
                    fre = maxT - 1
                _, sent, txt = runCheckAndTweet(maxT, fre)
                if sent:
                    quit()
            elif now > endChecks:
                print(f'No point running after {endChecks:%H:%M on %Y-%m-%d}')
                quit()
            
            # while True:
            #     now = datetime.now()
            #     fre = 60
            #     maxT = endChecks - now
            #     if (maxT.days > 0) and (maxT < timedelta(minutes=(fre*2))):
            #         fre = maxT.min()
            #     freTD = timedelta(minutes=fre)
            #     print(now.weekday())
            #     if (not(now.weekday() in daysToRun)) or (timeInRange(startChecks,endChecks,now)):
            #         break
            #     print(f'Running for {maxT}m, checking every {fre}m ....')
            #     _, sent, txt = checkAndTweet(True)
            #     if sent:
            #         quit()
            #     time.sleep(fre*60)
            
        else:
            dayText = weekDays[now.weekday()]
            print(f'Not Running on {dayText}')
            break