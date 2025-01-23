import json
import csv
from shapely.geometry import shape, Point
from geopy.distance import geodesic
import random



def traiter_batiments(bat_file_path, iris_file_path, bat_output_path, zone_id, N_ve_2000):
    """
    Filtre les bâtiments appartenant à une zone cible définie par son identifiant,
    nettoie les champs inutiles, et ajoute un récapitulatif des totaux.
    Attribue un nombre aléatoire de véhicules électriques (VE) à des bâtiments
    sélectionnés de manière aléatoire, tout en respectant une limite globale pour le secteur.

    Args:
    - bat_file_path (str): Chemin du fichier JSON contenant les bâtiments.
    - iris_file_path (str): Chemin du fichier JSON contenant les zones géographiques iris.
    - bat_output_path (str): Chemin du fichier JSON de sortie.
    - zone_id (str): Identifiant (gml_id) de la zone iris cible.
    - N_ve (int): Quantité maximale de véhicules électriques sur le secteur, normalisé sur un secteur de 2 000 personnes.


    Returns:
    - None
    """
    # Charger le fichier JSON des bâtiments
    with open(bat_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Charger le fichier JSON des zones
    with open(iris_file_path, 'r', encoding='utf-8') as f:
        zones = json.load(f)

    ###########################################################
    # Filtrer les bâtiments dans la zone cible
    ###########################################################

    # Trouver la zone cible par son gml_id
    zone_geographique = None
    for zone in zones:
        if zone.get("gml_id") == zone_id:
            zone_geographique = zone.get("geo_shape")
            break

    if not zone_geographique:
        raise ValueError(f"Zone avec l'identifiant '{zone_id}' non trouvée dans le fichier des zones.")

    # Créer le polygone de la zone cible
    zone_polygon = shape(zone_geographique["geometry"])

    # Filtrer les bâtiments en vérifiant si leur centre est dans la zone
    batiments_dans_zone = []
    for item in data:
        if "geo_point_2d" in item:
            lon, lat = item["geo_point_2d"]["lon"], item["geo_point_2d"]["lat"]
            center_point = Point(lon, lat)
            # Vérifier si le point central est dans la zone
            if center_point.within(zone_polygon):
                batiments_dans_zone.append(item)
    
    ###########################################################
    # Nettoyer les champs inutiles
    ###########################################################

    # Garder uniquement les catégories souhaitées
    categories_a_conserver = ["geo_point_2d", "geo_shape", "gml_id", "nb_maison", "nb_appart", "nb_occ_theor_18plus"]
    batiments_nettoyes = [
        {key: item[key] for key in categories_a_conserver if key in item}
        for item in batiments_dans_zone
    ]


    ###########################################################
    # Générer un nombre aléatoire de véhicules électriques (VE)
    ###########################################################

    for batiment in batiments_nettoyes:
        nb_occ_theor_18plus = batiment.get("nb_occ_theor_18plus", 0) or 0
        batiment["nb_ve_potentiel"] =  N_ve_2000 * nb_occ_theor_18plus/2000 # Pas de VE si aucun adulte


    ###########################################################
    # Calculer les totaux pour le récapitulatif
    ###########################################################

    # Calculer les totaux pour le récapitulatif
    nb_appart_total = sum(batiment.get("nb_appart", 0) or 0 for batiment in batiments_nettoyes)    
    nb_maison_total = sum(batiment.get("nb_maison", 0) or 0 for batiment in batiments_nettoyes)
    nb_occ_theor_18plus_total = sum(batiment.get("nb_occ_theor_18plus", 0) or 0 for batiment in batiments_nettoyes)
    nb_ve_total = N_ve_2000 * nb_occ_theor_18plus_total // 2000

    recapitulatif = {
        "nb_appart_total": nb_appart_total,
        "nb_maison_total": nb_maison_total,
        "nb_occ_theor_18plus_total": nb_occ_theor_18plus_total,
        "nb_ve_total": nb_ve_total
    }

    # Ajouter le récapitulatif au début du fichier JSON
    resultat = {
        "recapitulatif": recapitulatif,
        "batiments": batiments_nettoyes
    }

    # Sauvegarder dans un nouveau fichier JSON
    with open(bat_output_path, 'w', encoding='utf-8') as f:
        json.dump(resultat, f, ensure_ascii=False, indent=4)

    
    
    print(f"Les bâtiments sélectionnés et filtrés ont été sauvegardés dans '{bat_output_path}'.")
    print(f"Résumé des totaux : {recapitulatif}")


def traiter_parkings(park_file_path, iris_file_path, park_output_path, zone_id):
    """
    Filtre les parkings appartenant à une zone cible définie par son identifiant,
    puis nettoie les champs inutiles à la suite de la simulation. Ajoute un champ `max_bornes`
    correspondant au nombre maximal de bornes pouvant être installées.
    Compte également le nombre total de parkings disponibles et le nombre maximal de bornes.

    Args:
    - park_file_path (str): Chemin du fichier JSON contenant les parkings.
    - iris_file_path (str): Chemin du fichier JSON contenant les zones géographiques iris.
    - park_output_path (str): Chemin du fichier JSON de sortie.
    - zone_id (str): Identifiant (gml_id) de la zone iris cible.

    Returns:
    - None
    """
    import json
    from shapely.geometry import shape, Point

    # Charger le fichier JSON des parkings
    with open(park_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Charger le fichier JSON des zones
    with open(iris_file_path, 'r', encoding='utf-8') as f:
        zones = json.load(f)

    # Trouver la zone cible par son gml_id
    zone_geographique = None
    for zone in zones:
        if zone.get("gml_id") == zone_id:
            zone_geographique = zone.get("geo_shape")
            break

    if not zone_geographique:
        raise ValueError(f"Zone avec l'identifiant '{zone_id}' non trouvée dans le fichier des zones.")

    # Créer le polygone de la zone cible
    zone_polygon = shape(zone_geographique["geometry"])

    # Filtrer les parkings en vérifiant si leur centre est dans la zone
    parkings_dans_zone = []
    for item in data:
        if "geo_point_2d" in item:
            lon, lat = item["geo_point_2d"]["lon"], item["geo_point_2d"]["lat"]
            center_point = Point(lon, lat)
            # Vérifier si le point central est dans la zone
            if center_point.within(zone_polygon):
                parkings_dans_zone.append(item)

    # Garder uniquement les catégories souhaitées
    categories_a_conserver = ["geo_point_2d", "geo_shape", "gml_id", "type", "nb_pl", "categorie"]
    parkings_nettoyes = []
    total_parkings = 0
    total_max_bornes = 0

    for item in parkings_dans_zone:
        parking = {key: item[key] for key in categories_a_conserver if key in item}

        # Ajouter le champ `max_bornes` en fonction du nombre de places
        nb_places = parking.get("nb_pl", 0) or 0

        parking["max_bornes"] = int(0.1*nb_places) + 1 # Prendre la partie entière supérieure de 10% des places

        # Compter les parkings et les bornes maximales
        total_parkings += 1
        total_max_bornes += parking["max_bornes"]

        parkings_nettoyes.append(parking)

    # Ajouter les informations globales dans le JSON
    resultat = {
        "recapitulatif": {
            "total_parkings": total_parkings,
            "total_max_bornes": total_max_bornes
        },
        "parkings": parkings_nettoyes
    }

    # Sauvegarder dans un nouveau fichier JSON
    with open(park_output_path, 'w', encoding='utf-8') as f:
        json.dump(resultat, f, ensure_ascii=False, indent=4)

    print(f"Les parkings sélectionnés, filtrés et enrichis ont été sauvegardés dans '{park_output_path}'.")
    print(f"Résumé : {total_parkings} parkings disponibles, {total_max_bornes} bornes maximales possibles.")


def traiter_transfo(tf_file_path, iris_file_path, tf_output_path, zone_id):
    """
    Filtre les transformateurs appartenant à une zone IRIS définie par son identifiant
    et exporte uniquement les colonnes "id" et "Geo Point" sous format JSON.

    Args:
        - tf_file_path (str): Chemin du fichier CSV contenant les transformateurs.
        - iris_file_path (str): Chemin du fichier JSON contenant les zones IRIS.
        - tf_output_path (str): Chemin du fichier JSON de sortie.
        - zone_id (str): Identifiant (gml_id) de la zone IRIS cible.

    Returns:
        - None
    """
    # Charger le fichier JSON des zones IRIS
    with open(iris_file_path, 'r', encoding='utf-8') as f:
        zones = json.load(f)

    # Trouver la zone cible par son gml_id
    zone_geographique = None
    for zone in zones:
        if zone.get("gml_id") == zone_id:
            zone_geographique = zone.get("geo_shape")
            break

    if not zone_geographique:
        raise ValueError(f"Zone avec l'identifiant '{zone_id}' non trouvée dans le fichier des zones IRIS.")

    # Créer le polygone de la zone cible
    zone_polygon = shape(zone_geographique["geometry"])

    # Lire le fichier CSV des transformateurs
    transformateurs_dans_zone = []
    with open(tf_file_path, 'r', encoding='ISO-8859-1') as f:
        # Lecture brute du fichier pour extraire les en-têtes
        raw_data = f.readlines()
        header = raw_data[0].strip().split(";")  # Extraire les colonnes
        rows = raw_data[1:]  # Toutes les lignes de données

        for line in rows:
            # Associer les colonnes aux données
            values = line.strip().split(";")
            row = dict(zip(header, values))

            # Extraire les champs nécessaires
            transformateur_id = row.get("id", None)
            geo_point = row.get("Geo Point", None)

            if transformateur_id and geo_point:
                try:
                    # Extraire les coordonnées depuis le champ Geo Point
                    lat, lon = map(float, geo_point.split(","))
                    point = Point(lon, lat)

                    # Vérifier si le point est dans la zone IRIS
                    if point.within(zone_polygon):
                        transformateurs_dans_zone.append({
                            "gml_id": "tf." + transformateur_id,
                            "Geo Point": geo_point
                        })
                except (ValueError, TypeError):
                    print(f"Coordonnées invalides pour le transformateur avec id {transformateur_id}.")

    # Enregistrer les résultats dans un fichier JSON
    with open(tf_output_path, 'w', encoding='utf-8') as f:
        json.dump(transformateurs_dans_zone, f, ensure_ascii=False, indent=4)

    print(f"Les transformateurs sélectionnés ont été sauvegardés dans '{tf_output_path}'.")
    print(f"Nombre de transformateurs dans la zone '{zone_id}': {len(transformateurs_dans_zone)}")


def calculer_matrice_distances_bat_parkings(bat_file_path, parkings_file, output_file):
    """
    Calcule une matrice des distances entre des bâtiments et des parkings.

    Args:
    - bat_file_path (str): Chemin du fichier JSON des bâtiments sélectionnés.
    - parkings_file (str): Chemin du fichier JSON des parkings sélectionnés.
    - output_file (str): Chemin du fichier pour sauvegarder la matrice des distances.

    Returns:
    - None
    """
    # Charger les fichiers JSON
    with open(bat_file_path, 'r', encoding='utf-8') as f:
        data_bat = json.load(f)

    # Extraire les bâtiments de la structure JSON
    batiments = data_bat.get("batiments", [])

    with open(parkings_file, 'r', encoding='utf-8') as f:
        data_parkings = json.load(f)
    
    parkings = data_parkings.get("parkings", [])

    # Extraire les points des bâtiments et des parkings
    points_batiments = [
        (batiment["gml_id"], (batiment["geo_point_2d"]["lat"], batiment["geo_point_2d"]["lon"]))
        for batiment in batiments
    ]
    points_parkings = [
        (parking["gml_id"], (parking["geo_point_2d"]["lat"], parking["geo_point_2d"]["lon"]))
        for parking in parkings
    ]

    # Calculer la matrice des distances
    matrice_distances = []
    for id_batiment, coord_batiment in points_batiments:
        distances = {
            "batiment_id": id_batiment,
            "distances": {}
        }
        for id_parking, coord_parking in points_parkings:
            distance = geodesic(coord_batiment, coord_parking).meters
            distances["distances"][id_parking] = distance
        matrice_distances.append(distances)

    # Sauvegarder la matrice dans un fichier JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(matrice_distances, f, ensure_ascii=False, indent=4)

    print(f"La matrice des distances a été sauvegardée dans '{output_file}'.")


def calculer_matrice_distances_tf_parkings(tf_file_path, selected_sites_path, output_file):
    """
    Calcule une matrice des distances entre des transformateurs et des parkings sélectionnés avec des bornes.

    Args:
    - tf_file_path (str): Chemin du fichier JSON des transformateurs.
    - selected_sites (list): Liste de dictionnaires contenant gml_id, nb_bornes_installees et geo_point.
    - output_file (str): Chemin du fichier pour sauvegarder la matrice des distances.

    Returns:
    - None
    """
    # Charger les fichiers JSON
    with open(tf_file_path, 'r', encoding='utf-8') as f:
        transformateurs = json.load(f)

    # Charger le fichier JSON des sites sélectionnés
    with open(selected_sites_path, 'r', encoding='utf-8') as f:
        selected_sites = json.load(f)

    # Construire les points des parkings à partir de selected_sites
    points_parkings = [
        (site["gml_id"], (site["geo_point"]["lat"], site["geo_point"]["lon"]))
        for site in selected_sites
    ]

    # Extraire les points des transformateurs
    points_transformateurs = [
        (transfo["gml_id"], (float(transfo["Geo Point"].split(",")[0]), float(transfo["Geo Point"].split(",")[1])))
        for transfo in transformateurs
    ]

    matrice_distances = []
    for id_parking, coord_parking in points_parkings:
        distances = {
            "parking_id": id_parking,
            "distances": {}
        }
        for id_transfo, coord_transfo in points_transformateurs:
            distance = geodesic(coord_parking, coord_transfo).meters
            distances["distances"][id_transfo] = distance
        matrice_distances.append(distances)

    # Sauvegarder la matrice dans un fichier JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(matrice_distances, f, ensure_ascii=False, indent=4)

    print(f"La matrice des distances a été sauvegardée dans '{output_file}'.")



if __name__ == "__main__":

    zone_id = "iris.160" #identifiant de la zone cible
    N_ve = 50 #nombre de véhicules électriques à générer

    folder = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/codes/"
    bat_file = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/batiments-rennes-metropole.json" # fichier volumineux, mis à part pour pouvoir faire des git push
    iris_file = folder + "data_global/iris_version_rennes_metropole.json"
    parkings_file = folder + "data_global/parkings.json"
    transfo_file = folder + "data_global/poste-electrique-total.csv"

    bat_filtres = folder + "data_local/batiments_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    parkings_filtres = folder + "data_local/parkings_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    transfo_filtres_path = folder + "data_local/transfo_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances_bat_park = folder + "data_local/matrice_distances_bat-park_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances_tf_park = folder + "data_local/matrice_distances_tf-park_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"

    selected_sites = [{'gml_id': 'v_parking.5272', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.5981796810755085, 'lat': 48.131050605364955}}, {'gml_id': 'v_parking.6157', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.610297454250723, 'lat': 48.12509726328288}}, {'gml_id': 'v_parking.6169', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.6090822211252582, 'lat': 48.12395455634806}}, {'gml_id': 'v_parking.6179', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.6105903197320801, 'lat': 48.1236542823524}}, {'gml_id': 'v_parking.6181', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.6112321790149753, 'lat': 48.12425221113884}}, {'gml_id': 'v_parking.6143', 'nb_bornes_installees': 2, 'geo_point': {'lon': -1.6023755835466336, 'lat': 48.12566515944683}}, {'gml_id': 'v_parking.5271', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.5975394614392338, 'lat': 48.12915259974292}}, {'gml_id': 'v_parking.6174', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.610706506739586, 'lat': 48.12567738410442}}, {'gml_id': 'v_parking.6182', 'nb_bornes_installees': 1, 'geo_point': {'lon': -1.6071810676722722, 'lat': 48.12481266978351}}]

    # traiter_batiments(bat_file, iris_file, bat_filtres, zone_id, N_ve)
    # traiter_parkings(parkings_file, iris_file, parkings_filtres, zone_id)    
    # traiter_transfo(transfo_file, iris_file, transfo_filtres_path, zone_id)
    # calculer_matrice_distances_bat_parkings(bat_filtres, parkings_filtres, matrice_distances_bat_park)
    # calculer_matrice_distances_tf_parkings(transfo_filtres_path, selected_sites, matrice_distances_tf_park)
