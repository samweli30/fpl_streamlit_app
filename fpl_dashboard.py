# Import Packages
#===========================
import requests
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import os

# Access the fantasy premier league API 
# API access example https://towardsdatascience.com/fantasy-premier-league-value-analysis-python-tutorial-using-the-fpl-api-8031edfe9910
#============================
url='https://fantasy.premierleague.com/api/bootstrap-static/'
r=requests.get(url)
json=r.json()

# Creating dataframes from the API json
#=============================
elements_df = pd.DataFrame(json['elements'])
elements_types_df = pd.DataFrame(json['element_types'])
teams_df = pd.DataFrame(json['teams'])
phases_df = pd.DataFrame(json['phases'])
events_df = pd.DataFrame(json['events'])

# Create slim dataframe for fpl
slim_elements_df = elements_df[['first_name','web_name','team','element_type','selected_by_percent',
                                'now_cost','minutes','transfers_in','transfers_out','bonus',
                                'goals_scored','goals_conceded','assists','clean_sheets','saves','bps',
                                'influence','creativity','threat','ict_index','own_goals','penalties_saved',
                                'direct_freekicks_order','corners_and_indirect_freekicks_order','penalties_order',
                                'penalties_missed','value_season','points_per_game','total_points']]

# Change data type of some columns to float 
slim_elements_df['selected_by_percent'] = slim_elements_df.selected_by_percent.astype(float)
slim_elements_df['influence'] = slim_elements_df.influence.astype(float)
slim_elements_df['creativity'] = slim_elements_df.creativity.astype(float)
slim_elements_df['threat'] = slim_elements_df.threat.astype(float)
slim_elements_df['ict_index'] = slim_elements_df.ict_index.astype(float)
slim_elements_df['points_per_game'] = slim_elements_df.points_per_game.astype(float)

# Position, Team and Value mapping
slim_elements_df['position'] = slim_elements_df.element_type.map(elements_types_df.set_index('id').singular_name)
slim_elements_df['team'] = slim_elements_df.team.map(teams_df.set_index('id').name)
slim_elements_df['value'] = slim_elements_df.value_season.astype(float)
slim_elements_df.sort_values('value',ascending=False).head(5)

# filter players to remove players with 0 points all season
slim_elements_df = slim_elements_df.loc[slim_elements_df.value > 0]

# Streamlit app
#================
# Title and Side Bar Setup
st.set_page_config(layout="wide")
st.title('2022/2023 FPL Dashboard ⚽')
st.markdown('This dashboard will aid in player selection of my FPL team to maximise on my points for the 2022/2023 season.')
st.markdown('Selecting the best players for the team require an understanding of the relationship between the value, cost and transfers of a specific player.')
st.sidebar.title('Filters')
st.sidebar.markdown('Filter by Position, Team, Value and Cost')

df=slim_elements_df

# Create Position Dropdown
position_list = list(pd.unique(df['position']))
l2=[]
l2=position_list[:]
l2.append('Select all')
position_dropdown = st.sidebar.multiselect('Position',l2,default="Select all")

if 'Select all' in position_dropdown :
	position_dropdown=position_list

# Create Team Dropdown
team_list = list(pd.unique(df['team']))
m2=[]
m2=team_list[:]
m2.append('Select all')
team_dropdown = st.sidebar.multiselect('Team',m2,default="Select all")

if 'Select all' in team_dropdown :
	team_dropdown=team_list

# Slider for Player Value
select2=st.sidebar.slider("Value",min_value=(min(df['value'])),
                          max_value=(max(df['value'])),
                          value=(min(df['value']),max(df['value'])))

# Slider for Player Cost
select3=st.sidebar.slider("Cost",min_value=(min(df['now_cost'])),
                          max_value=(max(df['now_cost'])),
                          value=(min(df['now_cost']),max(df['now_cost'])))

