import pandas as pd
from geopy.distance import geodesic

folder = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/scenario_deloc_1/data"
parkings_file = folder + "donnees_parking_deloc.csv"
iris_file = folder + "iris_version_rennes_metropole.csv"
output_file = folder + "matrice_distances.csv"

# Charger les fichiers
parkings_df = pd.read_csv(parkings_file, delimiter=";")
iris_df = pd.read_csv(iris_file, delimiter=";")

# Fonction pour extraire les coordonnées depuis la colonne "Geo Point"
def extract_coordinates(geo_point):
    try:
        latitude, longitude = map(float, geo_point.split(","))
        return latitude, longitude
    except Exception as e:
        raise ValueError(f"Erreur lors de l'extraction des coordonnées : {geo_point}. Détail : {e}")

# Extraire les coordonnées pour les parkings
if "Geo Point" in parkings_df.columns:
    parkings_df["latitude"], parkings_df["longitude"] = zip(*parkings_df["Geo Point"].apply(extract_coordinates))
else:
    raise ValueError("La colonne 'Geo Point' est absente du fichier des parkings.")

# Extraire les coordonnées pour les parcelles IRIS
if "Geo Point" in iris_df.columns:
    iris_df["latitude"], iris_df["longitude"] = zip(*iris_df["Geo Point"].apply(extract_coordinates))
else:
    raise ValueError("La colonne 'Geo Point' est absente du fichier des parcelles IRIS.")

# Initialiser la matrice des distances
distance_matrix = []

for idx_iris, iris_row in iris_df.iterrows():
    iris_coordinates = (iris_row["latitude"], iris_row["longitude"])
    distances = []
    for idx_parking, parking_row in parkings_df.iterrows():
        parking_coordinates = (parking_row["latitude"], parking_row["longitude"])
        distance = geodesic(iris_coordinates, parking_coordinates).meters  # Distance en mètres
        distances.append(distance)
    distance_matrix.append(distances)

# Convertir la matrice en DataFrame
distance_matrix_df = pd.DataFrame(
    distance_matrix,
    index=iris_df["gml_id"],  # Remplacez par la colonne d'identifiant unique pour les IRIS
    columns=parkings_df["gml_id"]  # Remplacez par la colonne d'identifiant unique pour les parkings
)

# Sauvegarder la matrice des distances au format CSV
distance_matrix_df.to_csv(output_file)

print(f"Matrice des distances calculée et sauvegardée dans : {output_file}")