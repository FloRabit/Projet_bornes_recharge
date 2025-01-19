import json
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import shape, Point


def plot_parking_and_buildings_with_basemap(
    iris_file, parkings_file, buildings_file, zone_iris_id, selected_sites, output_file=None
):
    """
    Trace une carte avec un plan de Rennes comme fond de carte, adapté à la zone IRIS choisie.
    
    - La délimitation de la zone IRIS choisie.
    - Les parkings sélectionnés (taille proportionnelle au nombre de bornes installées, couleur rouge).
    - Les bâtiments (taille proportionnelle à la demande en VE, couleur verte pour ceux ayant une demande non nulle).

    Args:
        - iris_file (str): Chemin du fichier JSON contenant les zones IRIS.
        - parkings_file (str): Chemin du fichier JSON contenant tous les parkings de la zone IRIS.
        - buildings_file (str): Chemin du fichier JSON contenant les données des bâtiments.
        - zone_iris_id (str): Identifiant de la zone IRIS à afficher.
        - selected_sites (dict): Dictionnaire {parking_id: nombre_de_bornes_installées}.
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

    # Charger les données des parkings
    with open(parkings_file, 'r', encoding='utf-8') as f:
        parkings_data = json.load(f)["parkings"]

    parkings_gdf = gpd.GeoDataFrame(
        [
            {
                "gml_id": parking["gml_id"],
                "nb_pl": parking["nb_pl"],
                "max_bornes": parking["max_bornes"],
                "geometry": Point(parking["geo_point_2d"]["lon"], parking["geo_point_2d"]["lat"])
            }
            for parking in parkings_data
        ],
        crs="EPSG:4326"
    )

    # Ajouter le nombre de bornes installées aux parkings sélectionnés
    parkings_gdf['bornes_installées'] = parkings_gdf['gml_id'].map(selected_sites).fillna(0)

    # Charger les données des bâtiments
    with open(buildings_file, 'r', encoding='utf-8') as f:
        buildings_data = json.load(f)["batiments"]

    buildings_gdf = gpd.GeoDataFrame(
        [
            {
                "gml_id": building["gml_id"],
                "nb_ve": building["nb_ve"],
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

    # # Déterminer l'emprise géographique de la zone IRIS choisie
    # bounds = selected_iris_gdf.total_bounds  # [minx, miny, maxx, maxy]

    # Séparer les bâtiments avec et sans demande
    buildings_with_demand_gdf = buildings_gdf[buildings_gdf['nb_ve'] > 0]
    buildings_no_demand_gdf = buildings_gdf[buildings_gdf['nb_ve'] == 0]

    # Tracer la carte
    fig, ax = plt.subplots(figsize=(10, 10))


    # Tracer la zone IRIS choisie
    selected_iris_gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=2, label="Zone IRIS")

    # Tracer les bâtiments sans demande
    buildings_no_demand_gdf.plot(ax=ax, color='blue', markersize=5, label="Bâtiments sans demande")

    # Tracer les bâtiments avec demande (en vert, taille proportionnelle à la demande)
    buildings_with_demand_gdf['marker_size'] = buildings_with_demand_gdf['nb_ve'] * 5 + 10
    buildings_with_demand_gdf.plot(
        ax=ax, color='green', markersize=buildings_with_demand_gdf['marker_size'], label="Bâtiments avec demande"
    )

    # Annoter les bâtiments avec demande
    for _, row in buildings_with_demand_gdf.iterrows():
        ax.text(
            row.geometry.x, row.geometry.y+15, str(row['nb_ve']),
            fontsize=15, ha='center', color='darkgreen', weight='bold'
        )

    # Tracer les parkings sélectionnés (en rouge, taille proportionnelle aux bornes installées)
    parkings_gdf['marker_size'] = parkings_gdf['bornes_installées'] * 20 + 10
    parkings_gdf[parkings_gdf['bornes_installées'] > 0].plot(
        ax=ax, color='red', markersize=parkings_gdf['marker_size'], label="Parkings sélectionnés"
    )

    # Annoter les parkings avec le nombre de bornes installées
    for _, row in parkings_gdf[parkings_gdf['bornes_installées'] > 0].iterrows():
        ax.text(
            row.geometry.x, row.geometry.y + 15, str(int(row['bornes_installées'])),
            fontsize=15, ha='center', color='darkred', weight='bold'
        )

    # Ajouter le fond de carte
    ctx.add_basemap(
        ax, source=ctx.providers.CartoDB.Positron, zoom=15,
        crs=3857
    )

    # # Ajuster les limites de l'affichage à l'emprise géographique
    # ax.set_xlim(bounds[0], bounds[2])
    # ax.set_ylim(bounds[1], bounds[3])

    # Personnaliser la carte
    ax.set_title("Carte des parkings et bâtiments (Zone IRIS)", fontsize=16)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.legend()
    plt.grid(False)
    # plt.tight_layout()  # Ajuster les marges automatiquement en théorie, mais cela ne semble pas fonctionner correctement

    # Sauvegarder ou afficher la carte
    if output_file:
        plt.savefig(output_file, dpi=300)
        print(f"Carte sauvegardée dans '{output_file}'")
    else:
        plt.show()



if __name__=="__main__":

    folder = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/codes/data_global/"
    bat_file = folder + "batiments-rennes-metropole.json"
    zone_file = folder + "iris_version_rennes_metropole.json"
    parkings_file = folder + "parkings.json"


    zone_id = "iris.163" #identifiant de la zone cible
    N_ve = 50 #nombre de véhicules électriques à générer

    bat_filtres = folder + "batiments_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    parkings_filtres = folder + "parkings_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances = folder + "matrice_distances_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"

    plot_parking_and_buildings_with_basemap(
        zone_file,
        parkings_filtres,
        bat_filtres,
        zone_id,
        selected_sites={'v_parking.259': 2, 'v_parking.3737': 4, 'v_parking.6871': 4},  # Parkings et bornes installées
        output_file=None  # Changez en "output.png" pour sauvegarder la carte
    )