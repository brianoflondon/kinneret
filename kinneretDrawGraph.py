# kinneretDrawGraph
""" This is a complete mess at this point having been converted from a Jupyter notebook
    with very few modifications """


from datetime import datetime
import pandas as pd
import csv
import plotly as py
import plotly.graph_objs as go
import plotly.express as px
import plotly.io as pio
from convertdate import hebrew, holidays
from myChartStudio import chartStudioCreds
import chart_studio.plotly as cs_py

upperRedLine = -208.8
lowerRedLine = -213.0
histMin = -214.87

def getHebDate(date):
    """ Returns the year, month, day of the Hebrew date for a DateTime object"""
    day = date.day
    month = date.month
    year = date.year
    return hebrew.from_gregorian(year, month, day)


def getHebMonthDay(date):
    """ Returns the Hebrew month and day only as a string """
    year, month, day = getHebDate(date)
    return(f'{month}-{day}')


def getHebYear(date):
    """ Returns only the Hebrew Year """
    year, month, day = getHebDate(date)
    return year


def d_parser(x): return datetime.strptime(x, outputDateFormat)

# def getYearSeason(date):
#     """ Return the Year-season but with winter of one year running into next
#         i.e. Feb 1987 is 1986-w cut off March 1st """
#     month = date.month
#     year = date.year
#     season = getSeason(month)
#     if(month <= 3):
#         year -= 1
#     return f'{year}-{season}'

# def getSeason(month):
#     """ Return the season (s or w) but with winter of one year running into next
#         i.e. Feb 1987 is 1986-w cut off March 1st  """
#     if((month >= 8) or (month <= 3)):
#         return 'w'
#     else:
#         return 's'


outputDateFormat = '%Y-%m-%d'
dataFile = 'data/levels-pd.csv'

df = pd.read_csv(dataFile, parse_dates=['date'], date_parser=d_parser)
df.set_index('date', inplace=True)
df.sort_values(by='date', ascending=False, inplace=True)




df['year'] = df.index.year
df['month'] = df.index.month
df['week'] = df.index.week
df['day'] = df.index.day
df['weekday'] = df.index.weekday
df['hebyear'] = [getHebYear(d) for d in df.index]


# Needs a column for Year/Winter/Summer
# https://www.listendata.com/2019/07/python-list-comprehension-with-examples.html
# [makeAnnote(x,y,x.strftime('%b-%d')) for (x,y) in zip(dfmm['date-min'], dfmm['lv-min'])]

df['YearSeas'] = [f'{yr}-s' if mth > 5 else f'{yr}-w' for mth,
                  yr in zip(df['month'], df['year'])]
df['season'] = ['s' if mth > 5 else 'w' for mth in df['month']]


dfmm = pd.DataFrame(columns=['date-min', 'lv-min', 'date-max', 'lv-max'])
dfmin = pd.DataFrame(columns=['date', 'lv'])
dfmax = pd.DataFrame(columns=['date', 'lv'])


for yrs in df['YearSeas'].unique():
    yr, seas = yrs.split('-')
    filt = (df['YearSeas'] == yrs)
    if seas == 's':
        dfmin.loc[yr, 'date'] = df[filt]['level'].idxmin()
        dfmin.loc[yr,  'lv'] = df[filt]['level'].min()
    else:
        dfmax.loc[yr, 'date'] = df[filt]['level'].idxmax()
        dfmax.loc[yr,  'lv'] = df[filt]['level'].max()

dfmax






dfmin['hebdate'] = [getHebMonthDay(x) for x in (dfmin['date'])]
dfmax['hebdate'] = [getHebMonthDay(x) for x in (dfmax['date'])]

def roshHashLine(x):
    """ Return a dictionary object for a vertical line. """
    thisShape = dict(
        type='line',
        x0=x,
        y0=histMin,
        x1=x,
        y1=upperRedLine,
        line = dict(
            color='Red',
            width=1
        )
    )
    return thisShape


