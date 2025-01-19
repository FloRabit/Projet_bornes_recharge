import requests

# URL de base du service WFS
BASE_URL = "https://data.rennesmetropole.fr/api/explore/v2.1/catalog/datasets/bornes-de-recharge-dediees-aux-vehicules-electriques-sur-le-territoire-de-rennes/files/d5c2cb8fa5d4d394c289b8d2473c97d8"

# Paramètres pour récupérer les données
params = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeName": "bornes_recharge:v_bornes_recharge",  # Nom de la couche
    "outputFormat": "text/csv"
}

# Chemin du fichier de sortie
OUTPUT_FILE = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/bornes_actuelles_rennes.csv"

# Requête pour récupérer les données
response = requests.get(BASE_URL, params=params)

# Vérifier si la requête a réussi
if response.status_code == 200:
    # Sauvegarder les données dans un fichier CSV
    with open(OUTPUT_FILE, "wb") as file:
        file.write(response.content)
    print(f"Les données ont été téléchargées et enregistrées dans : {OUTPUT_FILE}")
else:
    # Gérer les erreurs
    print(f"Erreur lors de la récupération des données : {response.status_code}")
    print(f"Message : {response.text}")