from ortools.linear_solver import pywraplp
import pandas as pd
import geopandas as gpd
from geopy.distance import geodesic
import json
import matplotlib.pyplot as plt
from shapely.geometry import shape



####################################################################################################
## TRAITEMENT DES DONNEES
####################################################################################################

# Fonction pour extraire les coordonnées depuis la colonne "Geo Point"
def extract_coordinates(geo_point):
    try:
        latitude, longitude = map(float, geo_point.split(","))
        return latitude, longitude
    except Exception as e:
        raise ValueError(f"Erreur lors de l'extraction des coordonnées : {geo_point}. Détail : {e}")


# Fonction pour construire la matrice des distances en format CSV
def construction_matrice_distances(parkings_file, iris_file, distances_file):
    parkings_df = pd.read_csv(parkings_file, delimiter=";")
    iris_df = pd.read_csv(iris_file, delimiter=";")

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
    distance_matrix_df.to_csv(distances_file)

    print(f"Matrice des distances calculée et sauvegardée dans : {distances_file}")



####################################################################################################
## IMPRESSION GRAPHIQUE
####################################################################################################
# Convertir la colonne 'geoshape' en objets géométriques
def convert_to_geometry(geoshape_str):
    try:
        geoshape_dict = json.loads(geoshape_str)
        return shape(geoshape_dict)
    except Exception as e:
        print(f"Erreur lors de la conversion de Geo Shape : {geoshape_str}")
        return None
    
# Extraire les coordonnées des points des parkings
def extract_coordinates(geo_point):
    try:
        lat, lon = map(float, geo_point.split(","))
        return lat, lon
    except Exception as e:
        print(f"Erreur lors de l'extraction des coordonnées : {geo_point}")
        return None, None


def tracer_carte(iris_df, parkings_df, selected_sites):

    iris_df['geometry'] = iris_df['Geo Shape'].apply(convert_to_geometry)
    iris_gdf = gpd.GeoDataFrame(iris_df, geometry='geometry', crs="EPSG:4326")

    # Vérifier que 'Geo Point' et 'gml_id' sont présents
    if 'Geo Point' not in parkings_df.columns or 'gml_id' not in parkings_df.columns:
        raise ValueError("Les colonnes 'Geo Point' et 'gml_id' sont nécessaires dans le fichier des parkings.")

    parkings_df['latitude'], parkings_df['longitude'] = zip(*parkings_df['Geo Point'].apply(extract_coordinates))
    parking_gdf = gpd.GeoDataFrame(
        parkings_df, 
        geometry=gpd.points_from_xy(parkings_df['longitude'], parkings_df['latitude']),
        crs="EPSG:4326"
    )

    # Filtrer les parkings sélectionnés
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

####################################################################################################
## RESOLUTION DU PROBLEME MCPL
####################################################################################################