def makeAnnote(x, y, colour, shift):
    """ Make an annotation including label """
    label = getAnnoteText(x)
    thisAnnote = {
        'x': x,
        'y': y,
        #'y': df[row['name']].max(),
        'text': label,
        'font': dict(
            family="Courier New, monospace",
            size=16,
            color="#ffffff"
        ),
        'align': "center",
        'arrowhead': 2,
        'arrowsize': 1,
        'arrowwidth': 2,
        'arrowcolor': "#636363",
        'ax': 0,
        'ay': shift,
        #'ayref': "y",
        #'ay': df[row['name']].max(),
        #'ayref': "y",
        #'ay': df[ma][last_row] +15,
        'bordercolor': "#c7c7c7",
        'borderwidth': 2,
        'borderpad': 4,
        'bgcolor': colour,
        'opacity': 0.8
    }
    return thisAnnote

def drawYearBoxes():
    """ Draw boxes around the Hebrew Years """
    pass

def drawLevels():

    firstDate = max(df.index)
    lastDate = min(df.index)
    theseLines = []
    line = dict(
        type='line',
        x0=firstDate,
        y0=lowerRedLine,
        x1=lastDate,
        y1=lowerRedLine,
        line = dict(
            color='Red',
            width=3
        )
    )
    theseLines.append(line)
    line = dict(
        type='line',
        x0=firstDate,
        y0=upperRedLine,
        x1=lastDate,
        y1=upperRedLine,
        line = dict(
            color='Blue',
            width=3
        )
    )
    theseLines.append(line)
    return theseLines


def getAnnoteText(date):
    """ Takes in a date and returns the month-day and Hebrew month-day """
    nl = "\n"
    gregT = date.strftime('%b-%d')
    hebT = getHebMonthDay(date)
    anT = f'{gregT}<br>{nl}{hebT}'
    return anT


# df['level'].interpolate(method='cubic')
# df['level'].rolling(window=5).mean()




fig = px.scatter(df, x=df.index, y='level', title='Kinneret Water Level',
                 labels={'x': 'Date', 'y': 'mm below Sea Level'})
fig.add_trace(go.Scatter(x=df.index, y=df['level'].interpolate(
    method='time', interval='3'), mode='lines'))



# https://plotly.com/python/tick-formatting/
# fig.update_layout(
#     xaxis = dict(
#         tickmode = 'array',
#         tickvals = [],
#         ticktext = []
#     )
# )


lines = drawLevels()
fig.add_shape(lines[0])
fig.add_shape(lines[1])

dfmin.style.format({'date': lambda d: d.strftime('%m-%d-%y')})
dfmax.style.format({'date': lambda d: d.strftime('%m-%d-%y')})

dfmin['annote'] = [makeAnnote(x, y, 'red', 80)
                   for (x, y) in zip(dfmin['date'], dfmin['lv'])]
dfmax['annote'] = [makeAnnote(x, y, 'green', -80)
                   for (x, y) in zip(dfmax['date'], dfmax['lv'])]

dfmin.apply(lambda row: fig.add_annotation(row['annote']), axis=1)
dfmax.apply(lambda row: fig.add_annotation(row['annote']), axis=1)

# fig.add_annotation(dfmm.loc[1968,'annote'])
# fig.show()

def daysSinceJan1(date):
    """ Returns the number of days since Jan 1st """
    year = date.year
    adate = datetime(year, 1, 1)
    return date - adate


def daysSinceRH(date):
    """ Returns the number of days since Rosh Hashona """
    year = date.year
    rh = ()
    rh = holidays.rosh_hashanah(year)
    rhdate = datetime(rh[0], rh[1], rh[2])
    diff = date-rhdate
    if (diff.days) < 0:
        rh = holidays.rosh_hashanah(year-1)
        rhdate = datetime(rh[0], rh[1], rh[2])
        diff = date-rhdate
    return diff

    # rhlast = holidays.rosh_hashanah(year-1)


