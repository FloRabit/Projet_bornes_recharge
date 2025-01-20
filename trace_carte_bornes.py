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
    iris_file, parkings_file, buildings_file, zone_iris_id, selected_sites, R, output_file=None
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
                "nb_ve_potentiel": building["nb_ve_potentiel"],
                "geometry": Point(building["geo_point_2d"]["lon"], building["geo_point_2d"]["lat"])
            }
            for building in buildings_data
        ],
        crs="EPSG:4326"
    )

    # Convertir toutes les données en EPSG:3857 pour le fond de carte. buildings_gdf est converti en EPSG:3857 plus loin.
    selected_iris_gdf = selected_iris_gdf.to_crs(epsg=3857)
    parkings_gdf = parkings_gdf.to_crs(epsg=3857)
    

    # # Déterminer l'emprise géographique de la zone IRIS choisie
    # bounds = selected_iris_gdf.total_bounds  # [minx, miny, maxx, maxy]

    # Tracer la carte
    fig, ax = plt.subplots(figsize=(10, 10))


    # Tracer la zone IRIS choisie
    selected_iris_gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=2, label="Zone IRIS")

    
    # ### Tracer les bâtiments avec une couleur adaptée en fonction de nb_ve_potentiel

    # # La normalisation est modifiée pour décaler les valeurs vers le haut
    # min_val = buildings_gdf["nb_ve_potentiel"].min()
    # max_val = buildings_gdf["nb_ve_potentiel"].max()

    # # Décalage pour que 2/3 de la colormap soit la valeur minimale
    # norm = colors.Normalize(vmin=min_val, vmax=max_val)


    # # Créer une colormap
    # colormap = cm.get_cmap("Blues")

    # # Ajouter une couleur pour chaque bâtiment en fonction de nb_ve_potentiel
    # buildings_gdf['color'] = buildings_gdf['nb_ve_potentiel'].apply(lambda x: colormap(norm(x)))

    buildings_gdf = buildings_gdf.to_crs(epsg=3857)

    # Tracer les bâtiments avec une couleur adaptée
    buildings_gdf.plot(
        ax=ax,
        # color=buildings_gdf['color'],  # Utiliser les couleurs calculées
        # edgecolor='black',             # Couleur des contours
        # linewidth=0.5,                 # Épaisseur des contours
        color='blue',
        markersize=5,
        label="Bâtiments"
    )
    
    # Tracer les parkings sélectionnés (en rouge, taille proportionnelle aux bornes installées)
    parkings_gdf['marker_size'] = parkings_gdf['bornes_installées'] * 20 + 10
    parkings_gdf[parkings_gdf['bornes_installées'] > 0].plot(
        ax=ax, color='red', markersize=parkings_gdf['marker_size'], label="Parkings sélectionnés"
    )

    ### Ajustement de la distance de couverture D pour pouvoir la tracer sur la carte
    
    # Calculer la latitude moyenne des parkings
    latitudes = parkings_gdf.to_crs("EPSG:4326").geometry.y
    latitude_moyenne = latitudes.mean()

    # Calculer le facteur d'échelle en fonction de la latitude moyenne
    facteur_echelle = cos(radians(latitude_moyenne))

    # Ajouter des cercles de couverture pour les parkings sélectionnés
    patches = []
    for _, row in parkings_gdf[parkings_gdf['bornes_installées'] > 0].iterrows():
        # Ajuster le rayon R en fonction du facteur d'échelle
        adjusted_radius = 2*R * facteur_echelle
        circle = Circle((row.geometry.x, row.geometry.y), radius=adjusted_radius, color='lightcoral', alpha=0.2)
        patches.append(circle)

    # Ajouter les cercles de couverture au graphique
    patch_collection = PatchCollection(patches, match_original=True)
    ax.add_collection(patch_collection)

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
    # # Ajouter une barre de couleur (facultatif)
    # sm = cm.ScalarMappable(cmap=colormap, norm=norm)
    # sm.set_array([])
    # cbar = plt.colorbar(sm, ax=ax, orientation="vertical")
    # cbar.set_label("Nombre de véhicules électriques potentiels")

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
    N_ve_2000 = 50 #nombre de véhicules électriques à générer
    Rmax=200

    bat_filtres = folder + "batiments_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    parkings_filtres = folder + "parkings_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances = folder + "matrice_distances_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"

    plot_parking_and_buildings_with_basemap(
        zone_file,
        parkings_filtres,
        bat_filtres,
        zone_id,
        {'v_parking.259': 2, 'v_parking.3737': 3, 'v_parking.6871': 4}, 
        2*Rmax,
        output_file=None  # Changez en "output.png" pour sauvegarder la carte
    )