def mclp(T, p, Dmax, W, S, C):
    """
    Résout le problème Maximal Covering Location Problem (MCLP).

    Paramètres :
        T : dict, matrice des distances {i: {j: distance_ij}} (demande vers emplacement).
        p : int, nombre maximal de centres à implanter.
        Dmax : float, distance maximale de couverture.
        W : list, [(id, demande)], liste des lieux de demande.
        S : list, [id], liste des emplacements potentiels pour les centres.
        C : dict, {id: capacité}, capacité de chaque emplacement potentiel.

    Retourne :
        selected_sites : list, liste des identifiants des emplacements sélectionnés.
        max_coverage : float, couverture totale maximale.
        allocations : dict, {(i, j): couverture}, allocation de demande par emplacement.
    """
    # Initialisation du solveur
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        raise Exception("Erreur lors de la création du solveur.")

    # Extraire les identifiants des lieux de demande et des emplacements potentiels
    demande_ids = [w[1][0] for w in W.iterrows()]  # Liste des identifiants de lieux de demande
    site_ids = [s[1][0] for s in S.iterrows()]  # Liste des identifiants d'emplacements potentiels
    demande_weights = {w[1][0]: w[1][1] for w in W.iterrows()}  # Dictionnaire {id_demande: demande}

    # Variables de décision
    x = {i: solver.BoolVar(f"x[{i}]") for i in site_ids}  # x[i] = 1 si le site i est choisi
    y = {j: solver.BoolVar(f"y[{j}]") for j in demande_ids}  # y[j] = 1 si le lieu de demande j est couvert
    z = {}
    for j in demande_ids:
        for i in site_ids:
            if j in T and i in T[j]:  # Vérifie si le site i est à portée de la demande j
                z[(j, i)] = solver.IntVar(0, demande_weights[j], f"z[{j},{i}]")

    # Contraintes

    # 1. Limitation du nombre de centres à implanter
    solver.Add(solver.Sum(x[i] for i in site_ids) <= p)

    # 2. Couverture : une demande est couverte si au moins un site est dans sa zone
    for j in demande_ids:
        solver.Add(y[j] <= solver.Sum(x[i] for i in site_ids if j in T and i in T[j] and T[j][i] <= Dmax))

    # 3. Capacité des bornes
    for i in site_ids:
        solver.Add(solver.Sum(z[(j, i)] for j in demande_ids if j in T and i in T[j] and T[j][i] <= Dmax) <= C[i] * x[i])

    
    # Objectif : maximiser la demande couverte
    solver.Maximize(solver.Sum(y[j] * demande_weights[j] for j in demande_ids))

    # Résolution
    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL:
        selected_sites = [i for i in site_ids if x[i].solution_value() == 1]
        max_coverage = solver.Objective().Value()
        
        # Extraire les allocations --> ne fonctionne pas pour l'instant
        # allocations = {}
        # for j in demande_ids:
        #     for i in site_ids:
        #         if (j, i) in z and z[(j, i)].solution_value() > 0:
        #             allocations[(j, i)] = z[(j, i)].solution_value()
        return selected_sites, max_coverage #, allocations
    else:
        
        raise Exception("Le solveur n'a pas trouvé de solution optimale.")
        


####################################################################################################
## VARIABLES
####################################################################################################

# Chemins des fichiers
folder = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/scenario_deloc_1/data/"

# Fichiers de données globaux
parkings_file = folder + "donnees_parking_deloc.csv"
iris_file = folder + "iris_version_rennes_metropole.csv"
distances_file = folder + "matrice_distances.csv"

# Fichiers de données pour le MCLP
S_file = folder + "S_list.csv"
W_file = folder + "W_list.csv"
T_file = folder + "T_matrix.json"
capacite_file = folder + "capacite_sites.json"


# Paramètres du problème
demande_iris = 50  # Demande pour chaque parcelle IRIS de 2000 habitants. Uniforme pour simplification
p = 1000  # Nombre maximal de centres
Dmax = 500  # Distance maximale de couverture

####################################################################################################
## EXECUTION
####################################################################################################

# extraction_donnees(parkings_file, iris_file, distances_file, S_file, W_file, T_file, demande_iris)



if __name__ == "__main__":
    # Charger les données
    iris_df = pd.read_csv(iris_file, delimiter=";")
    parkings_df = pd.read_csv(parkings_file, delimiter=";")
    S_df = pd.read_csv(S_file, delimiter=",")
    W_df = pd.read_csv(W_file, delimiter=",")

    # Charger le fichier JSON en dictionnaire Python
    with open(T_file, "r") as file:
        T_matrix = json.load(file)
    with open(capacite_file, "r") as file:
        C_dict = json.load(file)


    selected_sites, max_coverage = mclp(T_matrix, p, Dmax, W_df, S_df, C_dict)
    # print("Sites sélectionnés :", selected_sites)
    print("Couverture maximale :", max_coverage)
    tracer_carte(iris_df, parkings_df, selected_sites)