def roshHash(dateoryear):
    """ Returns the date of Rosh Hashonah as a datetime object 
        Takes either a date or just a year """
    if type(dateoryear) is datetime:
        year = dateoryear.year
    elif type(dateoryear) is int:
        year = dateoryear
    else:
        year = int(dateoryear)
    rh = holidays.rosh_hashanah(year)
    rhdate = datetime(rh[0], rh[1], rh[2])
    return rhdate


# print(daysSinceRH(datetime.datetime(1973,1,28)))
# print(rh[0],rh[1],rh[2])
# print(timeSinceJan1(datetime.datetime(1973,1,28)))
d = datetime(1880, 1, 1)
# roshHash(2020)
type(d)
print(roshHash(d))


dfmin['jan1days'] = [daysSinceJan1(x) for x in dfmin['date']]
dfmin['rhdays'] = [daysSinceRH(x) for x in dfmin['date']]
dfmin['roshhash'] = [roshHash(d) for d in dfmin.index]
dfmax['jan1days'] = [daysSinceJan1(x) for x in dfmax['date']]
dfmax['rhdays'] = [daysSinceRH(x) for x in dfmax['date']]
dfmax['roshhash'] = [roshHash(d) for d in dfmax.index]
dfmax.describe()


# Adding the Rosh Hashona lines
top = df['level'].max()
dfmin['rhannote'] = [roshHashLine(x) for x in dfmin['roshhash']]
dfmin.apply(lambda row: fig.add_shape(row['rhannote']), axis=1)
# dfmin.apply(lambda row: fig.add_annotation(row['rhannote']), axis=1)
# fig.show()

fig.update_layout(
    xaxis=dict(
        rangeselector=dict(
            borderwidth=10,
            buttons=list([
                dict(count=1,
                     label="1y",
                     step="year",
                     stepmode="backward"),
                dict(count=4,
                     label="4y",
                     step="year",
                     stepmode="backward"),
                dict(count=20,
                     label="20y",
                     step="year",
                     stepmode="backward"),
                dict(count=1,
                     label="1y",
                     step="year",
                     stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(
            visible=True
        ),
        type="date"
    )
)


# fig.update_layout(autosize = True, height = 1080, width =1920)
pio.write_html(fig, file='index.html', auto_open=True)
chartStudioCreds()
# cs_py.plot(fig, filename='Kinneret Historical Water Level (mm).html', auto_open=True)


# Available frequencies in pandas include hourly ('H'), calendar daily ('D'), business daily ('B'), weekly ('W'), monthly ('M'), quarterly ('Q'), annual ('A'), and many others. Frequencies can also be specified as multiples of any of the base frequencies, for example '5D' for every five days.


# tol = .20

# q_low = dfmin["rhdays"].quantile(tol)
# q_hi = dfmin["rhdays"].quantile(1-tol)

# filt = ((dfmin['rhdays'] > q_low) & (dfmin['rhdays'] < q_hi))
# dffilt = dfmin[filt]
# dffilt.describe()

# q_low = dfmax["rhdays"].quantile(tol)
# q_hi = dfmax["rhdays"].quantile(1-tol)

# filt = (dfmax['rhdays'] > q_low) & (dfmax['rhdays'] < q_hi)

# dffilt = dfmax[filt]
# dffilt.describe()

# q_low = dfmin["level"].quantile(0.01)
# q_hi = df["col"].quantile(0.99)

# df_filtered = df[(df["col"] < q_hi) & (df["col"] > q_low)]


# df['diff'] = df['level'].pct_change(freq='W', fill_method='pad')

# figd = px.scatter(df, x=df.index, y=df['diff'], title='Difference period')
# figd.show()


# # %%
# dataFile = 'data/levels-pd.csv'
# def d_parser(x): return datetime.strptime(x, '%Y-%m-%d')


# dfnew = pd.read_csv(dataFile, parse_dates=['date'], date_parser=d_parser)
# dfnew.set_index('date', inplace=True)

# dDate = datetime(2020, 10, 8)
# filt = (dfnew.index == dDate)
# dfnew.describe()


# # %%
# df.sort_values(by='date', ascending=False, inplace=True)
# filt = df['level'] > df['level'][0]
# df[filt]['level']
