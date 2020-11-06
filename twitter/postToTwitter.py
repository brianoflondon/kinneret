import pandas as pd
import json
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
    tDif = round(100*df.iloc[[i]]['7day'].item(), 2)
    if tDif < 0:
        tCh = f'📉 dropping {-tDif:.0f}cm'
    elif tDif == 0:
        tCh = '🟢 without changing'
    elif tDif > 0:
        tCh = f'📈 rising {tDif:.0f}cm'

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

    levelNow = f'💧{tDate:%a %b %d} the level of the Kinneret {wasIs} {tLev:.2f}m {tCh} in 7 days.'
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
    return lastTweet['id']


def sendLatestTweet(df, send=False):
    """ Send the latest level tweet.
        Returns the tweet txt and the threadID if sent """
    # Lat and long of centre of Kinneret 32.822564, 35.592016
    # Tiberius 32.793809, 35.542755
    success, answ, api = setupTweets()
    if not success:
        return answ
    threadID = getLastTweetID()
    tweetTxt = getTweetText(df)
    if send:
        latt = 32.793809
        longg = 35.542755
        thisID = api.update_status(status=tweetTxt,
                                   lat=latt,
                                   long=longg,
                                   in_reply_to_status_id=threadID)

        with open('last_tweet.json', 'w') as jsfile:
            json.dump(thisID._json, jsfile, indent=2)
        return tweetTxt, thisID._json['id']
    else:
        return (f'{tweetTxt} - not sent'), threadID


if __name__ == "__main__":
    pass
