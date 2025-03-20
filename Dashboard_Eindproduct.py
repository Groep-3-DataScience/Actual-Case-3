import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import plotly.express as px
import geopandas as gpd
from branca.colormap import linear

fiets_data = pd.read_csv('fietsdata2021_rentals_by_day.csv')
weer_data = pd.read_csv('weather_london.csv', index_col=0)
metro_data = pd.read_csv('AC2021_AnnualisedEntryExit.csv', sep=';')
metro_stations_data = pd.read_csv('London stations.csv')
cyclestations_data = pd.read_csv('cycle_stations.csv')
boroughs = pd.read_csv('london_boroughs.geojson')

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
    trendline='ols',
    hover_data=['Date'],
    labels={
        'tavg': 'Gemiddelde Temperatuur (°C)',
        'Total Rentals': 'Aantal Fietsverhuur per Dag'
    },
    title='Correlatie tussen Weer en Fietsverhuur'
)

st.plotly_chart(fig)

###################################################################################################################################
# Ensure 'Day' is in datetime format
rentals_data['Day'] = pd.to_datetime(rentals_data['Day'])

# Add a 'Month' column to the rentals data
rentals_data['Month'] = rentals_data['Day'].dt.month

# Ensure 'Date' in weather data is in datetime format
weather_data['Date'] = pd.to_datetime(weather_data['Unnamed: 0'])
weather_data['Month'] = weather_data['Date'].dt.month

# Calculate monthly averages for weather data
monthly_weather = weather_data.groupby('Month').agg({
    'tavg': 'mean',  # Average temperature
    'prcp': 'mean'   # Average precipitation
}).reset_index()

# Calculate total rentals for each month
monthly_rentals = rentals_data.groupby('Month').agg({'Total Rentals': 'sum'}).reset_index()

# Calculate the global minimum and maximum total rentals across all months
global_min_rentals = monthly_rentals['Total Rentals'].min()
global_max_rentals = monthly_rentals['Total Rentals'].max()

# Streamlit app title
st.title("London Bike Rentals per Month with Weather Data")

# Month selection using a slider
selected_month = st.slider(
    "Select a month to visualize:",
    min_value=1,
    max_value=12,
    value=1,
    format="Month: %d"
)

# Get data for the selected month
selected_weather = monthly_weather[monthly_weather['Month'] == selected_month].iloc[0]
avg_temp = selected_weather['tavg']
avg_precipitation = selected_weather['prcp']

# Get total rentals for the selected month
selected_month_rentals = monthly_rentals[monthly_rentals['Month'] == selected_month].iloc[0]['Total Rentals']

# Display weather information and total rentals above the map
st.markdown(
    f"""
    ### Summary for {pd.to_datetime(f"2021-{selected_month}-01").strftime('%B')}
    - **Total Rentals**: {selected_month_rentals:,}
    - **Average Temperature**: {avg_temp:.1f}°C
    - **Average Precipitation**: {avg_precipitation:.1f} mm
    """
)

# Create a Folium map
m = folium.Map(location=[51.509865, -0.118092], tiles="CartoDB positron", zoom_start=10)

# Define a consistent colormap for rentals based on the global min and max rentals
colormap = linear.YlOrRd_09.scale(global_min_rentals, global_max_rentals)
colormap.caption = "Total Rentals per Month"

# Add a single GeoJson layer for London as a whole
for _, row in boroughs.iterrows():
    folium.GeoJson(
        row["geometry"],
        style_function=lambda feature: {
            "fillColor": colormap(selected_month_rentals),
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.7,
        },
        tooltip=(
            f"London<br>"
            f"Total Rentals: {selected_month_rentals:,}<br>"
            f"Avg Temp: {avg_temp:.1f}°C<br>"
            f"Avg Precipitation: {avg_precipitation:.1f} mm"
        )
    ).add_to(m)

# Add a legend to the map
m.add_child(colormap)

# Display the map in Streamlit
folium_static(m)

###################################################################################################################################
####################################### ________________________________________________________ ##################################
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static  # Importeer folium_static
import pandas as pd

# Laad de fietsstations data
cyclestations_data = pd.read_csv('cycle_stations_updated.csv')

# Convert 'Datetime' column to a readable string format (if it's not already in string format)
cyclestations_data['Datetime'] = pd.to_datetime(cyclestations_data['Datetime'], errors='coerce').dt.strftime('%Y-%m-%d')

# Maak een Streamlit app layout
st.title('London Cycle Stations')
st.markdown("Interaktive map met fietsverhuurstations in Londen")

# Voeg een slider toe om het aantal fietsen in te stellen
bike_slider = st.slider("Selecteer het aantal beschikbare fietsen", 0, 100, 0)

# Maak een basemap van Londen
m = folium.Map(location=[51.5074, -0.1278], zoom_start=12)

# MarkerCluster om stations te groeperen
marker_cluster = MarkerCluster().add_to(m)

# Voeg de stations toe aan de kaart
for index, row in cyclestations_data.iterrows():
    lat = row['lat']
    long = row['long']
    station_name = row['name']
    nb_bikes = row['nbBikes']  # Aantal fietsen
    nb_standard_bikes = row['nbStandardBikes']  # Aantal standaardfietsen
    nb_ebikes = row['nbEBikes']  # Aantal ebikes
    install_date = row['Datetime']  # Installatiedatum van het station

    # Voeg een marker toe met info over het station
    if nb_bikes >= bike_slider:  # Controleer of het aantal fietsen groter of gelijk is aan de slider
        folium.Marker(
            location=[lat, long],
            popup=folium.Popup(
                f"Station: {station_name}<br>Aantal fietsen: {nb_bikes}<br>Standaard: {nb_standard_bikes}<br>EBikes: {nb_ebikes}",
                max_width=300
            ),
            tooltip=f"Installatie datum: {install_date}",  # Toon de installatie datum in de tooltip
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(marker_cluster)

# Render de kaart in de Streamlit app
folium_static(m)
