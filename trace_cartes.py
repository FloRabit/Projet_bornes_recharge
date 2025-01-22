import json
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx # pour ajouter un fond de carte    
from shapely.geometry import shape, Point
from matplotlib.patches import Circle # pour tracer les cercles de couverture
from matplotlib.collections import PatchCollection # pour tracer les cercles de couverture
from math import cos, radians # pour ajuster la distance de couverture en fonction de la latitude
import matplotlib.cm as cm # faire un dégradé de couleur
import matplotlib.colors as colors # faire un dégradé de couleur


def plot_parking_and_buildings_with_basemap(
    iris_file, bat_file, zone_iris_id, selected_sites, R, output_file=None
):
    """
    Trace une carte avec un plan de Rennes comme fond de carte, adapté à la zone IRIS choisie.
    
    - La délimitation de la zone IRIS choisie.
    - Les parkings sélectionnés (taille proportionnelle au nombre de bornes installées, couleur rouge).
    - Les bâtiments (taille proportionnelle à la demande en VE, couleur verte pour ceux ayant une demande non nulle).

    Args:
        - iris_file (str): Chemin du fichier JSON contenant les zones IRIS.
        - parkings_file (str): Chemin du fichier JSON contenant tous les parkings de la zone IRIS.
        - bat_file (str): Chemin du fichier JSON contenant les données des bâtiments.
        - zone_iris_id (str): Identifiant de la zone IRIS à afficher.
        - selected_sites (list): Liste de dictionnaires contenant gml_id, nb_bornes_installees et geo_point.
        - R (float): Distance de couverture des bornes installées. ATTENTION : C'est un rayon !
        - output_file (str, optional): Chemin pour sauvegarder la carte générée (si None, la carte est affichée).
    """

    # Charger les données IRIS
    with open(iris_file, 'r', encoding='utf-8') as f:
        iris_data = json.load(f)

    iris_gdf = gpd.GeoDataFrame(
        [
            {
                "gml_id": iris["gml_id"],
                "geometry": shape(iris["geo_shape"]["geometry"])
            }
            for iris in iris_data
        ],
        crs="EPSG:4326"
    )

    # Filtrer la zone IRIS choisie
    selected_iris_gdf = iris_gdf[iris_gdf['gml_id'] == zone_iris_id]
    if selected_iris_gdf.empty:
        raise ValueError(f"Aucune zone IRIS trouvée avec l'identifiant '{zone_iris_id}'.")

    # Construire le GeoDataFrame des parkings sélectionnés à partir de selected_sites
    parkings_gdf = gpd.GeoDataFrame(
        [
            {
                "gml_id": site["gml_id"],
                "nb_bornes_installees": site["nb_bornes_installees"],
                "geometry": Point(site["geo_point"]["lon"], site["geo_point"]["lat"])
            }
            for site in selected_sites
        ],
        crs="EPSG:4326"
    )

    # Charger les données des bâtiments
    with open(bat_file, 'r', encoding='utf-8') as f:
        buildings_data= json.load(f)["batiments"]

    buildings_gdf = gpd.GeoDataFrame(
        [
            {
                "gml_id": building["gml_id"],
                "nb_ve_potentiel": building["nb_ve_potentiel"],
                "geometry": Point(building["geo_point_2d"]["lon"], building["geo_point_2d"]["lat"])
            }
            for building in buildings_data
        ],
        crs="EPSG:4326"
    )

    # Convertir toutes les données en EPSG:3857 pour le fond de carte
    selected_iris_gdf = selected_iris_gdf.to_crs(epsg=3857)
    parkings_gdf = parkings_gdf.to_crs(epsg=3857)
    buildings_gdf = buildings_gdf.to_crs(epsg=3857)

    # Tracer la carte
    fig, ax = plt.subplots(figsize=(10, 10))

    # Tracer la zone IRIS choisie
    selected_iris_gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=2, label="Zone IRIS")

    # Tracer les bâtiments avec une couleur adaptée
    buildings_gdf.plot(
        ax=ax,
        color='violet',
        markersize=5,
        label="Bâtiments"
    )

    # Tracer les parkings sélectionnés (en bleu, taille proportionnelle aux bornes installées)
    parkings_gdf['marker_size'] = parkings_gdf['nb_bornes_installees'] * 20 + 10
    parkings_gdf.plot(
        ax=ax, color='blue', markersize=parkings_gdf['marker_size'], label="Parkings sélectionnés"
    )

    # Ajouter des cercles de couverture pour les parkings sélectionnés
    patches = []
    for _, row in parkings_gdf.iterrows():
        # Ajuster le rayon R
        circle = Circle((row.geometry.x, row.geometry.y), radius=2*R, color='lightcoral', alpha=0.2)
        patches.append(circle)

    # Ajouter les cercles de couverture au graphique
    patch_collection = PatchCollection(patches, match_original=True)
    ax.add_collection(patch_collection)

    # Annoter les parkings avec le nombre de bornes installées
    for _, row in parkings_gdf.iterrows():
        ax.text(
            row.geometry.x, row.geometry.y + 15, str(int(row['nb_bornes_installees'])),
            fontsize=15, ha='center', color='darkred', weight='bold'
        )

    # Ajouter le fond de carte
    ctx.add_basemap(
        ax, source=ctx.providers.CartoDB.Positron, zoom=15,
        crs=3857
    )

    ax.set_title("Carte des parkings et bâtiments (Zone IRIS)", fontsize=16)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.legend()
    plt.grid(False)

    # Sauvegarder ou afficher la carte
    if output_file:
        plt.savefig(output_file, dpi=300)
        print(f"Carte sauvegardée dans '{output_file}'.")
    else:
        plt.show()


