import dash                                     # import dash
import dash_core_components as dcc              # import core components
import dash_html_components as html             # import html components
from dash.dependencies import Input, Output     # import package for interactivity
import pandas as pd                             # import pandas
from collections import Counter                 # import Counter for frequency counting
import dash_bootstrap_components as dbc         # import bootstrap component of dash
import dash_cytoscape as cyto                   # import dash_cytoscape for drawing network
import networkx as nx                           # import networkx for processing graphs
import base64
import io
import sys
from ReAudio_group import ReAudio
import json
from etherLogAnalyzer import etherLogAnalyzer
import plotly.graph_objs as go

#
user_selector=[]
time_scale=0
def generateElements(edge_list,sp_time):

    total_sp = sum(sp_time.values())
    ele=[]
    G = nx.Graph()
    for edge in edge_list:

    # Check if the current edge already exist or not
        if G.has_edge(edge[0],edge[1]):

            # Get the weight of that edge
            w = G[edge[0]][edge[1]]['weight']

            # Remove it from the graph
            G.remove_edge(edge[0],edge[1])

            # Add it again with updated weight
            G.add_edge(edge[0],edge[1],weight=w+1)

        else:

            # If edge doesn't exist in the graph then add it with weight .5
            G.add_edge(edge[0],edge[1],weight=1)
    total_edges = len(edge_list)
    for n in list(G):
        user = 'User-'+str(n)
        speak_ratio = 200*sp_time[n]/total_sp
        t = {'id':n,'label':user,'width':speak_ratio}
        ele.append({'data':t})
    for e in G.edges:
        t = {'source':e[0],'target':e[1],'weight':G[e[0]][e[1]]['weight']*(30/total_edges)}
        ele.append({'data':t})

    return ele

app = dash.Dash(__name__,external_stylesheets=["/assets/bootstrap.css","/assets/plot.css"])
file_name = ""

error_flag = False
if len(sys.argv)!=2:

    print('Error: You have not specified the file name')
    print("Usage: python speech_analyzer.py csv-file-name")
    sys.exit()
else:
    file_name = sys.argv[1]
    try:
        org_df = pd.read_csv(file_name,names=['group','timestamp','direction'])
    except Exception as e:
        print('Error:',str(e))
        sys.exit
## log analyzer code




user_df = {}





# log analyzer code ends
df = org_df.loc[org_df.group == 'group-1',:]
re = ReAudio(file_name)

group_options = []
groups =  re.getGroups()

for group in groups:
    group_options.append({'label':group,'value':group})



sp_time = re.getSpeakingTime(plot=False,group='group-1')

edge_list = re.generateEdgeFile('group-1')
elements = generateElements(edge_list,sp_time)
print("---------ELEMENTS----",elements)

figure_data1=[]
final_df = re.generateWindowWiseSpeakingTime(window_size="30S",group='group-1')
for i in range(4):
    user='u%d_speak'%(i+1)
    user_label = 'User-%d'%(i+1)
    figure_data1.append({'x':final_df['timestamp'],'y':final_df[user],'type':'bar','name':user_label})


dfreq = Counter(df['direction'])

directions=  df['direction'].unique()

freq = []
for dir in directions:
    c = df.loc[df['direction']==dir,:].shape[0]

    freq.append(c)

sp_user = [user for user in sp_time.keys()]
sp_duration = [sp for sp in sp_time.values()]

body = dbc.Container(
    [   dbc.Row([
            dbc.Col([
                html.H1("Speech Analyzer"),
                html.P("This web-app offers visualization of data collected from ReSpeaker (attached with Rapsberry Pi) and Etherpad Usage"),
                html.P("For processing audio data, we used Voice Activity detection (VAD) and Direction of Arrival (DoA) algorithms to detect the voice activity and it's direction of arrival."+
                " For Etherpad, we developed a plugin which allowed us to track participants' activities. "+
                "We mainly recorded the ip-address of the participant interacting with Etherpad along with the changes, he/she making in the pad"),
                html.P("For development of this dashboard, we used Python dash Framework and utilized Bootstrap for styling of the page."),
                html.P("**Tallinn University**")
            ])
        ]),
        html.H4("Select your group"),
        dcc.Dropdown(
            id='group-selector',
            options=group_options,
            value=groups[0]
        ),

        html.Hr(),
        html.H1(id='title'),
        dbc.Row([
            dbc.Col([
                html.H3("Direction of Arrival"),
                html.P("DoA (Direction of Arrival) represents the direction from which sound is detected by Raspberry prototype. DoA distribution (right figure) shows the freqeuncy of direction detected during recording. "),
                html.P("Voice activity detection (VAD) and Direction of Arrival (DoA) algorithms are used to detect voice and it's direction.")
            ],md=4),
            dbc.Col([
                html.H3("DoA  Distribution"),
                dcc.Graph(id='doa')
            ],md=8)
        ]),
        dbc.Row([
            html.H3("Speaking Time")
        ]),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='spk',
                figure={
                    'data':[
                        {'x':sp_user,'y':sp_duration,'type':'bar','name':'Speaking Time'}
                    ],
                    'layout':go.Layout(
                        xaxis={'title': 'User'},
                        yaxis={'title': 'Speaking Time (sec.)'},
                        margin={'l': 40, 'b': 40, 't': 10, 'r': 40},



                    )

                })
            ],md=5),
            dbc.Col([
                html.H3("How speaking time is computed?"),
                html.P("First of all, DoA distribution is computed (shown in above figure). From the distribution, frequent occuring directions are retrieved. Then these directions are processed to filter out a direction if it is close to another direction. Out of these, four directions are then extracted and assigned to users in clockwise."),
                html.P("Additionally, it also assume that speaker does not move while speaking.")
            ])

        ]),
        dbc.Row([
            html.H3("Group Dynamics"),
            html.P(elements)
        ]),
        dbc.Row([
            cyto.Cytoscape(
                id='sna',
                elements=elements,
                style={'width': '600%', 'height': '350px'},
                layout={
                    'name': 'circle'
                },
                stylesheet=[
                    {
                        'selector':'node',
                        'style':{
                            'label':'data(label)',
                            'width':'data(width)',
                            'height':'data(width)'

                        }
                    },
                    {
                        'selector': '[weight]',
                        'style':{
                            'width':'data(weight)'

                        }

                    }

                ]
            )

        ]),
        html.H3("Speaking behavior over time"),
        html.P("You can select the time duration within which you want explore the speaking behavior."),

        dbc.Row([
            dbc.Col([
                dcc.Graph(id='speech_graph_time',
                figure={
                    'data':figure_data1,
                    'layout':go.Layout(
                        xaxis={'title': 'Timestamp'},
                        yaxis={'title': 'Speaking Time(Sec)'},
                        margin={'l': 40, 'b': 40, 't': 10, 'r': 40},
                    )

                })
                ],md=10)
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Slider(
                id='window',
                min=0,
                max=10,
                step=None,
                marks = {
                    0 : '30Sec',
                    1 : '60Sec',
                    2 : '2Min',
                    3 : '5Min',
                    4 : '15Min',
                    5 : '30Min',
                    6 : '60Min',
                    7 : '2Hr'
                },
                value = 0

                )

            ])

        ]),
        html.Hr(),
        html.Hr(),

    ])

