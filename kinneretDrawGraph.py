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
import json

upperRedLine = -208.8
lowerRedLine = -213.0
histMin = -214.87

outputDateFormat = '%Y-%m-%d'
dataFile = 'data/levels-pd.csv'
chartTitle = "Kinneret Level (Sea of Galilee)<br>(m) below sea level<br>by @brianoflondon"

# df = pd.DataFrame()
# dfmin = pd.DataFrame()
# dfmax = pd.DataFrame()


def setupDataFrames(dateFr=None, dateTo=None):
    """ Set up the global dataframe with all the main data """
    df = pd.read_csv(dataFile, parse_dates=['date'], date_parser=d_parser)
    df.set_index('date', inplace=True)
    df.sort_values(by='date', ascending=False, inplace=True)

    # Filter by dates if we want a limited subset
    if dateFr is not None:
        filt = df.index >= dateFr
        df = df[filt]
    if dateTo is not None:
        filt = df.index <= dateTo
        df = df[filt]

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

    dfmin['annote'] = [makeAnnote(x, y, 'red', 40)
                       for (x, y) in zip(dfmin['date'], dfmin['lv'])]
    dfmax['annote'] = [makeAnnote(x, y, 'green', -40)
                       for (x, y) in zip(dfmax['date'], dfmax['lv'])]

    df['rhdays'] = [daysSinceRH(x) for x in df.index]

    return dfmin, dfmax


def fillHebYear(df):
    """ Takes in dataframe and creates a new data frame with Heb Year
        and date of Rosh Hash """
    firstYear = datetime(min(df.index).year, 1, 1, 0)
    lastYear = datetime(max(df.index).year+1, 12, 31, 0)

    dfRH = pd.DataFrame(index=range(firstYear.year, lastYear.year))
    dfRH['roshhash'] = [roshHash(yr) for yr in dfRH.index]
    dfRH['hebyear'] = [getHebYear(d) for d in dfRH['roshhash']]
    dfRH['gregyear'] = dfRH.index
    dfRH.set_index('roshhash', inplace=True)
    return dfRH


def getHebDate(date):
    """ Returns the year, month, day of the Hebrew date for a DateTime object"""
    day = date.day
    month = date.month
    year = date.year
    return hebrew.from_gregorian(year, month, day)


def getHebMonthDay(date):
    """ Returns the Hebrew month and day only as a string """
    _, month, day = getHebDate(date)
    return(f'{month}-{day}')


def getHebYearMonthDay(date):
    """ Returns the Hebrew month and day only as a string """
    year, month, day = getHebDate(date)
    return(f'{year}<br>{month}-{day}')


def getHebYear(date):
    """ Returns only the Hebrew Year """
    year, month, day = getHebDate(date)
    return year


def d_parser(x): return datetime.strptime(x, outputDateFormat)


def roshHashLine(x):
    """ Return a dictionary object for a vertical line. """
    thisShape = go.layout.Shape(
        type='line',
        x0=x,
        y0=histMin,
        x1=x,
        y1=upperRedLine,
        line=dict(
            color='Red',
            width=1
        )
    )
    return thisShape


def getAnnoteText(date):
    """ Takes in a date and returns the month-day and Hebrew month-day """
    gregT = date.strftime('%b-%d<br>%Y')
    hebT = getHebYearMonthDay(date)
    anT = f'{gregT}<br>{hebT}<br>'
    return anT


def makeAnnote(x, y, colour, shift):
    """ Make an annotation for level of lake including label
        returns an annotation object"""
    label = getAnnoteText(x)
    thisAnnote = go.layout.Annotation(
        x=x,
        y=y,
        ax=0,
        ay=shift,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor='#636363',
        text=label,
        bordercolor="#c7c7c7",
        borderwidth=2,
        borderpad=2,
        bgcolor=colour,
        opacity=0.7,
        font=dict(
            family="Courier New, monospace",
            size=12,
            color="#ffffff"
        )
    )
    return thisAnnote


def drawYearBoxes():
    """ Draw boxes around the Hebrew Years """
    pass


def drawLevel(level, colour, df):
    """ return a dictionary fig.add_shape object with a horizontal line """
    # firstDate = max(df.index)
    # lastDate = min(df.index)
    firstYear = datetime(min(df.index).year, 1, 1, 0)
    lastYear = datetime(max(df.index).year, 12, 31, 0)
    line = go.layout.Shape(
        type='line',
        x0=firstYear,
        y0=level,
        x1=lastYear,
        y1=level,
        line=dict(
            color=colour,
            width=3
        )
    )
    return line


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