def plot_parking_and_tf_with_basemap(
    iris_file, tf_file, selected_sites, matrice_distances_tf_park, zone_iris_id, R, max_connections_per_transformer, output_file=None
):
    """
    Trace une carte avec un plan de Rennes comme fond de carte, adapté à la zone IRIS choisie.

    - La délimitation de la zone IRIS choisie.
    - Les parkings sélectionnés (taille proportionnelle au nombre de bornes installées, couleur rouge).
    - Les transformateurs (couleur en fonction du nombre de connexions).
    - Une ligne relie chaque parking au transformateur le plus proche.

    Args:
        - iris_file (str): Chemin du fichier JSON contenant les zones IRIS.
        - tf_file (str): Chemin du fichier JSON contenant les transformateurs.
        - selected_sites (list): Liste de dictionnaires contenant gml_id, nb_bornes_installees, et geo_point.
        - matrice_distances_tf_park (list): Liste de dictionnaires contenant les distances entre transformateurs et parkings.
        - zone_iris_id (str): Identifiant de la zone IRIS à afficher.
        - R (float): Distance de couverture des bornes installées. ATTENTION : C'est un rayon !
        - output_file (str, optional): Chemin pour sauvegarder la carte générée (si None, la carte est affichée).
    """
    # Charger les données IRIS
    with open(iris_file, 'r', encoding='utf-8') as f:
        iris_data = json.load(f)

    iris_gdf = gpd.GeoDataFrame(
        [
            {
                "gml_id": iris["gml_id"],
                "geometry": shape(iris["geo_shape"]["geometry"])
            }
            for iris in iris_data
        ],
        crs="EPSG:4326"
    )

    # Filtrer la zone IRIS choisie
    selected_iris_gdf = iris_gdf[iris_gdf['gml_id'] == zone_iris_id]
    if selected_iris_gdf.empty:
        raise ValueError(f"Aucune zone IRIS trouvée avec l'identifiant '{zone_iris_id}'.")

    # Charger les données des transformateurs
    with open(tf_file, 'r', encoding='utf-8') as f:
        tf_data = json.load(f)

    tf_gdf = gpd.GeoDataFrame(
        [
            {
                "gml_id": tf["gml_id"],
                "geometry": Point(float(tf["Geo Point"].split(",")[1]), float(tf["Geo Point"].split(",")[0]))
            }
            for tf in tf_data
        ],
        crs="EPSG:4326"
    )

    with open(matrice_distances_tf_park, 'r', encoding='utf-8') as f:
        matrice_distances_tf_park_data = json.load(f)

    # Construire les points des parkings à partir de selected_sites
    parkings_gdf = gpd.GeoDataFrame(
        [
            {
                "gml_id": site["gml_id"],
                "nb_bornes_installees": site["nb_bornes_installees"],
                "geometry": Point(site["geo_point"]["lon"], site["geo_point"]["lat"])
            }
            for site in selected_sites
        ],
        crs="EPSG:4326"
    )

    # Convertir toutes les données en EPSG:3857 pour le fond de carte
    selected_iris_gdf = selected_iris_gdf.to_crs(epsg=3857)
    parkings_gdf = parkings_gdf.to_crs(epsg=3857)
    tf_gdf = tf_gdf.to_crs(epsg=3857)

    # Initialiser les connexions transformateurs-parking
    transformateur_connections = {tf["gml_id"]: 0 for tf in tf_data}

    # Tracer la carte
    fig, ax = plt.subplots(figsize=(10, 10))

    # Tracer la zone IRIS choisie
    selected_iris_gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=2, label="Zone IRIS")

    # Relier les parkings à leur transformateur le plus proche via la matrice des distances
    for entry in matrice_distances_tf_park_data:
        parking_id = entry["parking_id"]
        distances = entry["distances"]  # Dictionnaire des distances transformateur -> parking

        # Vérifier si le parking est sélectionné
        if parking_id in parkings_gdf['gml_id'].values:
            parking = parkings_gdf[parkings_gdf['gml_id'] == parking_id].iloc[0]

            # Obtenir le nombre de bornes installées pour ce parking
            nb_bornes = int(parking["nb_bornes_installees"])

            # Connecter chaque borne du parking
            for _ in range(nb_bornes):
                # Trier les transformateurs par distance croissante
                sorted_transformateurs = sorted(distances.items(), key=lambda x: x[1])

                # Trouver un transformateur non saturé
                closest_tf_id = None
                for tf_id, distance in sorted_transformateurs:
                    if transformateur_connections[tf_id] < max_connections_per_transformer:
                        closest_tf_id = tf_id
                        break

                if closest_tf_id is not None:  # Si un transformateur disponible est trouvé
                    # Ajouter une connexion au transformateur
                    transformateur_connections[closest_tf_id] += 1

                    # Obtenir les coordonnées du transformateur
                    closest_tf = tf_gdf[tf_gdf['gml_id'] == closest_tf_id].iloc[0]

                    # Tracer la ligne entre le parking et le transformateur
                    ax.plot(
                        [parking.geometry.x, closest_tf.geometry.x],
                        [parking.geometry.y, closest_tf.geometry.y],
                        color='gray',
                        linewidth=1,
                        alpha=0.5
                    )

                    # Retirer ce transformateur des distances pour éviter une nouvelle connexion inutile
                    distances.pop(closest_tf_id)
                else:
                    print(f"Parking {parking_id} : Aucun transformateur disponible pour connecter une borne.")

    # Colorer les transformateurs en fonction des connexions
    for _, row in tf_gdf.iterrows():
        color = 'red' if transformateur_connections[row["gml_id"]] >= 3 else 'green'
        ax.scatter(row.geometry.x, row.geometry.y, color=color, s=100, label=f"Transformateur {row['gml_id']}")

    # Tracer les parkings sélectionnés
    parkings_gdf['marker_size'] = parkings_gdf['nb_bornes_installees'] * 20 + 10
    parkings_gdf[parkings_gdf['nb_bornes_installees'] > 0].plot(
        ax=ax, color='blue', markersize=parkings_gdf['marker_size'], label="Parkings sélectionnés"
    )

    # Ajouter des cercles de couverture pour les parkings
    patches = []
    for _, row in parkings_gdf.iterrows():
        circle = Circle((row.geometry.x, row.geometry.y), radius=2*R, color='lightcoral', alpha=0.2)
        patches.append(circle)
    

    patch_collection = PatchCollection(patches, match_original=True)
    ax.add_collection(patch_collection)

    # Annoter les parkings avec le nombre de bornes installées
    for _, row in parkings_gdf[parkings_gdf['nb_bornes_installees'] > 0].iterrows():
        ax.text(
            row.geometry.x, row.geometry.y + 15, str(int(row['nb_bornes_installees'])),
            fontsize=15, ha='center', color='darkred', weight='bold'
        )

    # Ajouter le fond de carte
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=15, crs=3857)

    # Personnaliser la carte
    ax.set_title("Carte des parkings et transformateurs (Zone IRIS)", fontsize=16)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.legend()
    plt.grid(False)

    # Sauvegarder ou afficher la carte
    if output_file:
        plt.savefig(output_file, dpi=300)
        print(f"Carte sauvegardée dans '{output_file}'.")
    else:
        plt.show()
        

