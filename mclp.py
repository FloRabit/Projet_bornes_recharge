import json
from ortools.linear_solver import pywraplp

def mclp_deloc(bat_file_path, parkings_file_path, mat_distances_file_path, p, Dmax):
    """
    Résout le problème Maximal Covering Location Problem (MCLP) à partir de données JSON.

    Args:
        - bat_file_path (str): Chemin du fichier JSON contenant les bâtiments de la zone à couvrir.
        - parkings_file_path (str): Chemin du fichier JSON contenant les parkings de la zone à couvrir.
        - mat_distances_file_path (str): Chemin du fichier JSON contenant la matrice des distances entre les batiments de bat_file_path et les parkings de parkings_file_path.
        - p (int): Nombre maximal de bornes à implanter.
        - Dmax (float): Distance maximale de couverture.

    Returns:
        - selected_sites : dict, nombre de bornes à implanter dans chaque parking {parking_id: nombre_de_bornes}.
        - max_coverage : float, couverture totale maximale.
    """
    import json
    from ortools.linear_solver import pywraplp

    # Charger les données des bâtiments
    with open(bat_file_path, 'r', encoding='utf-8') as f:
        data_bat = json.load(f)

    # Extraire les bâtiments de la structure JSON
    batiments = data_bat.get("batiments", [])

    # Charger les données des parkings
    with open(parkings_file_path, 'r', encoding='utf-8') as f:
        data_parkings = json.load(f)
    
    # Extraire les parkings de la structure JSON
    parkings = data_parkings.get("parkings", [])

    # Charger la matrice des distances
    with open(mat_distances_file_path, 'r', encoding='utf-8') as f:
        T = json.load(f)  # Matrice des distances {id_batiment: {id_parking: distance}}

    # Extraire les informations nécessaires
    demande_ids = [batiment['gml_id'] for batiment in batiments if batiment['nb_ve'] > 0]
    demande_weights = {batiment['gml_id']: batiment['nb_ve'] for batiment in batiments if batiment['nb_ve'] > 0}

    site_ids = [parking['gml_id'] for parking in parkings]
    C = {parking['gml_id']: parking['max_bornes'] for parking in parkings}

    # Initialisation du solveur
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        raise Exception("Erreur lors de la création du solveur.")

    # Variables de décision
    # Nombre de bornes installées dans chaque parking (entre 0 et max_bornes)
    x = {i: solver.IntVar(0, C[i], f"x[{i}]") for i in site_ids}

    # Quantité de demande couverte pour chaque bâtiment
    y = {j: solver.IntVar(0, demande_weights[j], f"y[{j}]") for j in demande_ids}

    # Allocation de demande de chaque bâtiment à chaque parking
    z = {
    (j, i): solver.IntVar(0, demande_weights[j], f"z[{j},{i}]")
    for j in demande_ids
    for i in site_ids
    if any(entry["batiment_id"] == j and i in entry["distances"] and entry["distances"][i] <= Dmax for entry in T)
}

    # Contraintes

    # 1. Limitation du nombre total de bornes à implanter
    solver.Add(solver.Sum(x[i] for i in site_ids) <= p)

    # 2. Une demande couverte est alimentée par au moins un parking à distance Dmax
    for j in demande_ids:
        solver.Add(y[j] == solver.Sum(z[(j, i)] for i in site_ids if (j, i) in z))

    # 3. Une demande ne peut être couverte que si le parking est à distance Dmax
    for j in demande_ids:
        for i in site_ids:
            if (j, i) in z:
                solver.Add(z[(j, i)] <= demande_weights[j])  # La couverture ne peut pas excéder la demande
                solver.Add(z[(j, i)] <= x[i] * demande_weights[j])  # Dépend des bornes disponibles

    # 4. Respect de la capacité des bornes dans chaque parking
    for i in site_ids:
        solver.Add(solver.Sum(z[(j, i)] for j in demande_ids if (j, i) in z) <= x[i] * C[i])

    # Objectif : maximiser la demande couverte
    solver.Maximize(solver.Sum(y[j] for j in demande_ids))

    # Résolution
    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL:
        selected_sites = {i: int(x[i].solution_value()) for i in site_ids if x[i].solution_value() > 0}
        max_coverage = solver.Objective().Value()

        return selected_sites, max_coverage
    else:
        raise Exception("Le solveur n'a pas trouvé de solution optimale.")
    


if __name__ == '__main__':

    zone_id = "iris.163" #identifiant de la zone cible

    folder = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/codes/data_global/"
    bat_file = folder + "batiments-rennes-metropole.json"
    zones_file = folder + "iris_version_rennes_metropole.json"
    parkings_file = folder + "parkings.json"

    bat_filtres = folder + "batiments_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    parkings_filtres = folder + "parkings_rennes_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"
    matrice_distances = folder + "matrice_distances_" + zone_id.split(".")[0] + "_" + zone_id.split(".")[1] + ".json"

    p=10
    Dmax=500

    selected_sites, max_coverage = mclp(bat_filtres, parkings_filtres, matrice_distances, p, Dmax)

    print("Sites sélectionnés:", selected_sites)
    print("Couverture maximale:", max_coverage)
    