# Create a filtered dataframe based on the sliders
#----------------------------------
df_filtered=df.loc[(df['position'].isin(position_dropdown))
                   &(df['team'].isin(team_dropdown))
                   & (df['value']<=select2[1]) & (df['value']>=select2[0])
                   &(df['now_cost']<=select3[1]) & (df['now_cost']>=select3[0])]

# Streamlit plots and metric plots
#----------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("MVP Player", str(df_filtered.loc[df_filtered.value==max(df_filtered.value),"web_name"].iloc[0]))
col2.metric("MVP Value", str(max(df_filtered.value)))
col3.metric("MVP Team", str(df_filtered.loc[df_filtered.value==max(df_filtered.value),"team"].iloc[0]))
col4.metric("MVP Cost", "$"+str(df_filtered.loc[df_filtered.value==max(df_filtered.value),"now_cost"].iloc[0]))

position_scatter= px.scatter(df_filtered,x=df_filtered.now_cost,
                             y=df_filtered.total_points,
                             hover_data=[df_filtered.web_name],
                             color=df_filtered.team,
                             size=df_filtered.value,
                             labels={"now_cost":"Player Cost", 
                                     "total_points":"Total Points"})
position_scatter.add_hline(y=np.mean(df_filtered.total_points),line_width=3,line_dash="dash",line_color="green")
position_scatter.add_vline(x=np.mean(df_filtered.now_cost),line_width=3,line_dash="dash",line_color="blue")

position_scatter.update_layout( title={'text': "<b>Player Points by Cost</b>",
                                       'y':0.95,
                                       'x':0.5,
                                       'xanchor': 'center',
                                       'yanchor': 'top',
                                       'font_size':24})
st.plotly_chart(position_scatter)

st.markdown('This section will show the player popularity by assessing transfers in and out.')
col5, col6, col7, col8 = st.columns(4)
col5.metric("Most Popular Player", str(df_filtered.loc[df_filtered['selected_by_percent']==max(df_filtered['selected_by_percent']),"web_name"].iloc[0]))
col6.metric("Most Selected %",str(max(df_filtered['selected_by_percent']))+"%")
col7.metric("Most Transfered In Player", str(df_filtered.loc[df_filtered['transfers_in']==max(df_filtered['transfers_in']),"web_name"].iloc[0]))
col8.metric("Most Transfered Out Player", str(df_filtered.loc[df_filtered['transfers_out']==max(df_filtered['transfers_out']),"web_name"].iloc[0]))

df_filtered.net_transfers=df_filtered.transfers_in-df_filtered.transfers_out

position_scatter1= px.scatter(df_filtered,
                              x=df_filtered.selected_by_percent,
                              y=df_filtered.net_transfers,
                              hover_data=[df_filtered.web_name],
                              color=df_filtered.team,
                              size=df_filtered.value,
                              labels={"y":"Net Transfers",
                                      "selected_by_percent":"Selected By %"})

position_scatter1.update_layout( title={'text': "<b>Player Transfers and Popularity</b>",
                                       'y':0.95,
                                       'x':0.5,
                                       'xanchor': 'center',
                                       'yanchor': 'top',
                                       'font_size':24})

st.plotly_chart(position_scatter1)

st.markdown('This section will analyse bonus points and correlation with goals + assists')

bonus_x = st.selectbox('Select column for Bonus Analysis',
                       ('goals_scored', 'goals_conceded', 'assists','clean_sheets', 'saves', 'own_goals', 'penalties_saved'))

position_scatter2= px.scatter(df_filtered,
                              x=df_filtered[bonus_x],
                              y=df_filtered.bonus,
                              hover_data=[df_filtered.web_name,df_filtered.total_points],
                              color=df_filtered.team,
                              size=df_filtered.total_points)

position_scatter2.update_layout( title={'text': "<b>Bonus Points</b>",
                                       'y':0.95,
                                       'x':0.5,
                                       'xanchor': 'center',
                                       'yanchor': 'top',
                                       'font_size':24})

st.plotly_chart(position_scatter2)