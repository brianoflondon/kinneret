# kinneretDrawGraph
""" This is a complete mess at this point having been converted from a Jupyter notebook
    with very few modifications """


from datetime import datetime
import glob
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
from sftpconnect import connectSFTP
import pysftp
import getNewReading as gnr

upperRedLine = -208.8
lowerRedLine = -213.0
histMin = -214.87

outputDateFormat = '%Y-%m-%d'
todayDate = datetime.now()
chartTitle = f"""
Kinneret Level (Sea of Galilee) {todayDate:%d %b %Y}<br>
(m) below sea level<br>
by <a href='https://brianoflondon.me/kinneret'>Brian of London (back to main site)</a>"""

xAxesTitle = "Date (Hebrew Year)"
yAxesTitle = "Level Below Sea Level (m)"

# df = pd.DataFrame()
# dfmin = pd.DataFrame()
# dfmax = pd.DataFrame()


def getLevelDelta(df, ind, dateOff):
    """ Returns the level timedelta ago using pandas timedelta """
    timeAgo = dateOff + ind
    filt = df.index.get_loc(timeAgo, method='nearest')
    oldLevel = df.iloc[filt].level
    return df.iloc[0]['level'] - oldLevel


def setupDataFrames(dateFr=None, dateTo=None):
    """ Set up the global dataframe with all the main data """
    df = gnr.importReadings()
    df = gnr.addInterpolated(df,dateFr,dateTo)
    
    df['year'] = df.index.year
    df['month'] = df.index.month
    # df['week'] = df.index.week    #Depreciated function
    df['week'] = df.index.isocalendar().week
    df['day'] = df.index.day
    df['weekday'] = df.index.weekday
    df['hebyear'] = [getHebYear(d) for d in df.index]

    # df['7day'] = df['level'].diff(periods=-7) * 100
    # df['1month'] = df['level'].diff(periods=-30) * 100

    # df['check']= [a-b for a,b in zip(df['1monthAc'],df['1month'])]

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


def addRangeSlider(fig, df):
    """ Take in a figure and update it with a range slider """
    # firstYear = datetime(min(df.index).year, 1, 1, 0)
    firstYear = datetime(max(df.index).year-5, 1, 1, 0)
    lastYear = datetime(max(df.index).year, 12, 31, 0)
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
                buttons=rangeButtons(),
                visible=True
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        ),
        yaxis=dict(
            fixedrange=False
        )
    )
    return fig


def rangeButtons(steps=None):
    """ returns a list of buttons for range slider jumps """
    if steps == None:
        steps = [1, 4, 20, 40, 56]
    aList = []
    for s in steps:
        aDic = dict(count=s,
                    label=f'{s}y',
                    step="year",
                    stepmode="backward",
                    visible=True)
        aList.append(aDic)
    return aList


