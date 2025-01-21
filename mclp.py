import json
from ortools.linear_solver import pywraplp

    
def mclp_deloc(bat_file_path, parkings_file_path, mat_distances_file_path, p, Rmax, cout_unitaire):
    """
    Résout le problème Maximal Covering Location Problem (MCLP) avec une dimension économique et géolocalisation.

    Args:
        - bat_file_path (str): Chemin du fichier JSON contenant les bâtiments de la zone à couvrir.
        - parkings_file_path (str): Chemin du fichier JSON contenant les parkings de la zone à couvrir.
        - mat_distances_file_path (str): Chemin du fichier JSON contenant la matrice des distances entre les bâtiments et les parkings.
        - p (int): Nombre maximal de bornes à implanter.
        - Rmax (float): Distance maximale de couverture.
        - cout_unitaire (float): Coût unitaire pour une borne.

    Returns:
        - selected_sites : list, informations sur les parkings sélectionnés avec leur géolocalisation et coût total.
        - rapport_couverture_cout : float, rapport couverture/coût total.
    """

    # Charger les données des bâtiments, parkings et distances
    with open(bat_file_path, 'r', encoding='utf-8') as f:
        data_bat = json.load(f)
    with open(parkings_file_path, 'r', encoding='utf-8') as f:
        data_parkings = json.load(f)
    with open(mat_distances_file_path, 'r', encoding='utf-8') as f:
        T = json.load(f)

    # Extraire les informations nécessaires
    demande_ids = [bat['gml_id'] for bat in data_bat.get("batiments", []) if bat['nb_ve_potentiel'] > 0]
    demande_weights = {bat['gml_id']: bat['nb_ve_potentiel'] for bat in data_bat.get("batiments", []) if bat['nb_ve_potentiel'] > 0}
    site_ids = [park['gml_id'] for park in data_parkings.get("parkings", [])]
    C = {park['gml_id']: park['max_bornes'] for park in data_parkings.get("parkings", [])}
    parking_geopoints = {park['gml_id']: park['geo_point_2d'] for park in data_parkings.get("parkings", [])}

    print(data_parkings.get("recapitulatif"))
    print ("okkkkkkkkkkkkkkkkkkkkk")

    total_max_bornes = data_parkings.get("recapitulatif", [])["total_max_bornes"]
    nb_ve_total = data_bat.get("recapitulatif", [])["nb_ve_total"]

    # Initialisation du solveur
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        raise Exception("Erreur lors de la création du solveur.")

    # Variables de décision
    x = {i: solver.IntVar(0, C[i], f"x[{i}]") for i in site_ids}  # Nombre de bornes installées
    y = {j: solver.NumVar(0, demande_weights[j], f"y[{j}]") for j in demande_ids}  # Demande couverte
    z = {}
    for entry in T:
        batiment_id = entry["batiment_id"]
        if batiment_id in demande_ids:
            for parking_id, distance in entry["distances"].items():
                if distance <= Rmax and parking_id in site_ids:
                    z[(batiment_id, parking_id)] = solver.NumVar(0, demande_weights[batiment_id], f"z[{batiment_id},{parking_id}]")

    # Variables auxiliaires pour les coûts ajustés
    discount_cost = {i: solver.NumVar(0, float('inf'), f"discount_cost[{i}]") for i in site_ids}
    adjusted_costs = {i: solver.NumVar(0, float('inf'), f"adjusted_cost[{i}]") for i in site_ids}

    # Contraintes pour calculer discount_cost et adjusted_costs
    for i in site_ids:
        solver.Add(discount_cost[i] >= 0)
        solver.Add(discount_cost[i] <= x[i] * 0.5)  # Plafonner le discount à 50%
        solver.Add(adjusted_costs[i] == x[i] * cout_unitaire - discount_cost[i] * cout_unitaire)

    # Calcul du coût total
    cost_total = solver.NumVar(0, float('inf'), "cost_total")
    solver.Add(cost_total == solver.Sum(adjusted_costs[i] for i in site_ids))

    # Contraintes pour la demande couverte
    solver.Add(solver.Sum(x[i] for i in site_ids) <= p)
    for j in demande_ids:
        solver.Add(y[j] == solver.Sum(z[(j, i)] for i in site_ids if (j, i) in z))
    for j in demande_ids:
        for i in site_ids:
            if (j, i) in z:
                solver.Add(z[(j, i)] <= demande_weights[j])
                solver.Add(z[(j, i)] <= x[i] * demande_weights[j])
    for i in site_ids:
        solver.Add(solver.Sum(z[(j, i)] for j in demande_ids if (j, i) in z) <= x[i] * C[i])
    
    # Fonction objectif : maximiser couverture et minimiser coût.
    # Impossible de faire couverture / coût car la fonction objectif doit être linéaire, donc on maximise alpha*couverture - beta*coût
    solver.Maximize(1/nb_ve_total * solver.Sum(y[j] for j in demande_ids) - 1/(total_max_bornes*cout_unitaire) * cost_total )

    # Résolution
    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL:
        selected_sites = [
            {
                "gml_id": i,
                "nb_bornes_installees": int(x[i].solution_value()),
                "cout_total": adjusted_costs[i].solution_value(),
                "geo_point_2d": parking_geopoints.get(i, None)  # Ajouter les coordonnées géographiques
            }
            for i in site_ids if x[i].solution_value() > 0
        ]
        rapport_couverture_cout = solver.Objective().Value()
        return selected_sites, rapport_couverture_cout
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
    

