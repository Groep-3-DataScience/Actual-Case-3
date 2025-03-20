import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

fiets_data = pd.read_csv('fietsdata2021_rentals_by_day.csv')
weer_data = pd.read_csv('weather_london.csv', index_col=0)
metro_data = pd.read_csv('AC2021_AnnualisedEntryExit.csv', sep=';')
metro_stations_data = pd.read_csv('London stations.csv')
cyclestations_data = pd.read_csv('cycle_stations.csv')

# 1) Datumkolommen op juiste formaat
# Fietsdata: 'Day' omzetten naar datetime en opslaan als 'Date'
fiets_data['Date'] = pd.to_datetime(fiets_data['Day'])
# Weerdata: index omzetten naar datetime en daarna als kolom opslaan
weer_data.index = pd.to_datetime(weer_data.index, format='%Y-%m-%d', errors='coerce')
weer_data = weer_data.reset_index().rename(columns={'index': 'Date'})

# 2) Controleer op missing values en verwijder die indien nodig
fiets_data.dropna(subset=['Date', 'Total Rentals'], inplace=True)
weer_data.dropna(subset=['Date', 'tavg'], inplace=True)

# 3) Merge de datasets op overlappende data (inner join)
fiets_weer_data = pd.merge(weer_data, fiets_data, on='Date', how='inner')

###################################################################################################################################
####################################### Scatter plot van het weer t.o.v. fietsen gehuurd die dag ##################################
# Bereken de regressielijn met numpy.polyfit
x = fiets_weer_data['tavg']
y = fiets_weer_data['Total Rentals']
slope, intercept = np.polyfit(x, y, 1)

# Genereer een reeks x-waarden voor de lijn
x_line = np.linspace(x.min(), x.max(), 100)
y_line = slope * x_line + intercept

# Maak de scatterplot
fig = px.scatter(
    fiets_weer_data,
    x='tavg', 
    y='Total Rentals',
    hover_data=['Date'],
    labels={'tavg': 'Gemiddelde Temperatuur (°C)', 'Total Rentals': 'Aantal Fietsverhuur per Dag'},
    title='Correlatie tussen Weer en Fietsverhuur'
)

# Voeg de handmatig berekende regressielijn toe
fig.add_trace(go.Scatter(x=x_line, y=y_line, mode='lines', name='Trendline'))

st.plotly_chart(fig)

###################################################################################################################################
####################################### ________________________________________________________ ##################################


###################################################################################################################################
