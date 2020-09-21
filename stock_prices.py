import dash
import dash_core_components as dcc
import dash_html_components as html
import flask
import plotly.express as px
import dash_table
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output
import requests
from datetime import datetime, timedelta
import os

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, requests_pathname_prefix='/dash_stocks/', external_stylesheets=external_stylesheets)

def get_prices(symbol, days):
    apikey = os.environ.get('apikey')
    url = 'https://fmpcloud.io/api/v3/historical-price-full/'+ symbol +'?timeseries=' + str(days) + '&apikey='+ apikey
    data = requests.get(url).json()
    df = pd.json_normalize(data, record_path='historical')
    df['symbol'] = data['symbol']
    df['date'] = df['date'].astype('datetime64')
    df = (df
          .sort_values('date', ascending=True)
          .set_index('date'))
    df['delta'] = df['changeOverTime']
    df.loc[df.index == df.index.min(), 'delta'] = np.NaN
    df['change_indexed'] = 100*np.exp(np.nan_to_num(df['delta'].cumsum()))
    return df

symbols = ['NN.AS', 'ASRNL.AS', 'AGN.AS']
column_list = ['open', 'high', 'low', 'close', 'adjClose', 'volume',
       'unadjustedVolume', 'change', 'changePercent', 'vwap', 'label',
       'changeOverTime', 'symbol', 'indexed']
df = pd.DataFrame(columns=column_list)
for symbol in symbols:
    data = get_prices(symbol, days=365)
    df = pd.concat([df, data])


numdate= [x for x in range(len(df.index.unique()))]
date_dict = {numd:date.strftime('%d/%m/%y') for numd,date in zip(numdate, df.index.unique())}

fig = px.line(df, x=df.index, y='adjClose', color='symbol')

app.layout = html.Div(children=[
    html.H1(children='A tiny stock dashboard'),

    html.Div(children='''
        Source: fmpcloud.io
    '''),
    
    dcc.Dropdown(
        id='demo-dropdown',
        options=[
            {'label': 'Adjusted close prices', 'value': 'adjClose'},
            {'label': 'Reindexed close prices', 'value': 'change_indexed'},
        ],
        value='adjClose',
    ),

    dcc.Dropdown(
        id='demo-dropdown2',
        options=[
            {'label': 'Aegon', 'value': 'AGN.AS'},
            {'label': 'ASR', 'value': 'ASRNL.AS'},
            {'label': 'NN', 'value': 'NN.AS'}
        ],
        value=['AGN.AS', 'ASRNL.AS', 'NN.AS'],
        multi=True
    ),  
    dcc.Graph(id='g1', figure=fig),
    dcc.DatePickerRange(
        id='my-date-picker-range',
        display_format='DD-MM-YYYY',
        min_date_allowed=df.index.min().to_pydatetime(),
        max_date_allowed=df.index.max().to_pydatetime(),
        initial_visible_month=df.index.min().to_pydatetime(),
        start_date=df.index.min().to_pydatetime(),
        end_date=df.index.max().to_pydatetime()
    )

])

@app.callback(
    dash.dependencies.Output('g1', 'figure'),
    [dash.dependencies.Input('demo-dropdown', 'value'),
    dash.dependencies.Input('demo-dropdown2', 'value'),
    dash.dependencies.Input('my-date-picker-range', 'start_date'),
    dash.dependencies.Input('my-date-picker-range', 'end_date')])
def update_graph(value, sel_companies, start_date, end_date):
    selected = df['symbol'].isin(sel_companies)
    try: 
        df.loc[start_date].index[0]
    except IndexError:
        start_date = df.loc[df.index > start_date].first('1D')
    try:
        if (selected.value_counts().index[0] == True) or (selected.value_counts().index[1]) == True:
            if value == 'change_indexed':
                # recalculate base as 100 and change
                df['delta'] = df['changeOverTime'] 
                df.loc[df.index == str(start_date), 'delta'] = np.NaN
                df.loc[df.index == str(start_date), 'change_indexed'] = 100
                for symbol in sel_companies: 
                    df.loc[((df.index > str(start_date)) & (df.index <= str(end_date)) & (df['symbol'] == symbol)), 'change_indexed'] = 100*np.exp(np.nan_to_num(df.loc[((df.index > str(start_date)) & (df.index <= str(end_date)) & (df['symbol'] == symbol)), 'delta'].cumsum()))
                    filtered_df = df[df['symbol'].isin(sel_companies)].loc[str(start_date):str(end_date)]
                fig = px.line(filtered_df, x=filtered_df.index, y=value, color='symbol')
                return fig
            else:
                filtered_df = df[df['symbol'].isin(sel_companies)].loc[str(start_date):str(end_date)]
                fig = px.line(filtered_df, x=filtered_df.index, y=value, color='symbol')
                return fig
    except:
        filtered_df = df
        fig = px.line(filtered_df, x=filtered_df.index)
        return fig