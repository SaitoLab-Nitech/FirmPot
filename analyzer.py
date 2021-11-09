
#------------------------------------------------
# Import
#------------------------------------------------

import sys
sys.dont_write_bytecode = True

# Data processing
import numpy as np
import pandas as pd

# Flask
import flask

# Dash
import dash
import dash_core_components as dcc 
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# My programs
from utils.parse_log import get_data

#------------------------------------------------
# Data
#------------------------------------------------

if len(sys.argv) < 2:
    print("[!] Usage : python3 analyzer.py [logpath] ...")
    sys.exit(0)

# Access log
access_df = get_data(sys.argv[1:])

total_days = access_df["date"].nunique()
total_src_ips = access_df["src_ip"].nunique()
total_dst_ips = access_df["dst_ip"].nunique()
total_accesses = len(access_df.index)

#------------------------------------------------
# Ranking
#------------------------------------------------

partial_df = access_df.loc[:, ["req_method", "req_path", "req_query", "req_body", "res_id"]]
result = partial_df.groupby(["req_method", "req_path", "req_query", "req_body"], as_index=False).count()

result["rank"] = result["res_id"].rank(method='max', ascending=False).astype(int) # new column
result = result.sort_values("rank")

req_ranking = go.Figure(
    data=[go.Table(
        header=dict(values=["Rank", "Total", "Method", "Path", "Query", "Body"],
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[result["rank"], result["res_id"], result["req_method"], result["req_path"], result["req_query"], result["req_body"]],
                fill_color='lavender',
                align='left'))
])


#------------------------------------------------
# Number of accesses
#------------------------------------------------

partial_df = access_df.loc[:, ["date", "src_ip"]]
result = partial_df.groupby("date").count()

access_chart = go.Figure()

access_chart.add_trace(
    go.Bar(
        x=list(result.index), 
        y=result["src_ip"].values.tolist(),
        name='Number of accesses',
    )
)

observed_ip = []
for date in list(result.index):
    observed_ip.append(partial_df[partial_df.date == date].src_ip.nunique())

access_chart.add_trace(
    go.Scatter(
        x=list(result.index), 
        y=observed_ip,
        name='Number of IP addresses',
        marker=dict(color='#F2274C', size=8, line=dict(color='#b24644', width=1))
    )
)

access_chart.update_layout(height=400, width=1180, showlegend=True,
                                    autosize=False, title_text='Number of accesses')


#------------------------------------------------
# Barh
#------------------------------------------------

max_len = 7
result = partial_df.groupby("src_ip").count() # sesstion length for each client

bar_plot = np.zeros(max_len + 1)
for length in result["date"].values.tolist():
    if length <= max_len:
        bar_plot[length-1] += 1
    else:
        bar_plot[max_len] += 1

band_graph = []
for i in range(max_len):
    band_graph.append(
        go.Bar(
            y=["Session\nLength"], x=[bar_plot[i]],
            name= "Len=" + str(i+1),
            textposition="inside",
            orientation='h',
        )
    )

band_graph.append(
    go.Bar(
        y=["Session\nLength"], x=[bar_plot[max_len]],
        name= "Len>=" + str(max_len+1),
        textposition="inside",
        orientation='h',
    )
)


band_graph_layout = go.Layout(
    title='The length of session',
    barmode='stack',
    height=350,
    width=565*2
)

bar_chart = go.Figure(
    data=band_graph, layout=band_graph_layout, 
)

#------------------------------------------------
# Percentage of request methods
#------------------------------------------------

partial_df = access_df.loc[:, ["req_method", "res_status"]]

result = partial_df.groupby("req_method").count()
labels = list(result.index)
values = result["res_status"].values.tolist()

method_percentage = go.Figure(data=[go.Pie(labels=labels, values=values)])
method_percentage.update_layout(
    title = 'Percentage of request methods',
    height = 365, 
    width = 572,
    polar = dict(radialaxis=dict(visible=True, range=[0, 50])),
    margin = dict(l=10),
    showlegend = True
)

