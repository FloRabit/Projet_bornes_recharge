import requests

# URL de l'API fournissant le fichier CSV
api_url = "https://tabular-api.data.gouv.fr/api/resources/333270dc-3370-40d9-b488-5c563226319a/data/csv/"

# Chemin du fichier CSV de sortie
output_csv_path = "/Users/flo/Documents/Centrale_Supelec/2A/Projet_S7/donnees_parking.csv"

# Télécharger et enregistrer le fichier CSV
def download_csv(api_url, output_csv_path):
    response = requests.get(api_url, stream=True)
    response.raise_for_status()  # Vérifie si la requête a réussi

    # Écrire le contenu dans le fichier local
    with open(output_csv_path, mode="wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
    print(f"Fichier CSV téléchargé et enregistré à : {output_csv_path}")

# Appeler la fonction pour télécharger et enregistrer le CSV
download_csv(api_url, output_csv_path)