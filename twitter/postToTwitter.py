import pandas as pd
import json
import csv
import datetime
# from twitterCreds import setupTweets
from twitter.twitterCreds import setupTweets


def getYearAgo(df, i, y):
    """ Get text comparint the level i days ago to y years ago. """
    tLev = df.iloc[[i]]['level'].item()
    yearAgo = pd.DateOffset(years=-y) + df.index[i]
    filt = df.index.get_loc(yearAgo, method='nearest')
    # filt = df.index == yearAgo
    levelYago = df.iloc[filt].level
    # dateYago = df.iloc[filt].name.strftime('%d %b')
    # changeYago = round(df[filt]['7day'].item(), 2)
    yearDiff = round(tLev - levelYago, 2)
    if yearDiff > 0:
        lowHigh = 'higher than'
    elif yearDiff == 0:
        lowHigh = 'the same as'
    else:
        lowHigh = 'lower than'
    s = ''
    if y > 1:
        s = 's'

    # levelHist = f'{yearDiff}m {lowHigh} {y} year{s} ago ({yearAgo:%Y} {levelYago}m)'
    levelHist = f'{yearDiff}m {lowHigh} {yearAgo:%Y} {levelYago}m'
    return levelHist


def getTweetText(df, i=0):
    """ Returns a string for a tweet text based on level (i) days ago """
    tDate = df.index[i]
    tLev = df.iloc[[i]]['level'].item()
    tDif = round(1000*df.iloc[[i]]['7day'].item(), 2)
    if tDif < 0:
        tCh = f'📉 dropping {-tDif:.0f}mm'
    elif tDif == 0:
        tCh = '🟢 without changing'
    elif tDif > 0:
        tCh = f'📈 rising {tDif:.0f}mm'

    t1Dif = (tLev - df.iloc[[i+1]]['level'].item())*1000
    if t1Dif < 0:
        t1Ch = f'📉 dropping {-t1Dif:.0f}mm'
    elif t1Dif == 0:
        t1Ch = '🟢 without changing'
    elif t1Dif > 0:
        t1Ch = f'📈 rising {t1Dif:.0f}mm'

    # are we giving today's level?
    if tDate == pd.Timestamp.today().date():
        wasIs = 'is'
    else:
        wasIs = 'was'

    levelNow = f'💧{tDate:%a %b %d} Kinneret level {wasIs} {tLev:.3f}m\n{tCh} in 7 days.'
    levelYst = f'{t1Ch} since last reading.'
    levelHist = []
    for y in [1, 5, 10]:
        levelHist.append(getYearAgo(df, i, y))

    stLH = '\n'.join(levelHist)
    return f'{levelNow}\n{levelYst}\n\n{stLH}\n#Kinneret #SeaOfGalilee http://brianoflondon.me/kinneret/'


def getLastTweetID():
    """ Return the ID of the last tweet in the thread for the Kinneret level """
    with open('last_tweet.json', 'r') as jsfile:
        lastTweet = json.load(jsfile)
    return lastTweet['id'], lastTweet['entities']['urls'][0]['expanded_url']


def sendLatestTweet(df, send=False, newItems=1):
    """ Send the latest level tweet.
        Returns the tweet txt and the threadID if sent """
    # Lat and long of centre of Kinneret 32.822564, 35.592016
    # Tiberius 32.793809, 35.542755
    tweets = []
    if newItems > 1:
        tweets.append(getCatchUpTweet(df, newItems))

    tweets.append(getTweetText(df))

    if send:
        threadIDs, tweetURLs, errors = sendTweet(tweets)
        return True, tweets, threadIDs, tweetURLs, errors
    else:
        return False, tweets, [], [], []


def getCatchUpTweet(df, newReadings):
    """ Build the Text for a tweet catching up the most recent new readings """
    tweetTxt = f"💧Since the last Tweet we've had {newReadings} new readings:\n"
    levels = df.iloc[0:newReadings]['level'].tolist()
    dates = df.iloc[0:newReadings].index.tolist()
    levels.reverse()
    dates.reverse()
    for l, d in zip(levels, dates):
        tweetTxt = tweetTxt + (f'{d:%d %b}: {l:0.3f}\n')

    return tweetTxt


def sendTweet(tweets):
    """ Just send a tweet or tweets from a list"""
    success, answ, api = setupTweets()
    if not success:
        return answ
    latt = 32.793809
    longg = 35.542755
    threadIDs = []
    threadURLs = []
    errors = []
    for tweetTxt in tweets:
        threadID, _ = getLastTweetID()
        try:
            thisID = api.update_status(status=tweetTxt,
                                        lat=latt,
                                        long=longg,
                                        in_reply_to_status_id=threadID)
        
        except Exception as ex:
            errors.append(f'Tweet Problem: {ex}')
            print(f'Tweet Problem: {ex}')
            # logger.warning(f'Tweet Problem: {ex}')
            thisID = getTweetJson(threadID)
        
        iD = thisID._json['id']
        urL = thisID._json['entities']['urls'][0]['expanded_url']
        dateC = thisID._json['created_at']
            
        threadIDs.append(iD)
        threadURLs.append(urL)

        with open('last_tweet.json', 'w') as jsfile:
            json.dump(thisID._json, jsfile, indent=2)


        with open('tweet_ids.csv', 'a') as tFile:
            csvRow = [dateC,iD,urL]
            writer = csv.writer(tFile)
            writer.writerow(csvRow)

    return threadIDs, threadURLs, errors


def fillThreadCSV(thisId):
    """ Take in an Id and fill a csv with all the replies """
    success, answ, api = setupTweets()
    if not success:
        return answ
    csvRows = []
    
    myStatus = api.get_status(id=thisId, include_card_uri=True)

    dateC = myStatus._json['created_at']
    iD = myStatus._json['id']
    urL = myStatus._json['entities']['urls'][0]['expanded_url']
    
    inReplyTo = myStatus._json['in_reply_to_status_id']

    csvRow = [dateC,iD,urL]
    csvRows.append(csvRow)
    while inReplyTo is not None:
        myStatus = api.get_status(id=inReplyTo, include_card_uri=True)
        inReplyTo = myStatus._json['in_reply_to_status_id']
        dateC = myStatus._json['created_at']

        iD = myStatus._json['id']
        urL = myStatus._json['entities']['urls'][0]['expanded_url']
        csvRow = [dateC,iD,urL]
        print(csvRow)
        csvRows.insert(0, csvRow)
            
    with open('tweet_ids.csv', 'w') as tFile:
        writer = csv.writer(tFile)
        header = ['created_at','id','expanded_url']
        writer.writerow(header)
        for row in csvRows:
            writer.writerow(row)



def getTweetJson(thisId):
    """ Grabs and saves as the last_tweet.json the ID past """
    success, answ, api = setupTweets()
    if not success:
        return answ

    myStatus = api.get_status(id=thisId, include_card_uri=True)
    myJson = myStatus._json

    with open('last_tweet.json', 'w') as jsfile:
        json.dump(myJson, jsfile, indent=2)

    return myStatus



if __name__ == "__main__":
    pass
