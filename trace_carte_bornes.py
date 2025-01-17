import pandas as pd
import geopandas as gpd
import json
import matplotlib.pyplot as plt
from shapely.geometry import shape, Point


# Fichiers de données globaux
folder = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/scenario_deloc_1/data/"
parkings_file = folder + "donnees_parking_deloc.csv"
iris_file = folder + "iris_version_rennes_metropole.csv"

# Charger les données IRIS
def convert_to_geometry(geoshape_str):
    try:
        geoshape_dict = json.loads(geoshape_str)
        return shape(geoshape_dict)
    except Exception as e:
        print(f"Erreur lors de la conversion de Geo Shape : {geoshape_str}")
        return None

iris_df = pd.read_csv(iris_file, delimiter=";")
iris_df['geometry'] = iris_df['Geo Shape'].apply(convert_to_geometry)
iris_gdf = gpd.GeoDataFrame(iris_df, geometry='geometry', crs="EPSG:4326")

# Charger les données des parkings
parking_df = pd.read_csv(parkings_file, delimiter=";")

# Vérifier que 'Geo Point' et 'gml_id' sont présents
if 'Geo Point' not in parking_df.columns or 'gml_id' not in parking_df.columns:
    raise ValueError("Les colonnes 'Geo Point' et 'gml_id' sont nécessaires dans le fichier des parkings.")

# Extraire les coordonnées des points des parkings
def extract_coordinates(geo_point):
    try:
        lat, lon = map(float, geo_point.split(","))
        return lat, lon
    except Exception as e:
        print(f"Erreur lors de l'extraction des coordonnées : {geo_point}")
        return None, None

parking_df['latitude'], parking_df['longitude'] = zip(*parking_df['Geo Point'].apply(extract_coordinates))
parking_gdf = gpd.GeoDataFrame(
    parking_df, 
    geometry=gpd.points_from_xy(parking_df['longitude'], parking_df['latitude']),
    crs="EPSG:4326"
)

# Filtrer les parkings sélectionnés
selected_sites = ["v_parking.5269", "v_parking.5320"]  # Exemple, remplacez par votre liste réelle
selected_parkings_gdf = parking_gdf[parking_gdf['gml_id'].isin(selected_sites)]

# Tracer la carte
fig, ax = plt.subplots(figsize=(10, 10))
iris_gdf.plot(ax=ax, color='lightblue', edgecolor='black', alpha=0.5, label="Zones IRIS")
selected_parkings_gdf.plot(ax=ax, color='red', markersize=20, label="Parkings sélectionnés")

# Personnaliser la carte
ax.set_title("Carte de la métropole de Rennes avec parkings sélectionnés", fontsize=16)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
plt.legend()
plt.grid()
plt.show()