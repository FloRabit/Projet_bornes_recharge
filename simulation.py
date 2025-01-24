import traitement_donnees
import mclp 
import tracer_cartes
import os # Pour le nettoyage des fichiers au lancement de la simulation
import matplotlib.pyplot as plt
import json

def nettoyer_dossier(dossier):
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


def couts (selected_sites_path, cout_unitaire) :
    """
    Calcul du coût total d'installation des bornes de recharge

    Args:
        selected_sites (list): Liste des sites sélectionnés
        cout_unitaire (int): Coût unitaire d'installation d'une borne de recharge

    Returns:
        int: Coût total d'installation des bornes de recharge
    """
    # Charger le fichier JSON des sites
    with open(selected_sites_path, 'r', encoding='utf-8') as f:
        selected_sites = json.load(f)

    # cout_total = sum(site.get("nb_bornes_installees", 0) or 0 for site in selected_sites) * cout_unitaire
    cout_total = 0
    for site in selected_sites:
        nb_bornes = site.get("nb_bornes_installees", 0)
        cout_total += nb_bornes * cout_unitaire * (1 - min(0.1 * (nb_bornes - 1), 0.5))
    
    print(f"Coût total d'installation des bornes de recharge : {cout_total} €")
    return cout_total


if __name__ == "__main__":

    ############################################################
    # Paramètres de la simulation : Variables
    ############################################################

    zone_id = "iris.163"                    # identifiant de la zone cible
    N_ve_2000 = 50                          # nombre de véhicules électriques à générer, normalisé pour 2000 habitants
    cout_moy_22kW = 3000                    # cout moyen d'installation d'une borne de recharge 22kW
    Rmax=200                                # rayon de couverture d'une borne de recharge
    p=20                                    # nombre de bornes à sélectionner
    max_connections_per_transformer = 3     # nombre maximal de bornes connectées à un poste de transformation pour être assuré de la sécurité du réseau


    ############################################################
    # Paramètres de la simulation : Chemins des fichiers
    ############################################################

    # Fichiers de données initiaux
    bat_file = "../batiments-rennes-metropole.json" # fichier volumineux, mis à part pour pouvoir faire des git push
    iris_file = "data_global/iris_version_rennes_metropole.json"
    parkings_file = "data_global/parkings.json"
    transfo_file = "data_global/poste-electrique-total.csv"

    # Fichiers de données intermédiaires
    bat_filtres = "data_local/batiments_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    parkings_filtres = "data_local/parkings_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    transfo_filtres = "data_local/transfo_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances_bat_park = "data_local/matrice_distances_bat-park_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances_tf_park = "data_local/matrice_distances_tf-park_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"


    # Fichiers de sortie
    selected_sites_path = "output/SOLUTION_sites_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    asso_tf_bornes_path = "output/SOLUTION_asso_tf_bornes" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    img_plot_park_bat = "output/img_plot_park_bat_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".png"
    img_plot_tf_park = "output/img_plot_tf_park_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".png"


    ############################################################
    # Simulation
    ############################################################

    # Nettoyage des fichiers locaux
    nettoyer_dossier("data_local")
    nettoyer_dossier("output")
    
    # Traitement des données
    traitement_donnees.traiter_batiments(bat_file, iris_file, bat_filtres, zone_id, N_ve_2000)
    traitement_donnees.traiter_parkings(parkings_file, iris_file, parkings_filtres, zone_id)
    traitement_donnees.traiter_transfo(transfo_file, iris_file, transfo_filtres, zone_id)
    traitement_donnees.calculer_matrice_distances_bat_parkings(bat_filtres, parkings_filtres, matrice_distances_bat_park)

    # Résolution du problème
    selected_sites, max_coverage = mclp.mclp_deloc(bat_filtres, parkings_filtres, matrice_distances_bat_park, selected_sites_path, p, Rmax)    
    cout_total = couts(selected_sites_path, cout_moy_22kW)

    traitement_donnees.calculer_matrice_distances_tf_parkings(transfo_filtres, selected_sites_path, matrice_distances_tf_park)
    mclp.association_bornes_transfo(selected_sites_path, transfo_filtres, asso_tf_bornes_path, max_connections_per_transformer)


    # Affichage de la carte
    tracer_cartes.plot_parking_and_buildings_with_basemap(iris_file, bat_filtres, zone_id, selected_sites_path, Rmax, img_plot_park_bat )
    tracer_cartes.plot_parking_and_tf_with_basemap(iris_file, transfo_filtres, selected_sites_path, asso_tf_bornes_path, zone_id, Rmax, output_file=img_plot_tf_park)


    # Affichage des résultats
    print ("\n")
    print("########################################################################################")
    print("Résultats de la simulation \n")
    print("Zone cible :", zone_id)
    print("Nombre de sites sélectionnés :", sum(1 for _ in selected_sites))
    print("Nombre de bornes installées :", sum(site.get("nb_bornes_installees", 0) or 0 for site in selected_sites))
    print(f"Cout de l'installation : {cout_total} \n")
