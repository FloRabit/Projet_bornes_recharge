import json
from ortools.linear_solver import pywraplp

    
def mclp_deloc(bat_file_path, parkings_file_path, mat_distances_file_path, p, Rmax):
    """
    Résout le problème Maximal Covering Location Problem (MCLP) à partir de données JSON.

    Args:
        - bat_file_path (str): Chemin du fichier JSON contenant les bâtiments de la zone à couvrir.
        - parkings_file_path (str): Chemin du fichier JSON contenant les parkings de la zone à couvrir.
        - mat_distances_file_path (str): Chemin du fichier JSON contenant la matrice des distances entre les batiments de bat_file_path et les parkings de parkings_file_path.
        - p (int): Nombre maximal de bornes à implanter.
        - Rmax (float): Distance maximale de couverture.

    Returns:
        - selected_sites : dict, nombre de bornes à implanter dans chaque parking {parking_id: nombre_de_bornes}.
        - max_coverage : float, couverture totale maximale.
    """
    # Charger les données des bâtiments
    with open(bat_file_path, 'r', encoding='utf-8') as f:
        data_bat = json.load(f)

    # Charger les données des parkings
    with open(parkings_file_path, 'r', encoding='utf-8') as f:
        data_parkings = json.load(f)
    
    # Charger la matrice des distances
    with open(mat_distances_file_path, 'r', encoding='utf-8') as f:
        T = json.load(f)  # Liste des distances

    # Extraire les informations nécessaires
    demande_ids = [batiment['gml_id'] for batiment in data_bat.get("batiments", []) if batiment['nb_ve_potentiel'] > 0]
    demande_weights = {batiment['gml_id']: batiment['nb_ve_potentiel'] for batiment in data_bat.get("batiments", []) if batiment['nb_ve_potentiel'] > 0}

    site_ids = [parking['gml_id'] for parking in data_parkings.get("parkings", [])]
    C = {parking['gml_id']: parking['max_bornes'] for parking in data_parkings.get("parkings", [])}

    # Charger les données des parkings pour récupérer les informations de localisation pour les sites sélectionnés
    parking_info = {parking["gml_id"]: parking["geo_point_2d"] for parking in data_parkings.get("parkings", [])}

    # Initialisation du solveur
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        raise Exception("Erreur lors de la création du solveur.")

    # Variables de décision
    x = {i: solver.IntVar(0, C[i], f"x[{i}]") for i in site_ids}  # Nombre de bornes installées
    y = {j: solver.NumVar(0, demande_weights[j], f"y[{j}]") for j in demande_ids}  # Demande couverte
    z = {}

    # Création de z uniquement pour les parkings à distance <= Rmax
    for entry in T:
        batiment_id = entry["batiment_id"]
        if batiment_id in demande_ids:
            for parking_id, distance in entry["distances"].items():
                if distance <= Rmax and parking_id in site_ids:
                    z[(batiment_id, parking_id)] = solver.NumVar(0, demande_weights[batiment_id], f"z[{batiment_id},{parking_id}]")

    # Contraintes
    solver.Add(solver.Sum(x[i] for i in site_ids) <= p)  # Limite du nombre de bornes

    for j in demande_ids:
        solver.Add(y[j] == solver.Sum(z[(j, i)] for i in site_ids if (j, i) in z))  # Demande couverte

    for j in demande_ids:
        for i in site_ids:
            if (j, i) in z:
                solver.Add(z[(j, i)] <= demande_weights[j])  # Limite de couverture par bâtiment
                solver.Add(z[(j, i)] <= x[i] * demande_weights[j])  # Dépend des bornes disponibles

    for i in site_ids:
        solver.Add(solver.Sum(z[(j, i)] for j in demande_ids if (j, i) in z) <= x[i] * C[i])  # Capacité du parking

    # Objectif : maximiser la demande couverte
    solver.Maximize(solver.Sum(y[j] for j in demande_ids))

    # Résolution
    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL:
        selected_sites = [
            {
                "gml_id": i,
                "nb_bornes_installees": int(x[i].solution_value()),
                "geo_point": parking_info.get(i, None)
            }
            for i in site_ids if x[i].solution_value() > 0
        ]
        max_coverage = solver.Objective().Value()
        return selected_sites, max_coverage
    else:
        raise Exception("Le solveur n'a pas trouvé de solution optimale.")


if __name__ == '__main__':

    zone_id = "iris.160" #identifiant de la zone cible
    p=10
    Rmax=500
    cout_unitaire = 3000

    folder = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/codes/"
    bat_file = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/batiments-rennes-metropole.json" # fichier volumineux, mis à part pour pouvoir faire des git push
    iris_file = folder + "data_global/iris_version_rennes_metropole.json"
    parkings_file = folder + "data_global/parkings.json"

    bat_filtres = folder + "data_local/batiments_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    parkings_filtres = folder + "data_local/parkings_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances_bat_park = folder + "data_local/matrice_distances_bat-park_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances_tf_park = folder + "data_local/matrice_distances_tf-park_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"

    selected_sites, rapport_couverture_cout = mclp_deloc(bat_filtres, parkings_filtres, matrice_distances_bat_park, p, Rmax, cout_unitaire)

    print("Sites sélectionnés:", selected_sites)
    print("Couverture maximale:", rapport_couverture_cout)
    