def drawKinGraph():
    """ Draw the graph """
    # Global Filter
    dateFrom = datetime(1966, 6, 1)
    # dateTo = datetime(1969,12,31)
    df = setupDataFrames(dateFrom)
    dfmin, dfmax = fillMinMax(df)

    # First line
    # fig = px.scatter(df, x=df.index, y='level', title=chartTitle,
    #                 labels={'x': 'Date', 'y': 'm below Sea Level'})
    fig = px.scatter(title=chartTitle, labels={
                     'x': 'Date', 'y': 'm below Sea Level'})

    # Second and third traces
    fig = addChangeTriangles(fig, True, df, 1)
    # Second and third traces
    fig = addChangeTriangles(fig, True, df, 7)
    
    # Fourth Trace line
    fig.add_trace(go.Scatter(x=df.index, y=df['level'],
                             name='Level',
                             mode='lines',
                             showlegend=False,
                             visible=True))

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

    # Fith Line
    fig.add_trace(go.Scatter(
        x=dfRH.index,
        dx=3,
        y=dfRH['ypos'],
        mode="text",
        name="Hebrew Year",
        showlegend=False,
        text=dfRH['hebyear'],
        textposition="top right",
        visible=True
    ))

    # allTrue = [True] * 5
    # allFalse = [False] * 5

    # https://plotly.com/python/custom-buttons/
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                name="Markers",
                direction="right",
                active=0,
                x=0.5,
                y=1.1,
                buttons=list([
                    dict(label="Line",
                         method="restyle",
                         args=[{"visible": [False, False, False, False, False, False, True]}]),
                    dict(label="▲ 1 Day 📉",
                         method="restyle",
                         args=[{"visible": [True, True, True, False, False, False, True]}]),
                    dict(label="▲ 7 Day 📉",
                         method="restyle",
                         args=[{"visible": [False, False, False, True, True, True, True]}]),
                    dict(label="▲ 1 Day",
                         method="restyle",
                         args=[{"visible": [True, True, True, False, False, False, False]}]),
                    dict(label="▲ 7 Day",
                         method="restyle",
                         args=[{"visible": [False, False, False, True, True, True, False]}])

                ]),
            ),
            dict(
                type="buttons",
                name="Annotations",
                direction="right",
                active=0,
                x=0.8,
                y=1.1,
                buttons=list([
                    dict(label="None",
                         method="update",
                         args=[{"visible": []},
                               {"title": chartTitle,
                                "annotations": []}]),
                    dict(label="High",
                         method="update",
                         args=[{"visible": []},
                               {"title": chartTitle,
                                "annotations": upAn}]),
                    dict(label="Low",
                         method="update",
                         args=[{"visible": []},
                               {"title": chartTitle,
                                "annotations": dnAn}]),
                    dict(label="All",
                         method="update",
                         args=[{"visible": []},
                               {"title": chartTitle,
                                "annotations": upAn + dnAn}])
                ]),
            ),
            dict(
                type="buttons",
                name="Lines",
                direction="right",
                active=0,
                x=0.8,
                y=1.05,
                buttons=list([
                    dict(label="None ",
                         method="update",
                         args=[{"visible": []},
                               {"title": chartTitle,
                                "shapes": []}]),
                    dict(label="Level Lines",
                         method="update",
                         args=[{"visible": []},
                               {"title": chartTitle,
                                "shapes": lines}]),
                    dict(label="Rosh Hashona",
                         method="update",
                         args=[{"visible": []},
                               {"title": chartTitle,
                                "shapes": rhSh}]),
                    dict(label="All Lines",
                         method="update",
                         args=[{"visible": []},
                               {"title": chartTitle,
                                "shapes": lines + rhSh}])
                ])
            )
        ])

    # Adding the Rosh Hashona lines
    # top = df['level'].max()
    dfmin['rhannote'] = [roshHashLine(x) for x in dfmin['roshhash']]

    fig = addBolAvatar(fig)
    # fig.update_xaxes(range=[firstYear, lastYear], fixedrange=False)
    fig.update_yaxes(range=[histMin-.1,
                            upperRedLine+.1], fixedrange=False)
    fig.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ))
    fig = addRangeSlider(fig, df)

    fig.update_layout(
        xaxis_title=xAxesTitle,
        yaxis_title=yAxesTitle
    )

    # fig.update_layout(autosize = True, height = 1080, width =1920)
    fold = 'brianoflondon_site'
    file = 'kinneret_level'
    fileHtml = gnr.relFileName(fold,file,'html')
    filePng = gnr.relFileName(fold,file,'png')
    pio.write_html(
        fig, file=fileHtml, auto_open=True)
    fig.write_image(filePng,
                    engine="kaleido", width=1920, height=1080)
    # chartStudioCreds()

    return df


def addBolAvatar(fig):
    """ Adds avatar image to bottom left of graph """
    fig.add_layout_image(
        dict(
            source="https://i1.wp.com/brianoflondon.me/blog/wp-content/uploads/2019/01/cropped-Brian-of-London-with-sig-600x600.png?w=250&ssl=1",
            xref="paper", yref="paper",
            x=0.1, y=0.05,
            sizex=0.2, sizey=0.2,
            xanchor="left", yanchor="bottom"
        )
    )
    return fig


