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

outputDateFormat = '%Y-%m-%d'
dataFile = 'data/levels-pd.csv'
# df = pd.DataFrame()
# dfmin = pd.DataFrame()
# dfmax = pd.DataFrame()


def setupDataFrames():
    """ Set up the global dataframe with all the main data """
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
    return df


    
def fillMinMax(df):
    """ Fills the data frames for the min an max levels of the lake """    
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

    dfmin['hebdate'] = [getHebMonthDay(x) for x in (dfmin['date'])]
    dfmax['hebdate'] = [getHebMonthDay(x) for x in (dfmax['date'])]
    dfmin['jan1days'] = [daysSinceJan1(x) for x in dfmin['date']]
    dfmin['rhdays'] = [daysSinceRH(x) for x in dfmin['date']]
    dfmin['roshhash'] = [roshHash(d) for d in dfmin.index]
    dfmax['jan1days'] = [daysSinceJan1(x) for x in dfmax['date']]
    dfmax['rhdays'] = [daysSinceRH(x) for x in dfmax['date']]
    dfmax['roshhash'] = [roshHash(d) for d in dfmax.index]
    
    dfmin.style.format({'date': lambda d: d.strftime('%m-%d-%y')})
    dfmax.style.format({'date': lambda d: d.strftime('%m-%d-%y')})

    dfmin['annote'] = [makeAnnote(x, y, 'red', 80)
                    for (x, y) in zip(dfmin['date'], dfmin['lv'])]
    dfmax['annote'] = [makeAnnote(x, y, 'green', -80)
                    for (x, y) in zip(dfmax['date'], dfmax['lv'])]


    return dfmin, dfmax

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

def drawLevel(level,colour,df):
    """ return a dictionary fig.add_shape object with a horizontal line """
    firstDate = max(df.index)
    lastDate = min(df.index)
    line = dict(
        type='line',
        x0=firstDate,
        y0=level,
        x1=lastDate,
        y1=level,
        line = dict(
            color=colour,
            width=3
        )
    )
    return line


def getAnnoteText(date):
    """ Takes in a date and returns the month-day and Hebrew month-day """
    nl = "\n"
    gregT = date.strftime('%b-%d')
    hebT = getHebMonthDay(date)
    anT = f'{gregT}<br>{nl}{hebT}'
    return anT

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




df = setupDataFrames()
dfmin, dfmax = fillMinMax(df)

fig = px.scatter(df, x=df.index, y='level', title='Kinneret Water Level',
                 labels={'x': 'Date', 'y': 'mm below Sea Level'})
fig.add_trace(go.Scatter(x=df.index, y=df['level'].interpolate(
    method='time', interval='3'), mode='lines'))

dfmin.apply(lambda row: fig.add_annotation(row['annote']), axis=1)
dfmax.apply(lambda row: fig.add_annotation(row['annote']), axis=1)

# https://plotly.com/python/tick-formatting/
# fig.update_layout(
#     xaxis = dict(
#         tickmode = 'array',
#         tickvals = [],
#         ticktext = []
#     )
# )


lines = [drawLevel(upperRedLine,'Blue',df),
         drawLevel(lowerRedLine,'Red',df),
         drawLevel(histMin,'Black',df)]

for line in lines:
    fig.add_shape(line)


# fig.add_annotation(dfmm.loc[1968,'annote'])
# fig.show()




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
