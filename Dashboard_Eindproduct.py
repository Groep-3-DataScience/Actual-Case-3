import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import plotly.express as px

fiets_data = pd.read_csv('fietsdata2021_rentals_by_day.csv')
weer_data = pd.read_csv('weather_london.csv', index_col=0)
metro_data = pd.read_csv('AC2021_AnnualisedEntryExit.csv', sep=';')
metro_stations_data = pd.read_csv('London stations.csv')

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
merged_data = pd.merge(weer_data, fiets_data, on='Date', how='inner')

###################################################################################################################################
####################################### Scatter plot van het weer t.o.v. fietsen gehuurd die dag ##################################
fig = px.scatter(
    merged_data,
    x='tavg', 
    y='Total Rentals',
    hover_data=['Date'],
    labels={'tavg': 'Gemiddelde Temperatuur (°C)', 'Total Rentals': 'Aantal Fietsverhuur per Dag'},
    title='Correlatie tussen Weer en Fietsverhuur'
)
st.plotly_chart(fig)

###################################################################################################################################
####################################### ________________________________________________________ ##################################
import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import os
from branca.colormap import linear
import json

# Streamlit app title
st.title("London Metro Station and Cycling Data Visualization")

# Define file paths
base_path = "/Users/enola/Documents/School/Jaar 3/Semester 2 (Minor Datascience)/Presentaties/03_Presentatie_Casus_London/"
geojson_file = os.path.join(base_path, 'london_boroughs.geojson')  # Path to the GeoJSON file
merged_file = os.path.join(base_path, '2021 Q2-Q4 (Apr-Dec)-Central.csv')  # Path to the merged file
metro_file = os.path.join(base_path, 'AC2021_AnnualisedEntryExit.csv')  # Path to the metro data file

# Cache the function to load the merged cycling data
@st.cache_data
def load_cycling_data(file_path):
    return pd.read_csv(file_path)

# Cache the function to load other datasets
@st.cache_data
def load_other_datasets():
    metro_data = pd.read_csv(metro_file, sep=';')
    metro_stations_data = pd.read_csv(os.path.join(base_path, 'London stations.csv'))
    tube_lines_data = pd.read_csv(os.path.join(base_path, 'London tube lines.csv'))
    return metro_data, metro_stations_data, tube_lines_data