def drawKinGraph():
    """ Draw the graph """
    # Global Filter
    dateFrom = datetime(2066, 1, 1)
    df = setupDataFrames()
    dfmin, dfmax = fillMinMax(df)

    # First line
    fig = px.scatter(df, x=df.index, y='level', title=chartTitle,
                    labels={'x': 'Date', 'y': 'm below Sea Level'})
    # Second line
    fig.add_trace(go.Scatter(x=df.index, y=df['level'].interpolate(method='time', interval='20'),
                             mode='lines', showlegend=False))

    # Add the annotations for max and min
    # dfmin.apply(lambda row: fig.add_annotation(row['annote']), axis=1)
    # dfmax.apply(lambda row: fig.add_annotation(row['annote']), axis=1)

    dnAn = []
    dfmin.apply(lambda row: dnAn.append(row['annote']), axis=1)

    upAn = []
    dfmax.apply(lambda row: upAn.append(row['annote']), axis=1)
    lines = [drawLevel(upperRedLine, 'Blue', df),
             drawLevel(lowerRedLine, 'Red', df),
             drawLevel(histMin, 'Black', df)]

    for line in lines:
        fig.add_shape(line)

    dfmin['rhannote'] = [roshHashLine(x) for x in dfmin['roshhash']]
    rhSh = []
    dfmin.apply(lambda row: rhSh.append(row['rhannote']), axis=1)
    # dfmin.apply(lambda row: fig.add_shape(row['rhannote']), axis=1)

    dfRH = fillHebYear(df)

    dfRH['ypos'] = [histMin+.18 if x %
                    2 == 0 else histMin+.1 for x in dfRH['hebyear']]

    # Third Line
    fig.add_trace(go.Scatter(
        x=dfRH.index,
        dx=3,
        y=dfRH['ypos'],
        mode="text",
        name="Hebrew Year",
        showlegend=False,
        text=dfRH['hebyear'],
        textposition="top right",
        visible=False
    ))

    # https://plotly.com/python/custom-buttons/
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                name="Annotations",
                direction="right",
                active=0,
                x=0.7,
                y=1.1,
                buttons=list([
                    dict(label="None",
                         method="update",
                         args=[{"visible": [True, True, True]},
                               {"title": chartTitle,
                                "annotations": []}]),
                    dict(label="High",
                         method="update",
                         args=[{"visible": [True, True, True]},
                               {"title": chartTitle,
                                "annotations": upAn}]),
                    dict(label="Low",
                         method="update",
                         args=[{"visible": [True, True, True]},
                               {"title": chartTitle,
                                "annotations": dnAn}]),
                    dict(label="All",
                         method="update",
                         args=[{"visible": [True, True, True]},
                               {"title": chartTitle,
                                "annotations": upAn + dnAn}])
                ]),
            ),
            dict(
                type="buttons",
                name="Lines",
                direction="right",
                active=0,
                x=0.7,
                y=1.05,
                buttons=list([
                    dict(label="None ",
                         method="update",
                         args=[{"visible": [True, True, False]},
                               {"title": chartTitle,
                                "shapes": []}]),
                    dict(label="Level Lines",
                         method="update",
                         args=[{"visible": [True, True, False]},
                               {"title": chartTitle,
                                "shapes": lines}]),
                    dict(label="Rosh Hashona",
                         method="update",
                         args=[{"visible": [True, True, True]},
                               {"title": chartTitle,
                                "shapes": rhSh}]),
                    dict(label="All Lines",
                         method="update",
                         args=[{"visible": [True, True, True, ]},
                               {"title": chartTitle,
                                "shapes": lines + rhSh}])
                ])
            )
        ])

    # Adding the Rosh Hashona lines
    # top = df['level'].max()
    dfmin['rhannote'] = [roshHashLine(x) for x in dfmin['roshhash']]

    firstYear = datetime(min(df.index).year, 1, 1, 0)
    lastYear = datetime(max(df.index).year, 12, 31, 0)

    # fig.update_xaxes(range=[firstYear, lastYear], fixedrange=False)
    fig.update_yaxes(range=[histMin-.1, upperRedLine+.1], fixedrange=False)
    fig.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ))
    fig.update_layout(
        xaxis=dict(
            range=[firstYear, lastYear],
            fixedrange=False,
            rangeselector=dict(
                yanchor='top',
                xanchor='left',
                x=0.02,
                y=0.02,
                borderwidth=1,
                bgcolor='#d3d3d3',
                activecolor='Green',
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
                    dict(count=40,
                         label="40y",
                         step="year",
                         stepmode="backward"),
                    dict(count=56,
                         label="56y",
                         step="year",
                         stepmode="backward")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )

    fig.add_layout_image(
        dict(
            source="https://i1.wp.com/brianoflondon.me/blog/wp-content/uploads/2019/01/cropped-Brian-of-London-with-sig-600x600.png?w=250&ssl=1",
            xref="paper", yref="paper",
            x=0.1, y=0.05,
            sizex=0.2, sizey=0.2,
            xanchor="left", yanchor="bottom"
        )
    )


    


    # fig.update_layout(autosize = True, height = 1080, width =1920)
    pio.write_html(fig, file='index.html', auto_open=True)
    # chartStudioCreds()

    return True


if __name__ == "__main__":
    drawKinGraph()
