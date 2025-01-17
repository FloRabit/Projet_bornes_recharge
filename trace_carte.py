import pandas as pd
import geopandas as gpd
import json
import matplotlib.pyplot as plt
from shapely.geometry import shape

# Chemin du fichier CSV
folder = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/scenario_deloc_1/data/"
iris_file = folder + "iris_version_rennes_metropole.csv"

# Lire le fichier CSV avec pandas
iris_df = pd.read_csv(iris_file, delimiter=";")

# Vérifier que la colonne 'geoshape' est présente
if 'Geo Shape' not in iris_df.columns:
    raise ValueError("La colonne 'geoshape' est absente du fichier CSV.")

# Convertir la colonne 'geoshape' en objets géométriques
def convert_to_geometry(geoshape_str):
    try:
        geoshape_dict = json.loads(geoshape_str)
        return shape(geoshape_dict)
    except Exception as e:
        print(f"Erreur lors de la conversion de geoshape : {geoshape_str}")
        return None

iris_df['geometry'] = iris_df['Geo Shape'].apply(convert_to_geometry)

# Créer un GeoDataFrame à partir du DataFrame
gdf = gpd.GeoDataFrame(iris_df, geometry='geometry', crs="EPSG:4326")

# Vérification des données
print(gdf.head())

# Tracer la carte
fig, ax = plt.subplots(figsize=(10, 10))
gdf.plot(ax=ax, color='lightblue', edgecolor='black', alpha=0.7)
ax.set_title("Carte de la métropole de Rennes (IRIS)", fontsize=16)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
plt.grid()
plt.show()