def drawChangesGraph(df=None, period=7):
    """ Draws a graph of the change over the last period days """
    periods = [1, 7, 30, 60, 365]
    # periods = [1]
    if df is None:
        df = setupDataFrames(dateFr='2015-1-1')

    figch = go.Figure()
    i = 0
    for p in periods:
        dCol = f'{p}day'
        df[dCol] = df['level'].diff(periods=-period) * 100         
        figch = addChangeTriangles(figch, False, df, p)
        # vis[]
    if 365 in periods:
        dateOff = pd.DateOffset(years=-1)
        df['365day'] = [100 * getLevelDelta(df, i, dateOff) for i in df.index]
    titleTxt = f"Kinneret Water Level {p} Day change (cm)<br>{todayDate:%d %b %Y}<br>by <a href='https://brianoflondon.me/kinneret'>Brian of London (back to main site)</a>"

    figch.update_layout(title=titleTxt,
                        legend=dict(
                            x=0.90),
                        yaxis_title=f'{period} Day Change (cm)')

    figch = addBolAvatar(figch)
    figch = addRangeSlider(figch, df)
    # figch.show()

    # tr3 = [True] * 3
    # fl3 = [False] * 3
    # matrix = []
    leng = len(periods)
    matrix = [[False] * leng*3 for _ in range(leng)]
    for i in range(0, leng):
        for c in range(i*3, i*3+3):
            matrix[i][c] = True

    # matrix.append(tr3 + fl3 + fl3)
    # matrix.append(fl3 + tr3 + fl3)
    # matrix.append(fl3 + fl3 + tr3)
    # matrix.append(tr3 + tr3 + tr3)

    # plotly.graph_objs.layout.updatemenu.Button
    butts = []
    i = 0

    for p in periods:
        titleTxt = f"Kinneret Water Level {p} Day change (cm)<br>{todayDate:%d %b %Y}<br>by <a href='https://brianoflondon.me/kinneret'>Brian of London (back to main site)</a>"

        thisBut = go.layout.updatemenu.Button(
            label=f"{p} Day",
            method="update",
            args=[{"visible": matrix[i]},
                  {"title": titleTxt}]
        )
        butts.append(thisBut)
        i += 1

    figch.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                name="Markers",
                direction="right",
                active=0,
                x=0.6,
                y=1.05,
                buttons=butts
            )]
    )
    # figch_data_Scatter.update_layout(visible=matrix[0])
    figch.update_traces(visible=False)
    figch.update_traces(visible=True,
                        selector=dict(meta=1))
    # figch.scatter.update_layout(visible=matrix[0])

    fold = 'brianoflondon_site'
    file = 'changes'
    fileHtml = gnr.relFileName(fold,file,'html')
    filePng = gnr.relFileName(fold,file,'png')
    
    pio.write_html(
        figch, file=fileHtml, auto_open=True)
    figch.write_image(filePng, engine="kaleido",
                      width=1920, height=1080)