# Cache the function to load the GeoJSON file
@st.cache_data
def load_geojson(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Load the merged cycling data
fiets_data_jaar = load_cycling_data(merged_file)

# Load other datasets
metro_data, metro_stations_data, tube_lines_data = load_other_datasets()

# Load the GeoJSON file
london_geojson = load_geojson(geojson_file)

# Ensure the 'Date' column is parsed correctly and create the 'Quarter' column
if 'Date' in fiets_data_jaar.columns:
    try:
        fiets_data_jaar['Date'] = pd.to_datetime(fiets_data_jaar['Date'], format='%d/%m/%Y', errors='coerce')
        fiets_data_jaar['Quarter'] = fiets_data_jaar['Date'].dt.quarter
    except Exception as e:
        st.error(f"Error parsing 'Date' column: {e}")
else:
    st.error("'Date' column is missing in the cycling data.")
    fiets_data_jaar['Quarter'] = None

# Group data by 'Direction' and 'Quarter' and calculate total cycling counts
if 'Direction' in fiets_data_jaar.columns and 'Count' in fiets_data_jaar.columns:
    cycling_counts = fiets_data_jaar.groupby(['Direction', 'Quarter'])['Count'].sum().reset_index()
else:
    st.error("'Direction' or 'Count' column is missing in the cycling data.")
    cycling_counts = pd.DataFrame(columns=['Direction', 'Quarter', 'Count'])

# Define a colormap for cycling intensity
if not cycling_counts.empty:
    color_map = linear.YlOrRd_09.scale(cycling_counts['Count'].min(), cycling_counts['Count'].max())
else:
    color_map = linear.YlOrRd_09.scale(0, 1)

# Use the 'AnnualisedEnEx' column for yearly entry/exit values
if 'AnnualisedEnEx' in metro_data.columns:
    # Ensure the column is numeric
    try:
        metro_data['AnnualisedEnEx'] = pd.to_numeric(metro_data['AnnualisedEnEx'].str.replace('.', '', regex=False), errors='coerce')
    except AttributeError:
        # If the column is already numeric, skip the string replacement
        metro_data['AnnualisedEnEx'] = pd.to_numeric(metro_data['AnnualisedEnEx'], errors='coerce')

    # Exclude outliers by capping at the 95th percentile
    max_value = metro_data['AnnualisedEnEx'].quantile(0.95)  # 95th percentile
    min_value = metro_data['AnnualisedEnEx'].replace(0, 1).min()  # Replace 0 with 1 to avoid log(0)

    # Define a colormap for station intensity using the capped range
    station_color_map = linear.YlOrRd_09.scale(min_value, max_value).to_step(n=10)  # Create 10 distinct color steps
else:
    st.error("'AnnualisedEnEx' column is missing in the metro data.")

# Define a colormap for station intensity using a logarithmic scale
if 'AnnualisedEnEx' in metro_data.columns:
    # Use a logarithmic scale for the colormap
    station_color_map = linear.YlOrRd_09.scale(
        metro_data['AnnualisedEnEx'].replace(0, 1).min(),  # Replace 0 with 1 to avoid log(0)
        metro_data['AnnualisedEnEx'].max()
    ).to_step(n=10)  # Create 10 distinct color steps for better differentiation
else:
    st.error("'AnnualisedEnEx' column is missing in the metro data.")

# Define colors for each tube line
line_colors = {
    "Bakerloo": "brown",
    "Central": "red",
    "Circle": "yellow",
    "District": "green",
    "Hammersmith and City": "pink",
    "Jubilee": "silver",
    "Metropolitan": "purple",
    "Northern": "black",
    "Piccadilly": "blue",
    "Victoria": "lightblue",
    "Waterloo and City": "turquoise",
    "Overground": "orange",
    "C2C": "darkblue",
    "DLR": "teal",
    "Elizabeth": "magenta",
    "Thameslink": "pink",
    "Southern": "chocolate",
    "Southeastern": "maroon",
    "South Western": "navy",
    "Tramlink": "lime",
    "Great Northern": "darkred",
    "Greater Anglia": "darkorange",
    "Heathrow Express": "gold",
    "Liberty": "lightgray",
    "Lioness": "darkgray",
    "Mildmay": "cyan",
    "Suffragette": "purple",
    "Windrush": "darkcyan",
    "Weaver": "olive",
}

# Create a Folium map
m = folium.Map(location=[51.509865, -0.118092], tiles='CartoDB positron', zoom_start=10)

# Add a slider to select the quarter
selected_quarter = st.slider("Select Quarter", min_value=2, max_value=4, step=1, key="quarter_slider")

# Filter data for the selected quarter
quarter_data = cycling_counts[cycling_counts['Quarter'] == selected_quarter]

# Add polygons for the boroughs corresponding to the direction
direction_to_boroughs = {
    "Northbound": ["Camden", "Islington", "Hackney", "City of London"],
    "Southbound": ["Southwark", "Lambeth", "Wandsworth"],
    "Eastbound": ["Tower Hamlets", "Newham", "Greenwich"],
    "Westbound": ["Hammersmith and Fulham", "Kensington and Chelsea", "Westminster"]
}

for _, row in quarter_data.iterrows():
    direction = row['Direction']
    total_count = row['Count']
    color = color_map(total_count)
    
    if direction in direction_to_boroughs:
        boroughs = direction_to_boroughs[direction]
        for feature in london_geojson['features']:
            if feature['properties']['name'] in boroughs:
                folium.GeoJson(
                    feature,
                    style_function=lambda x, color=color: {
                        'fillColor': color,
                        'color': 'black',
                        'weight': 3,
                        'fillOpacity': 0.7
                    },
                    tooltip=f"Direction: {direction}<br>Total Count: {total_count}"
                ).add_to(m)

# Add tube lines to the map
for idx, row in tube_lines_data.iterrows():
    from_station = row["From Station"]
    to_station = row["To Station"]
    tube_line = row["Tube Line"]

    if from_station in metro_stations_data["Station"].values and to_station in metro_stations_data["Station"].values:
        lat_lon1 = metro_stations_data.loc[metro_stations_data["Station"] == from_station, ["Latitude", "Longitude"]].values[0]
        lat_lon2 = metro_stations_data.loc[metro_stations_data["Station"] == to_station, ["Latitude", "Longitude"]].values[0]

        line_color = line_colors.get(tube_line, "gray")

        folium.PolyLine(
            locations=[lat_lon1, lat_lon2],
            color=line_color,
            weight=2.5,
            opacity=0.8,
            tooltip=f"{tube_line}: {from_station} ↔ {to_station}"
        ).add_to(m)

# Add metro stations to the map
for idx, row in metro_stations_data.iterrows():
    station_name = row["Station"]
    lat, lon = row["Latitude"], row["Longitude"]

    annualised_enex = metro_data.loc[metro_data["Station"] == station_name, "AnnualisedEnEx"].values
    annualised_enex = annualised_enex[0] if len(annualised_enex) > 0 else 0

    station_color = station_color_map(annualised_enex)

    folium.CircleMarker(
        location=[lat, lon],
        radius=3,
        popup=f"Station: {station_name}<br>Annualised Entry/Exit: {annualised_enex:,}",
        color="black",
        weight=1,
        fill=True,
        fill_color=station_color,
        fill_opacity=0.7
    ).add_to(m)

# Display the map in Streamlit
folium_static(m)
