import traitement_donnees
import mclp 
import trace_carte_bornes
import json
import os # Pour le nettoyage des fichiers au lancement de la simulation
import matplotlib.pyplot as plt

def supprimer_tous_les_fichiers(dossier):
    """
    Supprime tous les fichiers d'un dossier local.

    Args:
        dossier (str): Chemin absolu ou relatif du dossier cible.
    """
    try:
        # Parcourir tous les fichiers dans le dossier
        for fichier in os.listdir(dossier):
            chemin_fichier = os.path.join(dossier, fichier)

            # Vérifier si c'est un fichier (et pas un dossier)
            if os.path.isfile(chemin_fichier):
                os.remove(chemin_fichier)  # Supprimer le fichier
                print(f"Supprimé : {chemin_fichier}")
    except Exception as e:
        print(f"Erreur : {e}")


if __name__ == "__main__":
    # Paramètres
    zone_id = "iris.160" #identifiant de la zone cible
    N_ve_2000 = 50 #nombre de véhicules électriques à générer
    cout_moy_22kW = 1000
    Rmax=200
    p=20
    max_connections_per_transformer = 3

    # Fichiers entrée/sortie
    folder = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/codes/"
    bat_file = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/batiments-rennes-metropole.json" # fichier volumineux, mis à part pour pouvoir faire des git push
    iris_file = folder + "data_global/iris_version_rennes_metropole.json"
    parkings_file = folder + "data_global/parkings.json"
    transfo_file = folder + "data_global/poste-electrique-total.csv"


    bat_filtres = folder + "data_local/batiments_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    parkings_filtres = folder + "data_local/parkings_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    transfo_filtres = folder + "data_local/transfo_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances_bat_park = folder + "data_local/matrice_distances_bat-park_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances_tf_park = folder + "data_local/matrice_distances_tf-park_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    img_plot_park_bat = folder + "data_local/img_plot_park_bat_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".png"
    img_plot_tf_park = folder + "data_local/img_plot_tf_park_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".png"


    # Nettoyage des fichiers locaux
    supprimer_tous_les_fichiers(folder + "data_local")
    
    # Traitement des données
    traitement_donnees.traiter_batiments(bat_file, iris_file, bat_filtres, zone_id, N_ve_2000)
    traitement_donnees.traiter_parkings(parkings_file, iris_file, parkings_filtres, zone_id)
    traitement_donnees.traiter_transfo(transfo_file, iris_file, transfo_filtres, zone_id)
    traitement_donnees.calculer_matrice_distances_bat_parkings(bat_filtres, parkings_filtres, matrice_distances_bat_park)

    # Résolution du problème
    selected_sites, max_coverage = mclp.mclp_deloc(bat_filtres, parkings_filtres, matrice_distances_bat_park, p, Rmax)

    traitement_donnees.calculer_matrice_distances_tf_parkings(transfo_filtres, selected_sites, matrice_distances_tf_park)

    # Affichage de la carte
    trace_carte_bornes.plot_parking_and_buildings_with_basemap(iris_file, bat_filtres, zone_id, selected_sites, Rmax, img_plot_park_bat )
    trace_carte_bornes.plot_parking_and_tf_with_basemap(iris_file, transfo_filtres, selected_sites, matrice_distances_tf_park, zone_id, Rmax, max_connections_per_transformer, output_file=img_plot_tf_park)