app.layout = html.Div([body])

@app.callback(Output('doa','figure'),[Input('group-selector','value')])
def update_doa(group_value):

    df = re.getGroupFrame(group_value)
    directions=  df['degree'].unique()

    freq = []
    for dir in directions:
        c = df.loc[df['degree']==dir,:].shape[0]
        freq.append(c)
    figure={
        'data':[
            {'x':directions,'y':freq,'type':'bar','name':'DoA distribution for '+group_value}
        ],
        'layout':go.Layout(
            xaxis={'title': 'Direction of Arrival (In degree)'},
            yaxis={'title': 'Frequency'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 40},
        )
    }
    return figure

@app.callback(Output('spk','figure'),[Input('group-selector','value')])
def update_spk(group_value):
    sp_time = re.getSpeakingTime(plot=False,group=group_value)
    sp_user = [user for user in sp_time.keys()]
    sp_duration = [sp for sp in sp_time.values()]
    figure={
        'data':[
            {'x':sp_user,'y':sp_duration,'type':'bar','name':'Speaking Time'}
        ],
        'layout':go.Layout(
            xaxis={'title': 'User'},
            yaxis={'title': 'Speaking Time (sec.)'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 40},



        )

    }
    return figure

@app.callback(Output('sna','elements'),[Input('group-selector','value')])
def update_sna(group_value):
    sp_time = re.getSpeakingTime(plot=False,group=group_value)
    edge_list1 = re.generateEdgeFile(group_value)
    #elements1 = generateElements(edge_list,sp_time)
    total_sp = sum(sp_time.values())
    ele=[]
    G = nx.Graph()
    for edge in edge_list:

    # Check if the current edge already exist or not
        if G.has_edge(edge[0],edge[1]):

            # Get the weight of that edge
            w = G[edge[0]][edge[1]]['weight']

            # Remove it from the graph
            G.remove_edge(edge[0],edge[1])

            # Add it again with updated weight
            G.add_edge(edge[0],edge[1],weight=w+1)

        else:

            # If edge doesn't exist in the graph then add it with weight .5
            G.add_edge(edge[0],edge[1],weight=1)
    total_edges = len(edge_list)
    for n in list(G):
        user = 'User-'+str(n)
        speak_ratio = 200*sp_time[n]/total_sp
        t = {'id':n,'label':user,'width':speak_ratio}
        ele.append({'data':t})
    for e in G.edges:
        t = {'source':e[0],'target':e[1],'weight':G[e[0]][e[1]]['weight']*(30/total_edges)}
        ele.append({'data':t})

    return ele
#return str(elements1)

@app.callback(Output('speech_graph_time', 'figure'),
              [Input('window', 'value'),Input('group-selector','value')])
def display_value(value,group_value):

    time_window={0:'30S',1:'60S',2:'2T',3:'5T',4:'15T',5:'30T',6:'60T',7:'120T'}
    figure_data=[]
    time = 'sec'
    if value > 0 and value < 6:
        time = 'min'
    elif value >5 :
        time = 'hour'
    final_df = re.generateWindowWiseSpeakingTime(window_size=time_window[value],time=time,group=group_value)
    for i in range(4):
        user='u%d_speak'%(i+1)
        user_label = 'User-%d'%(i+1)

        figure_data.append({'x':final_df['timestamp'],'y':final_df[user],'type':'bar','name':user_label})
    figure={
        'data':figure_data,
        'layout':go.Layout(
            xaxis={'title': 'Timestamp'},
            yaxis={'title': 'Speaking Time ('+time+')'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 40},
        )

    }
    return figure



if __name__ == '__main__':
    app.run_server(debug=False)
