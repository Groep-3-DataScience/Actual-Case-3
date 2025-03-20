import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import plotly.express as px

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
fig = px.scatter(
    fiets_weer_data,
    x='tavg', 
    y='Total Rentals',
    hover_data=['Date'],
    labels={'tavg': 'Gemiddelde Temperatuur (°C)', 'Total Rentals': 'Aantal Fietsverhuur per Dag'},
    title='Correlatie tussen Weer en Fietsverhuur'
)
st.plotly_chart(fig)

###################################################################################################################################
####################################### ________________________________________________________ ##################################
# Laad de bestanden
df_cyclestations = pd.read_csv('cycle_stations.csv')
bestanden = ['2021_Q2_Central.csv', '2021_Q3_Central.csv', '2021_Q4_Central.csv']
fiets_data_jaar = pd.concat([pd.read_csv(file) for file in bestanden], ignore_index=True)

# Zet de Unix timestamp om naar een datum in 'dd-mm-yyyy' formaat
df_cyclestations['installDateFormatted'] = pd.to_datetime(df_cyclestations['installDate'], unit='ms').dt.strftime('%d-%m-%Y')

# Weerdata en metrodata zijn geladen, maar niet nodig voor de map zelf.
# We gaan nu een interactieve map maken met de fietsstations.

# Create Streamlit app layout
st.title('London Cycle Stations')
st.markdown("Interaktive map met fietsverhuurstations in Londen")

# Voeg een slider toe om het aantal fietsen in te stellen
bike_slider = st.slider("Selecteer het aantal beschikbare fietsen", 0, 100, 0)

# Maak een basemap van Londen
m = folium.Map(location=[51.5074, -0.1278], zoom_start=12)

# MarkerCluster om stations te groeperen
marker_cluster = MarkerCluster().add_to(m)

# Voeg de stations toe aan de kaart
for index, row in df_cyclestations.iterrows():
    lat = row['lat']
    long = row['long']
    station_name = row['name']
    nb_bikes = row['nbBikes']  # Aantal fietsen
    nb_standard_bikes = row['nbStandardBikes']  # Aantal standaardfietsen
    nb_ebikes = row['nbEBikes']  # Aantal ebikes
    install_date = row['installDateFormatted']  # De geformatteerde installatiedatum
    

    # Voeg een marker toe met info over het station
    if nb_bikes >= bike_slider:  # Controleer of het aantal fietsen groter of gelijk is aan de slider
        folium.Marker(
            location=[lat, long],
            popup=folium.Popup(f"Station: {station_name}<br>Aantal fietsen: {nb_bikes}<br>Standaard: {nb_standard_bikes}<br>EBikes: {nb_ebikes}<br>Installatiedatum: {install_date}", max_width=300),
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(marker_cluster)

# Render de kaart in de Streamlit app
folium_static(m)

###################################################################################################################################
