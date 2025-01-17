import pandas as pd 
import json


# Fonction pour extraire les données et les sauvegarder pour usage ultérieur, sous forme de fichiers CSV et JSON. Ce sont des données simplifiées.
def extraction_donnees (parkings_file, iris_file, distances_file, S_file, W_file, T_file, demande_iris):

    # Charger les données
    parkings_df = pd.read_csv(parkings_file, delimiter=";")
    iris_df = pd.read_csv(iris_file, delimiter=";")
    distances_df = pd.read_csv(distances_file, index_col=0, delimiter=",")

    # Création de la liste S (emplacements potentiels)
    if 'gml_id' not in parkings_df.columns:
        raise ValueError("La colonne 'gml_id' est absente du fichier des parkings.")
    S = list(parkings_df['gml_id'])

    # Création de la liste W (lieux de demande avec pondération)
    if 'gml_id' not in iris_df.columns :
        raise ValueError("Les colonnes 'gml_id' est absente du fichier IRIS.")
    W = [(row['gml_id'], demande_iris) for _, row in iris_df.iterrows()]

    print(f"S : \n{S}")
    print("############################################")
    print(f"Colonnes initiales de distances_df : \n{distances_df.columns}")
    print("############################################")
    print(f"Colonnes initiales de distances_df, élément 0: \n{distances_df.columns[0]}")

    # Création de la matrice des distances T
    if set(distances_df.columns) != set(S): # Vérifier que les colonnes correspondent aux identifiants des parkings
        raise ValueError("Les colonnes du fichier des distances ne correspondent pas aux identifiants des parkings.")
    if set(distances_df.index) != set([w[0] for w in W]):
        raise ValueError("Les lignes du fichier des distances ne correspondent pas aux identifiants des lieux de demande.")
    T = distances_df.to_dict(orient='index')  # Convertir en dictionnaire {j: {i: distance}}

    # Vérification des structures
    print("Liste S :", S[:5], "...")
    print("Liste W :", W[:5], "...")
    print("Extrait de T :", {k: v for k, v in list(T.items())[:5]})


    # Sauvegarder S et W au format CSV
    pd.DataFrame({'gml_id': S}).to_csv(S_file, index=False)
    pd.DataFrame(W, columns=['gml_id', 'demande']).to_csv(W_file, index=False)

    # Sauvegarder T au format JSON pour compatibilité
    import json
    with open(T_file, "w") as f:
        json.dump(T, f)

    print(f"Données sauvegardées :\nS -> {S_file}\nW -> {W_file}\nT -> {T_file}")


def capa_bornes (S, list_capa, capa_file) :
    site_ids = [s[1][0] for s in S.iterrows()]  # Liste des identifiants d'emplacements potentiels
    capa = dict(zip(site_ids, list_capa))  # Dictionnaire des capacités des bornes
    with open(capa_file, "w") as f:
        json.dump(capa, f)

if __name__ == "__main__":

    S_file = "data/S_list.csv"
    S_df = pd.read_csv(S_file, delimiter=";")
    capa_file = "data/capa.json"
    site_ids = [s[1][0] for s in S_df.iterrows()]
    n= len(site_ids)
    
    list_capa = [30 for _ in range(n)]

    capa_bornes(S_df, list_capa, capa_file)