#------------------------------------------------
# Percentage of response status
#------------------------------------------------

result = partial_df.groupby("res_status").count()
labels = list(result.index)
values = result["req_method"].values.tolist()

status_percentage = go.Figure(data=[go.Pie(labels=labels, values=values)])
status_percentage.update_layout(
    title = 'Percentage of response status',
    height = 365, 
    width = 572,
    polar = dict(radialaxis=dict(visible=True, range=[0, 50])),
    margin = dict(l=10),
    showlegend=True
)

#------------------------------------------------
# Percentage of response id
#------------------------------------------------

result = partial_df.groupby("res_status").count()
labels = list(result.index)
values = result["req_method"].values.tolist()

status_percentage = go.Figure(data=[go.Pie(labels=labels, values=values)])
status_percentage.update_layout(
    title = 'Percentage of response status',
    height = 365, 
    width = 572,
    polar = dict(radialaxis=dict(visible=True, range=[0, 50])),
    margin = dict(l=10),
    showlegend=True
)


#------------------------------------------------
# Flask
#------------------------------------------------

server = flask.Flask(__name__)

@server.route('/attackmap')
def index():
    return flask.render_template("attackmap.html")

#------------------------------------------------
# Top page Layout
#------------------------------------------------
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app1 = dash.Dash(name='index', server=server, external_stylesheets=external_stylesheets)
app1.layout = html.Div([

    # ----- Overview -----

    html.Div([
        html.Div([ # block 1
            html.Span(['Total recieved requests', html.Br()]),
            html.Br(),
            html.Img(
                src=app1.get_asset_url("internet.svg"),
                style={"height": "80px", "width": "80px", "margin-bottom": "0px"}),
            html.Br(),
            html.Span(
                total_accesses, style={'font-size': 'xxx-large',
                                    'font-weight': 'bold'}),
            ], style={'background-color': '#ffffff', 'text-align': 'center', 'border-radius': '5px', 'width': '200px',
                              'margin': '10px 10px 0px 10px', 'padding': '15px', 'position': 'relative', 'box-shadow': '4px 4px 4px lightgrey'}),
        html.Div([ # block 2
            html.Span(['Total observed IP addresses', html.Br()]),
            html.Br(),
            html.Img(
                src=app1.get_asset_url("people.svg"),
                style={"height": "80px", "width": "80px", "margin-bottom": "0px"}),
            html.Br(),
            html.Span(
                total_src_ips, style={'font-size': 'xxx-large',
                                    'font-weight': 'bold'}),
            ], style={'background-color': '#ffffff', 'text-align': 'center', 'border-radius': '5px', 'width': '200px',
                              'margin': '10px 10px 0px 10px', 'padding': '15px', 'position': 'relative', 'box-shadow': '4px 4px 4px lightgrey'}),
        html.Div([ # block 3
            html.Span(['Total days observed', html.Br()]),
            html.Br(),
            html.Img(
                src=app1.get_asset_url("calender.svg"),
                style={"height": "80px", "width": "80px", "margin-bottom": "0px"}),
            html.Br(),
            html.Span(
                total_days, style={'font-size': 'xxx-large',
                                    'font-weight': 'bold'}),
            ], style={'background-color': '#ffffff', 'text-align': 'center', 'border-radius': '5px', 'width': '200px',
                              'margin': '10px 10px 0px 10px', 'padding': '15px', 'position': 'relative', 'box-shadow': '4px 4px 4px lightgrey'}),
        html.Div([ # block 4
            html.Span(['Total honeypot servers', html.Br()]),
            html.Br(),
            html.Img(
                src=app1.get_asset_url("honeypot.svg"),
                style={"height": "80px", "width": "80px", "margin-bottom": "0px"}),
            html.Br(),
            html.Span(
                total_dst_ips, style={'font-size': 'xxx-large',
                                    'font-weight': 'bold'}),
            ], style={'background-color': '#ffffff', 'text-align': 'center', 'border-radius': '5px', 'width': '200px',
                              'margin': '10px 10px 0px 10px', 'padding': '15px', 'position': 'relative', 'box-shadow': '4px 4px 4px lightgrey'}),
    ], style={'display': 'flex', 'margin': '0px 0px 30px 0px'}),

    html.Div([

        html.A(
            html.Button('Dashboard', id='btn-nclicks-1', n_clicks=0, 
            style={'background-color': '#ffffff', 'text-align': 'center', 'border-radius': '5px', 'width': '450px',
                   'margin': '10px 10px 0px 10px', 'position': 'relative', 'box-shadow': '4px 4px 4px lightgrey'}),
            href='http://localhost:8050/dashboard'
        ),

        html.A(
            html.Button('Attack Map', id='btn-nclicks-2', n_clicks=0,
            style={'background-color': '#ffffff', 'text-align': 'center', 'border-radius': '5px', 'width': '450px',
                   'margin': '10px 10px 0px 10px', 'position': 'relative', 'box-shadow': '4px 4px 4px lightgrey'}),
            href='http://localhost:8050/attackmap'
        ),

    ], style={'display': 'flex', 'margin': '0px 0px 30px 0px'}),

])

