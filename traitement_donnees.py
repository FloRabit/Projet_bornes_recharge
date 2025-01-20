import json
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


def calculer_matrice_distances(bat_file_path, parkings_file, output_file):
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

if __name__ == "__main__":

    folder = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/codes/data_global/"
    bat_file = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/batiments-rennes-metropole.json" # fichier volumineux, mis à part pour pouvoir faire des git push
    zones_file = folder + "iris_version_rennes_metropole.json"
    parkings_file = folder + "parkings.json"


    zone_id = "iris.163" #identifiant de la zone cible
    N_ve = 50 #nombre de véhicules électriques à générer

    bat_filtres = folder + "batiments_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    parkings_filtres = folder + "parkings_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances = folder + "matrice_distances_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"

    # traiter_batiments(bat_file, zones_file, bat_filtres, zone_id, N_ve)
    # traiter_parkings(parkings_file, zones_file, parkings_filtres, zone_id)
    # calculer_matrice_distances(bat_filtres, parkings_filtres, matrice_distances)