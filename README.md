# **Optimisation des Bornes de Recharge Électrique - Projet MCLP**

## **Contexte du problème**

Avec la transition vers des modes de transport plus durables, la demande pour des infrastructures de recharge électrique ne cesse de croître. Cependant, l'implantation de bornes de recharge doit être pensée de manière stratégique pour maximiser leur efficacité tout en maîtrisant les coûts d'installation et d'adaptation du réseau. 

Ce projet s'intéresse spécifiquement à la ville de Rennes et propose une solution basée sur l'algorithme **MCLP (Maximal Covering Location Problem)**. L'objectif est de répondre au mieux aux besoins en recharge des habitants en optimisant le positionnement des bornes dans les parkings tout en respectant des contraintes budgétaires et géographiques.

---

## **Hypothèses réalisées**

Pour modéliser le problème, nous avons établi quelques hypothèses :

- **Demande en véhicules électriques (VE)** : Chaque bâtiment possède une demande calculée en fonction du nombre potentiel d'habitants adultes. La demande en VE est donc directement liée à la densité des habitants de plus de 18 ans.
- **Capacité des parkings** : Les parkings sont limités en nombre de bornes installables, en fonction de leur taille. Nous considérons que nous pouvons installer des bornes électriques sur au plus 10% des places.
- **Rayon de couverture** : Une borne peut desservir tous les bâtiments situés dans un rayon maximal défini (\( R_{\text{max}} \)).
- **Modèle de coût** : Le coût des bornes suit une dégressivité pour refléter les économies réalisées lorsqu'on installe plusieurs bornes dans un même parking. Par exemple, 5 bornes dans un parking coûtent moins que 5 bornes réparties dans 5 parkings différents.

---

## **Bases de données utilisées**

Pour ce projet, nous avons utilisé les données en libre accès de la métropole de Rennes. Tous ces fichiers JSON, sauf celui des batiments, sont déjà dans ce projet.

1. **Données des bâtiments** :
   - Contient les informations géographiques et démographiques des bâtiments de la zone étudiée.
   - Les principaux champs incluent les coordonnées géographiques (`geo_point_2d`), l'identifiant unique (`gml_id`) et la demande en VE (`nb_ve_potentiel`).
   - https://data.rennesmetropole.fr/explore/dataset/referentiel-batiment-et-ses-donnees-descriptives-sur-rennes-metropole/information/

2. **Données des parkings** :
   - Recense les parkings disponibles avec leurs caractéristiques.
   - Les champs importants sont : le nombre maximal de bornes installables (`max_bornes`), les coordonnées géographiques (`geo_point_2d`) et l'identifiant unique (`gml_id`).
   - https://data.rennesmetropole.fr/explore/dataset/parkings/information/

3. **Données des transformateurs** :
    - Recense les transformateurs disponibles avec leurs caractéristiques.
    - https://data.enedis.fr/pages/cartographie-des-reseaux-contenu/

4. **Données IRIS** :
   - Fournit les contours géographiques des zones IRIS de Rennes, permettant de visualiser la zone d'étude sur une carte.
   - https://data.rennesmetropole.fr/explore/dataset/iris_version_rennes_metropole/information/

---

## **Fonctionnement de l'algorithme MCLP**

L'algorithme MCLP est au cœur de ce projet. Il vise à maximiser la couverture des besoins en recharge tout en minimisant les coûts. Voici comment il fonctionne :

1. **Maximiser la couverture** : L'algorithme cherche à couvrir la demande en VE en positionnant stratégiquement les bornes dans les parkings.

2. **Contraintes mathématiques**

A. *Limitation du nombre total de bornes installées*

Cette contrainte limite le nombre total de bornes à \( p \), défini par l'utilisateur.

\[
\sum_{i \in S} x_i \leq p
\]

où :

- \( S \) : Ensemble des parkings potentiels.
- \( x_i \) : Nombre de bornes installées dans le parking \( i \).

---

B. *Respect des capacités maximales des parkings*

Chaque parking \( i \) a une capacité maximale \( C_i \) en nombre de bornes installables. On impose que le nombre de bornes \( x_i \) dans chaque parking \( i \) ne dépasse pas cette capacité.

\[
x_i \leq C_i \quad \forall i \in S
\]

où :

- \( C_i \) : Capacité maximale du parking \( i \) en nombre de bornes.

---

C. *Prise en compte d’un rayon maximal de couverture pour chaque borne*

Une borne installée dans le parking \( i \) peut couvrir une demande \( j \) seulement si la distance entre \( i \) et \( j \), notée \( d_{ij} \), est inférieure ou égale à \( R_{\text{max}} \).

Pour la couverture d'un bâtiment \( j \) :

\[
z_{ij} \leq y_j \quad \forall j \in D, \forall i \in S \text{ avec } d_{ij} \leq R_{\text{max}}
\]

où :

- \( D \) : Ensemble des bâtiments.
- \( y_j \) : Demande couverte pour le bâtiment \( j \).
- \( z_{ij} \) : Partie de la demande \( j \) couverte par le parking \( i \).

D. *Capacité liée aux parkings*

Pour garantir que la demande totale couverte par un parking ne dépasse pas les bornes disponibles, on impose :

\[
\sum_{j \in D : d_{ij} \leq R_{\text{max}}} z_{ij} \leq x_i \cdot C_i \quad \forall i \in S
\]

---

L'algorithme retourne les parkings sélectionnés, le nombre de bornes à installer dans chacun, et la couverture maximale obtenue.

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