if __name__=="__main__":

    zone_id = "iris.160" #identifiant de la zone cible
    N_ve_2000 = 50 #nombre de véhicules électriques à générer
    Rmax=200
    max_connections_per_transformer = 3

    folder = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/codes/"
    bat_file = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/batiments-rennes-metropole.json" # fichier volumineux, mis à part pour pouvoir faire des git push
    iris_file = folder + "data_global/iris_version_rennes_metropole.json"
    parkings_file = folder + "data_global/parkings.json"

    bat_filtres = folder + "data_local/batiments_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    parkings_filtres = folder + "data_local/parkings_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    transfo_filtres = folder + "data_local/transfo_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances_bat_park = folder + "data_local/matrice_distances_bat-park_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances_tf_park = folder + "data_local/matrice_distances_tf-park_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"

    selected_sites = [{'gml_id': 'v_parking.5272', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.5981796810755085, 'lat': 48.131050605364955}}, {'gml_id': 'v_parking.6157', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.610297454250723, 'lat': 48.12509726328288}}, {'gml_id': 'v_parking.6169', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.6090822211252582, 'lat': 48.12395455634806}}, {'gml_id': 'v_parking.6179', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.6105903197320801, 'lat': 48.1236542823524}}, {'gml_id': 'v_parking.6181', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.6112321790149753, 'lat': 48.12425221113884}}, {'gml_id': 'v_parking.6143', 'nb_bornes_installees': 2, 'geo_point': {'lon': -1.6023755835466336, 'lat': 48.12566515944683}}, {'gml_id': 'v_parking.5271', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.5975394614392338, 'lat': 48.12915259974292}}, {'gml_id': 'v_parking.6174', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.610706506739586, 'lat': 48.12567738410442}}, {'gml_id': 'v_parking.6182', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.6071810676722722, 'lat': 48.12481266978351}}]


    plot_parking_and_buildings_with_basemap(
        iris_file, bat_filtres, zone_id, selected_sites, Rmax, output_file=None
    )

    plot_parking_and_tf_with_basemap(
      iris_file, transfo_filtres, selected_sites, matrice_distances_tf_park, zone_id, Rmax, max_connections_per_transformer, output_file=None
    )