def addChangeTriangles(figch, plotLevel=True, df=None, period=7):
    """ takes a fig object and adds up down triangles in a colour scale according to 7 day
        change ploting out the level of the lake 
        If plotLevel is true plot the points at the right level, else
        produce a change graph"""
    plotInterpolated = False
    dCol = f'{period}day'
    if df is None:
        df = setupDataFrames(dateFr='2010-1-1')


    df[dCol] = df['level'].diff(periods=-period) * 100

    df['hovtext'] = [f'{period} day change<br>{lv:.3f}m {ch:.1f}cm<br>{d:%d %b %Y}<extra></extra>' for (
        lv, ch, d) in zip(round(df['level'], 3), df[dCol], df.index)]

    filtUp = ((df[dCol] > 0) & (df['real']))
    filtLv = ((df[dCol] == 0) & (df['real']))
    filtDn = ((df[dCol] < 0) & (df['real']))
    filtIn = (df['real'] == False)               # Interpolated points

    if plotLevel is True:
        yValsU = df[filtUp]['level']
        yValsL = df[filtLv]['level']
        yValsD = df[filtDn]['level']
        yValsI = df[filtIn]['level']
    else:
        yValsU = df[filtUp][dCol]
        yValsL = df[filtLv][dCol]
        yValsD = df[filtDn][dCol]
        yValsI = df[filtIn][dCol]
    colU = df[filtUp][dCol]
    colD = df[filtDn][dCol]

    mSize = 12  # Marker Size
    figch.add_trace(go.Scatter(x=df[filtUp].index, y=yValsU,
                               visible = False,
                               meta=period,
                               text=df[filtUp]['hovtext'],
                               hovertemplate='%{text}',
                               marker_symbol='triangle-up',
                               name=f'{period} Day Up',
                               showlegend=False,
                               mode='markers',
                               marker=dict(size=mSize,
                                           colorscale=blueUp,
                                           reversescale=False,
                                           showscale=True,
                                           color=colU,
                                           colorbar=dict(x=0.98, y=.73,
                                                         len=0.5, title=f'{period} Day<br>Change<br>(cm)')
                                           )
                               ))
    figch.add_trace(go.Scatter(x=df[filtLv].index, y=yValsL,
                               visible = False,
                               meta=period,
                               text=df[filtLv]['hovtext'],
                               hovertemplate='%{text}',
                               marker_symbol='hexagram',
                               name='No Change',
                               showlegend=False,
                               mode='markers',
                               marker=dict(size=mSize,
                                           color='white',
                                           line=dict(
                                               color='#0036B2',
                                               width=2
                                           )
                                           )
                               ))
    figch.add_trace(go.Scatter(x=df[filtDn].index, y=yValsD,
                               visible=False,
                               meta=period,
                               text=df[filtDn]['hovtext'],
                               hovertemplate='%{text}',
                               marker_symbol='triangle-down',
                               name=f'{period} Day Down',
                               showlegend=False,
                               mode='markers',
                               marker=dict(size=mSize,
                                           # cmax = 0,
                                           # cmin = -0.2,
                                           colorscale=redDn,
                                           reversescale=True,
                                           showscale=True,
                                           color=colD,
                                           colorbar=dict(x=0.98, y=.23,
                                                         len=0.5))
                               ))
    if plotInterpolated :
        # Interpolated points
        figch.add_trace(go.Scatter(x=df[filtIn].index, y=yValsI,
                                visible = False,
                                meta=period,
                                text=df[filtIn]['hovtext'],
                                hovertemplate='%{text}',
                                marker_symbol='circle',
                                name='No Change',
                                showlegend=False,
                                mode='markers',
                                marker=dict(size=mSize *0.5,
                                            color='white',
                                            line=dict(
                                                color='#0036B2',
                                                width=2
                                            )
                                            )
                                ))
    return figch

def uploadGraphs():
    """ Upload the graphs to brianoflondon.me using SFTP """
    sftp = pysftp
    sftp = connectSFTP()
    fold = 'brianoflondon_site'
    with sftp:
        sftp.cwd('public_html/kinneret')
        for filen in glob.glob(f'{fold}/*'):
            sftp.put(filen)
    sftp.close()
    

# def createChangeMarkerTemplate():
#     """ Creates the marker templates for the Up, Level and Down change
#         triangles """
#     cTemp = go.layout.Template()
#     cTemp.data.scatter = [go.Scatter(marker=dict(size=10,
#                                                 colorscale=blueUp,
#                                                 reversescale=False,
#                                                 showscale=True,
#                                                 color=colU,
#                                                 colorbar=dict(x=0.98, y=.73,
#                                                                 len=0.5, title=f'{period} Day<br>Change<br>(cm)')
#                                            )


#     )]


blueUp = [[0, 'rgb(199, 68, 124)'],
          [0.3, 'rgb(17, 92, 165)'],
          [0.3, 'rgb(17, 92, 165)'],
          [1.0, 'rgb(5, 48, 107)']]

redDn = [[0, 'rgb(199, 68, 124)'],
         [0.8, 'rgb(252, 128, 97)'],
         [0.8, 'rgb(252, 128, 97)'],
         [1.0, 'rgb(104, 0, 12)']]

if __name__ == "__main__":

    # df = setupDataFrames()

    # dateOff = pd.DateOffset(years=-2)
    # oldLevel = getLevelDelta(df,df.index[0],dateOff)
    # print(df.iloc[0]['level'],oldLevel)

    # print(df)
    # print(df.describe())

    df = drawKinGraph()
    drawChangesGraph(df)
    uploadGraphs()
    # drawChangesGraph(period=7)
    # drawChangesGraph(period=1)
    # drawChangesGraph(period=30)