#------------------------------------------------
# Dashboard Layout
#------------------------------------------------

app2 = dash.Dash(name='dashboard', server=server, url_base_pathname='/dashboard/')
app2.layout = html.Div([

    # ----- Acccess num per date -----
    html.Div(
        [dcc.Graph(id='', figure=access_chart),], 
        style={'background-color': '#ffffff', 'text-align': 'center', 'border-radius': '5px 0px 0px 5px', 'height': '400px', 'width': '1185px',
                    'margin': '0px 0px 30px 10px', 'padding': '15px', 'position': 'relative', 'box-shadow': '4px 4px 4px lightgrey',}
    ),

    # ----- Pie charts -----
    html.Div(
        [
            # ----- Request method -----
            html.Div(
                [dcc.Graph(id='', figure=method_percentage),], 
                style={'background-color': '#ffffff', 'text-align': 'center', 'border-radius': '5px 0px 0px 5px', 'height': '350px', 'width': '572px',
                        'margin': '0px 0px 30px 10px', 'padding': '15px', 'position': 'relative', 'box-shadow': '4px 4px 4px lightgrey',}
            ),

            # ----- Response status -----
            html.Div(
                [dcc.Graph(id='', figure=status_percentage),], 
                style={'background-color': '#ffffff', 'text-align': 'center', 'border-radius': '5px 0px 0px 5px', 'height': '350px', 'width': '572px',
                        'margin': '0px 0px 30px 10px', 'padding': '15px', 'position': 'relative', 'box-shadow': '4px 4px 4px lightgrey',}
                ),
        ], style={'display': 'flex'}
    ),

    # ----- Session length -----
    html.Div(
        [dcc.Graph(id='',figure=bar_chart),], 
        style={'background-color': '#ffffff', 'text-align': 'center', 'border-radius': '5px 0px 0px 5px', 'height': '400px', 'width': '1185px',
                'margin': '0px 0px 30px 10px', 'padding': '15px', 'position': 'relative', 'box-shadow': '4px 4px 4px lightgrey',}
    ),

    html.Div(
        [dcc.Graph(id='', figure=req_ranking),], 
        style={'background-color': '#ffffff', 'text-align': 'center', 'border-radius': '5px 0px 0px 5px', 'height': '500px', 'width': '1185px',
                'margin': '0px 0px 30px 10px', 'padding': '15px', 'position': 'relative', 'box-shadow': '4px 4px 4px lightgrey',}
    ),

])




#------------------------------------------------
# if __name__ == '__main__'
#------------------------------------------------

if __name__ == '__main__':
    app1.run_server(debug=True)
