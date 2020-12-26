""" Code to reach out and grab any new readings on the Kinneret """

from requests_html import HTMLSession
import json
from bs4 import BeautifulSoup
import lxml
import os
import csv
# import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import time
import logging
import random
import re
from itertools import zip_longest
import math
import kinneretDrawGraph as kdg
import twitter.postToTwitter as tw

webDateFormat = '%d.%m.%Y'
outputDateFormat = '%Y-%m-%d'
baseUrl = 'https://www.gov.il/he/Departments/DynamicCollectors/kinneret_level'
paramUrl = '?skip='

colHead = ['level','1day','7day','1month']

upRedLine = -208.8
histMin = -214.87


def getDataFileName():
    """ Return the filename """
    outputFol = 'data'
    outputFile = 'levels-pd-calc'
    dataFile = f'{outputFol}/{outputFile}.csv'
    return dataFile


def importReadings():
    """ Import history to date and return the Pandas Dataset """
    """ Updating to import 1,7 & 30 day look back """
    dataFile = getDataFileName()

    def d_parser(x): return datetime.strptime(x, outputDateFormat)
    df = pd.read_csv(dataFile, parse_dates=['date'], date_parser=d_parser)
    df.set_index('date', inplace=True)
    # df['7day'] = df['level'].diff(periods=-7)
    return df


def pageChangeCheck(df, skipUrl=0):
    """ Has the page changed? Returns a tuple of Boolean and r.html object"""
    fetchUrl = f'{baseUrl}{paramUrl}{skipUrl}'
    # skipUrl += 10

    session = HTMLSession()
    r = session.get(fetchUrl)
    logStr = f'Fetch:  {r} - {fetchUrl}'
    logger.info(logStr)
    r.html.render(keep_page=True)
    logStr = f'Render: {r} - {fetchUrl}'
    logger.info(logStr)

    # raise Exception("Halt and Catch Fire")

    session.close()

    # Unused: reads the headline number of readings stored by the site.
    # obj = r.html.find('span.h1.reforma-medium.xs-me-10.dark-blue-txt.ng-binding')
    # countOfReadings = obj[0].text
    obj2 = r.html.find('bdi')
    dDate = datetime.strptime(obj2[0].text, webDateFormat)

    filt = (df.index == dDate)
    if len(df[filt]) > 0:
        changed = False
    else:
        changed = True
    return changed, r


def updateLevels():
    """ Check the websit and update the data/levels-pd.csv file if there are any new readings
        Returns the number of new items and the dataframe"""

    skipUrl = 0
    # folder = 'gathered'

    df = importReadings()
    changed = True

    # if changed is True:

    failure = 0
    countnewItems = 0
    newItemsPage = 11
    while changed is True and newItemsPage >= 10:
        newItemsPage = 0
        while failure < 4:
            try:
                changed, r = pageChangeCheck(df, skipUrl)
                skipUrl += 10
                break
            except Exception as ex:
                failure += 1
                logger.warning(f'Failure: {failure} Reason: {ex}')
                time.sleep(5)

        if changed is False or failure == 4:
            break

        obj = r.html.find('div.col-12.px-3.col-lg-8')
        source = obj[0].html
        soup = BeautifulSoup(source, 'lxml')
        listTags = soup.find_all(
            'span', attrs={'class': 'mr-1 xs-me-10 error-txt ng-binding'})
        xLevel = 0.0
        xDate = ''
        for elm in listTags:
            isDate = elm.bdi
            if isDate is None:
                xLevel = float(elm.next)
            else:
                xDate = str(isDate.next)
                dDate = datetime.strptime(xDate, webDateFormat)
                filt = (df.index == dDate)
                if len(df[filt]) > 0:
                    dfLev = df.loc[dDate]['level']
                    logger.info(f'{xDate} - already in data {dfLev}')
                    logger.info(f'{dDate} - {xLevel} - {dfLev}')
                else:
                    # This is where i need to add the 1day 7day 1month look back data.
                    newRow = pd.Series(data={'level': xLevel}, name=dDate)
                    df = df.append(newRow, ignore_index=False)
                    logger.info(f'Adding: {dDate} {newRow}')
                    countnewItems += 1
                    newItemsPage += 1

    if countnewItems > 0:
        dataFile = getDataFileName()

        df.sort_values(by='date', inplace=True, ascending=False)
        df = updateCalcValues(df)
        df.round({'1day': 3,'7day': 3, '1month': 3}).to_csv(dataFile, index_label='date', columns=colHead)
        # df.to_csv(dataFile, index_label='date', columns=['level'])
        # df['7day'] = df['level'].diff(periods=-7)

    return countnewItems, df

