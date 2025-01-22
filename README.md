Penser à expliquer comment télécharger les données initiales (liens), ils ne peuvent pas être mis sur github.
Penser à faire les requierments 


# **Optimisation des Bornes de Recharge Électrique - Projet MCLP**

## **Contexte du problème**

Avec la transition vers des modes de transport plus durables, la demande pour des infrastructures de recharge électrique ne cesse de croître. Cependant, l'implantation de bornes de recharge doit être pensée de manière stratégique pour maximiser leur efficacité tout en maîtrisant les coûts d'installation et d'adaptation du réseau. 

Ce projet s'intéresse spécifiquement à la ville de Rennes et propose une solution basée sur l'algorithme **MCLP (Maximal Covering Location Problem)**. L'objectif est de répondre au mieux aux besoins en recharge des habitants en optimisant le positionnement des bornes dans les parkings tout en respectant des contraintes budgétaires et géographiques.

---

## **Hypothèses réalisées**

Pour modéliser le problème, nous avons établi quelques hypothèses :

- **Demande en véhicules électriques (VE)** : Chaque bâtiment possède une demande calculée en fonction du nombre potentiel d'habitants adultes. Si un bâtiment n’a pas de demande en VE, il n'est pas pris en compte dans l'optimisation.
- **Capacité des parkings** : Les parkings sont limités en nombre de bornes installables, en fonction de leur taille :
  - Moins de 20 places : 1 borne.
  - Entre 20 et 50 places : 2 bornes.
  - Plus de 50 places : 4 bornes.
- **Rayon de couverture** : Une borne peut desservir tous les bâtiments situés dans un rayon maximal défini (\( R_{\text{max}} \)).
- **Modèle de coût** : Le coût des bornes suit une dégressivité pour refléter les économies réalisées lorsqu'on installe plusieurs bornes dans un même parking. Par exemple, 5 bornes dans un parking coûtent moins que 5 bornes réparties dans 5 parkings différents.

---

## **Bases de données utilisées**

Pour ce projet, nous avons utilisé plusieurs fichiers JSON, chacun jouant un rôle essentiel dans la modélisation et l'optimisation :

1. **Données des bâtiments** :
   - Contient les informations géographiques et démographiques des bâtiments de la zone étudiée.
   - Les principaux champs incluent les coordonnées géographiques (`geo_point_2d`), l'identifiant unique (`gml_id`) et la demande en VE (`nb_ve_potentiel`).

2. **Données des parkings** :
   - Recense les parkings disponibles avec leurs caractéristiques.
   - Les champs importants sont : le nombre maximal de bornes installables (`max_bornes`), les coordonnées géographiques (`geo_point_2d`) et l'identifiant unique (`gml_id`).

3. **Matrice des distances** :
   - Fournit les distances entre chaque bâtiment et chaque parking. 
   - Pour chaque bâtiment, un dictionnaire associe les identifiants des parkings à leurs distances.

4. **Données IRIS** :
   - Fournit les contours géographiques des zones IRIS de Rennes, permettant de visualiser la zone d'étude sur une carte.

---

## **Fonctionnement de l'algorithme MCLP**

L'algorithme MCLP est au cœur de ce projet. Il vise à maximiser la couverture des besoins en recharge tout en minimisant les coûts. Voici comment il fonctionne :

1. **Maximiser la couverture** : L'algorithme cherche à couvrir la demande en VE en positionnant stratégiquement les bornes dans les parkings.
2. **Minimiser le coût** : Le coût total est optimisé en tenant compte de la dégressivité des coûts par parking.
3. **Respect des contraintes** : 
   - Limitation du nombre total de bornes installées.
   - Respect des capacités maximales des parkings.
   - Prise en compte d’un rayon maximal de couverture pour chaque borne.

L'algorithme retourne les parkings sélectionnés, le nombre de bornes à installer dans chacun, et le rapport couverture/coût.

---

## **Modules principaux du programme**

Voici un aperçu des principaux fichiers de ce projet et de leurs fonctionnalités :

### **1. `mclp.py`**
Ce fichier contient l'implémentation de l'algorithme MCLP. En prenant en entrée les fichiers JSON des bâtiments, parkings et distances, il effectue l’optimisation et retourne les parkings sélectionnés, le nombre de bornes installées dans chacun, ainsi que le rapport couverture/coût.

### **2. `simulation.py`**
Ce module permet de réaliser des simulations variées en modifiant les paramètres comme \( p \) (nombre de bornes), \( R_{\text{max}} \) (rayon de couverture) ou le coût unitaire. Il permet de tester différents scénarios pour évaluer leurs impacts sur la couverture et le coût total.

### **3. `trace_cartes.py`**
Ce fichier génère des cartes interactives pour visualiser les résultats :
- Les bâtiments avec ou sans demande en VE.
- Les parkings sélectionnés avec le nombre de bornes installées.
- La délimitation géographique des zones IRIS.
- La couverture des bornes à l'aide de cercles correspondant au rayon \( R_{\text{max}} \).

### **4. `traitement_donnees.py`**
Ce module est dédié au nettoyage et au prétraitement des données :
- Filtrage des bâtiments et parkings pour ne conserver que ceux dans la zone IRIS choisie.
- Calcul des demandes potentielles pour chaque bâtiment.
- Création de la matrice des distances entre bâtiments et parkings.

---

## **Comment utiliser ce projet**

1. **Installer les dépendances** :
   - Python 3.9+
   - Bibliothèques nécessaires : `ortools`, `geopandas`, `shapely`, `matplotlib`, `contextily`.

   Pour installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

2. **Exécuter l'algorithme MCLP** :
   Lancez le fichier `mclp.py` avec vos fichiers JSON et les paramètres désirés (p, Rmax, etc.) pour obtenir les résultats d’optimisation.

3. **Visualiser les résultats** :
   Utilisez `trace_cartes.py` pour générer une carte illustrant les parkings sélectionnés et leur impact.

4. **Tester différents scénarios** :
   Modifiez les paramètres dans `simulation.py` pour explorer différentes solutions et trouver celle qui correspond le mieux à vos contraintes.

---

## **Contributions**

Si vous souhaitez contribuer ou proposer des améliorations, n'hésitez pas à soumettre une **pull request** ou à ouvrir une **issue** sur le dépôt GitHub.

---

## **Licence**

Ce projet est sous licence MIT. Vous êtes libre de l'utiliser, le modifier et le distribuer tant que vous respectez les termes de la licence.