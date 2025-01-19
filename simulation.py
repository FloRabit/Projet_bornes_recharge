import traitement_donnees
import mclp 
import trace_carte_bornes

if __name__ == "__main__":
    folder = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/codes/data_global/"
    bat_file = folder + "batiments-rennes-metropole.json"
    zone_file = folder + "iris_version_rennes_metropole.json"
    parkings_file = folder + "parkings.json"


    zone_id = "iris.163" #identifiant de la zone cible
    N_ve = 50 #nombre de véhicules électriques à générer
    p=10
    Dmax=500

    bat_filtres = folder + "batiments_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    parkings_filtres = folder + "parkings_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances = folder + "matrice_distances_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"


    # Traitement des données
    traitement_donnees.traiter_batiments(bat_file, zone_file, bat_filtres, zone_id, N_ve)
    traitement_donnees.traiter_parkings(parkings_file, zone_file, parkings_filtres, zone_id)
    traitement_donnees.calculer_matrice_distances(bat_filtres, parkings_filtres, matrice_distances)

    # Résolution du problème
    selected_sites, max_coverage = mclp.mclp_deloc(bat_filtres, parkings_filtres, matrice_distances, p, Dmax)

    # Affichage de la carte
    trace_carte_bornes.plot_parking_and_buildings_with_basemap(
        zone_file,
        parkings_filtres,
        bat_filtres,
        zone_id,
        selected_sites
    )