def naCheckDelta(df,x,y,dateOff):
    """ Returns the delta value for this offset first checking if the y value is NAN """
    if math.isnan(y):
        return(kdg.getLevelDelta(df,x,dateOff))
    else:
        return y


def updateCalcValues(df):
    """ Updates the 1day 7day and 1month calc values in the Dataframe
        Only updating what has changed. """
        
    dateOff1m = pd.DateOffset(months=-1)
    dateOff7d = pd.DateOffset(days=-7)
    dateOff1d = pd.DateOffset(days=-1)
    
    df['1day'] = [naCheckDelta(df,x,y,dateOff1d) for x,y in zip(df.index,df['1day'])]
    df['7day'] = [naCheckDelta(df,x,y,dateOff7d) for x,y in zip(df.index,df['7day'])]
    df['1month'] = [naCheckDelta(df,x,y,dateOff1m) for x,y in zip(df.index,df['1month'])]
    return df


def checkAndTweet(sendNow=False):
    """ Checks for a new reading, records it and tweets if something
        has changed. Returns dataframe and boolean True if tweet sent
        and the text of the tweet or no tweet sent """
    blCheck = True
    if blCheck:
        newItems, df = updateLevels()
    else:
        df = importReadings()
        newItems = 0

    if newItems > 0:
        logger.info(f'New Items found: {newItems}')
        print(f'New Items found: {newItems}')
        kdg.drawKinGraph()
        kdg.drawChangesGraph()
        kdg.uploadGraphs()

        sent, tweets, threadIDs, tweetURLs, errors = tw.sendLatestTweet(df, sendNow, newItems)
        for err in errors:
            logger.critical(err)

        # Get the first line of the tweet only
        for tweet, threadID, url in zip_longest(tweets, threadIDs, tweetURLs):
            tweetTxt = re.search('(.*)', tweet)[0]
            logTxt = f'{tweetTxt} - Thread: {threadID} {url}'
            logger.info(logTxt)

    else:
        logTxt = f'No new Items found.'
        logger.warning(logTxt)
        sent = False
        

    if sent:
        # logger.info(f'Tweet Sent: {txt}')
        notifyMac('Kinneret Levels', f'New Tweet sent {logTxt}')
    else:
        # logger.warning(f'Tweet NOT Sent: {txt}')
        notifyMac('Kinneret Levels', 'NOTHING SENT')
    return(df, sent, logTxt)        



LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename='getNewReading.log',
                    level=logging.INFO,
                    format=LOG_FORMAT)

logger = logging.getLogger()


def runCheckAndTweet(maxTime=360, freq=10):
    """ Runs the check and tweet code checking the website every freq minutes
        Tweets out the level if it changes
        Will run until the site changes or maxTime (in minutes) is reached"""

    maxSec = maxTime * 60
    freqSec = freq * 60
    sent = False
    begin = time.time()
    elapsed = time.time() - begin
    while (elapsed < maxSec):
        df, sent, txt = checkAndTweet(True)
        if sent is True:
            break

        timeRem = int(maxSec - elapsed)
        mins, secs = divmod(timeRem, 60)
        hrs, mins = divmod(mins, 60)
        fudge = 1 - ((random.random() - 0.5)/5)
        tSleep = freqSec*fudge
        sleepM, sleepS = divmod(tSleep, 60)
        msgNow = f'Waiting {sleepM:.0f}:{sleepS:.0f}. Time remaining: {hrs}h {mins}m {secs}s'
        notifyMac('Kinneret Levels', msgNow)
        logger.warning(msgNow)
        if timeRem <= freqSec:
            break
        sleepT = freqSec*fudge
        if sleepT < 0:
            sleepT = 59
        time.sleep(freqSec*fudge)
        elapsed = time.time() - begin

    return(df, sent, txt)


def notifyMac(title, message):
    """ Display a system notification on Mac with Title and Message """
    command = f'''
        osascript -e 'display notification "{message}" with title "{title}"'
        '''
    os.system(command)


def testMultiTweet():
    df = importReadings()
    sent, tweetTxts, threadIDs, tweetURLs, errors = tw.sendLatestTweet(df, False, 2)
    for t, tId, tURL in zip_longest(tweetTxts, threadIDs, tweetURLs):
        print(t, tId, tURL)


if __name__ == "__main__":
    df, sent, txt = runCheckAndTweet(1, 0.5)
    # df, sent, txt = checkAndTweet(False)
    # testMultiTweet()

# for y in range(0,100):
#     print(tw.getYearAgo(df,0,y))
    # Use this line to rebuild the last tweet json
    # twObject =tw.getTweetJson(1325738595404181505)
    
    # tw.fillThreadCSV('1325738595404181505')