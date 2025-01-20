import traitement_donnees
import mclp 
import trace_carte_bornes
import json

import matplotlib.pyplot as plt

def afficher_rapport_couverture_cout(
    bat_file_path, parkings_file_path, mat_distances_file_path, Rmax, cout_moy_22kW
):
    """
    Affiche le rapport couverture/coût pour p allant de 0 au nombre maximal de bornes.

    Args:
        - bat_file_path (str): Chemin du fichier JSON contenant les bâtiments de la zone à couvrir.
        - parkings_file_path (str): Chemin du fichier JSON contenant les parkings de la zone à couvrir.
        - mat_distances_file_path (str): Chemin du fichier JSON contenant la matrice des distances.
        - Rmax (float): Distance maximale de couverture.
        - cout_moy_22kW (float): Coût moyen d'installation d'une borne 22 kW.

    Returns:
        - None
    """

    with open(parkings_file_path, 'r', encoding='utf-8') as f:
        parkings_recap = json.load(f)["recapitulatif"]
    
    # Variables pour les calculs
    total_max_bornes = parkings_recap["total_max_bornes"]
    rapport_couverture_cout = []

    # Calcul pour chaque valeur de p
    for p in range(1, total_max_bornes + 1):
        try:
            # Appeler votre fonction MCLP
            selected_sites, max_coverage = mclp.mclp_deloc(
                bat_file_path, parkings_file_path, mat_distances_file_path, p, Rmax
            )

            rapport = max_coverage / (cout_moy_22kW * p)
            
            rapport_couverture_cout.append((p, rapport))

        except Exception as e:
            print(f"Erreur pour p = {p}: {e}")
            rapport_couverture_cout.append((p, 0))

    # Extraire les valeurs pour le tracé
    p_values, rapports = zip(*rapport_couverture_cout)

    print(rapport_couverture_cout)
    print("###################")
    print (p_values)
    print("###################")
    print (rapports)
        

    # Tracer le graphique
    plt.figure(figsize=(10, 6))
    plt.plot(p_values, rapports, marker='o', linestyle='-', color='b', label="Rapport couverture/coût")
    plt.title("Évolution du rapport couverture/coût en fonction de p", fontsize=16)
    plt.xlabel("Nombre de bornes (p)", fontsize=12)
    plt.ylabel("Rapport couverture/coût", fontsize=12)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    folder = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/codes/data_global/"
    bat_file = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/batiments-rennes-metropole.json" # fichier volumineux, mis à part pour pouvoir faire des git push
    zone_file = folder + "iris_version_rennes_metropole.json"
    parkings_file = folder + "parkings.json"


    zone_id = "iris.160" #identifiant de la zone cible
    N_ve_2000 = 50 #nombre de véhicules électriques à générer
    cout_moy_22kW = 1000
    Rmax=200
    p=20

    bat_filtres = folder + "batiments_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    parkings_filtres = folder + "parkings_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances = folder + "matrice_distances_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"


    # Traitement des données
    traitement_donnees.traiter_batiments(bat_file, zone_file, bat_filtres, zone_id, N_ve_2000)
    traitement_donnees.traiter_parkings(parkings_file, zone_file, parkings_filtres, zone_id)
    traitement_donnees.calculer_matrice_distances(bat_filtres, parkings_filtres, matrice_distances)

    # Résolution du problème
    selected_sites, max_coverage = mclp.mclp_deloc(bat_filtres, parkings_filtres, matrice_distances, p, Rmax)

    # Affichage de la carte
    trace_carte_bornes.plot_parking_and_buildings_with_basemap(zone_file,parkings_filtres,bat_filtres,zone_id,selected_sites, Rmax)

    # afficher_rapport_couverture_cout(bat_filtres, parkings_filtres, matrice_distances, Rmax, cout_moy_22kW)
