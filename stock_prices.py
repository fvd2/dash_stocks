import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import dash_table
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output
import requests
from datetime import date

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

def get_prices(symbol, days):
    apikey = '16469a8ae9b8895e2c4cd7f2bcd69062'
    url = 'https://fmpcloud.io/api/v3/historical-price-full/'+ symbol +'?timeseries=' + str(days) + '&apikey='+ apikey
    data = requests.get(url).json()
    df = pd.json_normalize(data, record_path='historical')
    df['symbol'] = data['symbol']
    df['date'] = df['date'].astype('datetime64')
    df = (df
          .sort_values('date', ascending=True)
          .set_index('date'))
    df.loc[df.index == df.index.min(), 'changeOverTime'] = np.NaN
    df['change_indexed'] = 100*np.exp(np.nan_to_num(df['changeOverTime'].cumsum()))
    return df

symbols = ['nn.as', 'asrnl.as', 'agn.as']
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
    dcc.RangeSlider(
        id='rangeslider',
        min=numdate[0],
        max=numdate[-1],
        value=[numdate[0], numdate[-1]],
        marks=date_dict
        ),
    html.Div(id='output-container-range-slider'),
])

@app.callback(
    [dash.dependencies.Output('g1', 'figure'),
    dash.dependencies.Output('output-container-range-slider', 'children')],
    [dash.dependencies.Input('demo-dropdown', 'value'),
    dash.dependencies.Input('demo-dropdown2', 'value'),
    dash.dependencies.Input('rangeslider', 'value')])
def update_graph(value, sel_companies, sel_dates):
    selected = df['symbol'].isin(sel_companies)
    try:
        if selected.unique()[0] or selected.unique()[1] == True:
            filtered_df = df[df['symbol'].isin(sel_companies)].loc[date_dict[sel_dates[0]]:date_dict[sel_dates[1]]]
            fig = px.line(filtered_df, x=filtered_df.index, y=value, color='symbol')
    except: 
        filtered_df = df
        fig = px.line(filtered_df, x=filtered_df.index)
    return fig, print(fig)
        
if __name__ == '__main__':
    app.run_server(port=9050, debug=True)