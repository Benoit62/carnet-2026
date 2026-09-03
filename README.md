# Carnet 2026

Carnet de route hors ligne : un fil chronologique, des fiches villes et des
fiches lieux, consultables sans réseau depuis un téléphone.

## Installation sur le téléphone

Ouvrir l'adresse GitHub Pages, puis « Ajouter à l'écran d'accueil ». Le service
worker met tout en cache à la première visite, photos comprises. Ensuite
l'application fonctionne en mode avion.

## Organisation

    source/          ← ce qui s'édite à la main
      villes.json        les 6 villes : présentation, tables, conseils
      activites.json     les lieux : description, horaires, réservation
      etapes.json        le fil : vols, trains, bus, hébergements
      lieux.json         coordonnées GPS, par identifiant de lieu
      reglages.json      dates, contacts d'urgence, choses à réserver
      faits.json         lieux visités et tables essayées
      fond.json          fond de carte vectoriel, Natural Earth
      prive.json         PNR et places — non versionné

    outils/          ← les scripts
      build.py           construit tout
      photos.py          télécharge les illustrations
      lieux.py           récupère les coordonnées GPS
      fond.py            refabrique le fond de carte

    donnees/         ← généré, ne pas éditer
    photos/          les illustrations, 1000×667
    index.html       l'application, CSS et JS inclus
    sw.js            mise en cache hors ligne

## Construire

    python outils/build.py

Une seule commande, trois sorties cohérentes :

    donnees/voyage.json   le contenu public, servi par GitHub Pages
    donnees/fond.json     le fond de carte, recopié tel quel
    donnees/prive.json    PNR et places, jamais poussé
    hors-ligne.html       fichier unique autonome, photos intégrées

`donnees/` et `hors-ligne.html` sont **écrasés à chaque build** : les modifier à
la main ne sert à rien. Tout se passe dans `source/`.

Le build s'interrompt s'il trouve un PNR, un numéro de place ou un nom de billet
dans le fichier public. Il signale aussi les lieux sans coordonnées et les
activités rattachées à une ville inconnue.

## Modifier une étape du fil

Tout se passe dans `source/etapes.json`, un bloc par étape. Les dates sont au
format ISO et **en heure indienne** (UTC+5:30), l'application n'applique aucune
conversion. Trois champs facultatifs enrichissent l'affichage :

```json
{
 "id": "j1-vol-paris",
 "type": "vol",
 "titre": "Paris → Delhi",
 "depart": "2026-08-24T10:50",
 "arrivee": "2026-08-24T22:50",
 "lieu": "hotel-jaipur",
 "ville": "jaipur",
 "note": "Texte libre, affiché dans le bloc « à savoir ».",

 "infos": [
  {"libelle": "Terminal", "valeur": "2E"}
 ],
 "instructions": [
  "Enregistrement en ligne",
  "Photo des sacs avant dépôt"
 ],
 "deroule": [
  {"quand": "Mer 26 · 11h", "titre": "Haldi",
   "texte": "…", "tenue": "…"}
 ]
}
```

`infos` produit les étiquettes courtes sur la carte du fil, sous le titre.
`instructions` produit une liste à cocher dans la fiche détaillée, et une
pastille orange « N à faire » sur la carte ; les cases cochées sont mémorisées
dans le navigateur du téléphone. `deroule` produit un programme détaillé, comme
celui du mariage.

Le champ `lieu` doit correspondre à une clé de `source/lieux.json`, c'est lui
qui alimente le bouton « S'y rendre ».

Ajouter un lieu à visiter se fait de la même façon dans `source/activites.json`.
Le champ `etoile` vaut 0, 1 ou 2 et détermine l'ordre dans la fiche ville.

Après toute modification, relancer `python outils/build.py` puis pousser.

## Marquer ce qui a été fait

Ajouter le slug du lieu dans `source/faits.json` :

```json
{
 "faits": [
  "amber-fort",
  "nahargarh",
  "masala-chowk"
 ]
}
```

L'élément est alors coché en vert dans la fiche ville, remonté en tête de la
liste, et affiché en mosaïque sur la carte du séjour dans le fil. Le build
signale un slug qui ne correspondrait à aucun lieu.

Un `"fait": true` posé directement dans `source/activites.json` fonctionne
aussi, les deux mécanismes se cumulent.

## Noter une table

Une table essayée se déclare d'un seul bloc, dans la liste `tables` du même
`source/faits.json`. Rien d'autre à toucher : ni `activites.json`, ni
`lieux.json`. C'est le format à utiliser pendant le voyage.

```json
{
 "faits": ["amber-fort", "nahargarh"],
 "tables": [
  {"nom": "Ambrai", "ville": "udaipur",
   "lat": 24.5795, "lng": 73.6824,
   "note": "Une phrase sur l'endroit.",
   "pratique": "Réserver le soir pour la terrasse."}
 ]
}
```

Seuls `nom` et `ville` sont obligatoires. Le slug se déduit du nom, et sans
`lat`/`lng` la table apparaît quand même dans la fiche ville, simplement pas sur
la carte. La coche verte devient une fourchette orange, dans le fil comme sur la
carte.

Une table déjà écrite dans `activites.json` avec `"categorie": "restaurant"`
fonctionne toujours, il suffit alors d'ajouter son slug dans `faits`.

## La carte

Un panneau permanent à droite sur ordinateur et sur tablette en paysage, un
bouton flottant en bas à droite sur téléphone.

Rien à renseigner : la carte se construit toute seule à partir de
`source/etapes.json` et de `source/lieux.json`. Chaque trajet devient un arc
entre son `lieu_depart` et son `lieu_arrivee`, avec la pastille de son mode de
transport au milieu. Un trajet en cours se remplit au fil des heures, et un
point clignotant marque la position calculée sur l'arc. Les villes portent leur
numéro d'ordre et passent du contour au vert une fois traversées.

Les hébergements apparaissent en violet, les lieux marqués dans `faits.json` en
vert et les tables en orange. Ces trois-là ne se montrent qu'une fois zoomé,
sinon la vue d'ensemble devient illisible. Un appui sur une ville ouvre son
aperçu, d'où l'on descend sur ses lieux ; « Où on est » ramène à la position du
moment et « Tout voir » au trajet entier.

Le fond vient de Natural Earth, dans le domaine public. Il est vectoriel et
versionné dans le dépôt, donc la carte se dessine encore en mode avion, sans
aucun serveur de tuiles. `python outils/fond.py` le refabrique, à ne relancer
que pour changer la fenêtre ou le degré de simplification.

Ajouter une ville à la carte demande sa clé dans `source/lieux.json`, du même
nom que son `slug`. Sans coordonnées, elle est simplement ignorée.

## Ajouter des photos

Aucun fichier JSON à modifier. Il suffit de déposer les images dans `photos/` en
les nommant d'après la clé du sujet, et le carrousel apparaît tout seul :

```
photos/hotel-jaipur.jpg      la principale, affichée en vignette
photos/hotel-jaipur-2.jpg    les suivantes, dans l'ordre
photos/hotel-jaipur-3.jpg
```

La clé est celle du champ `lieu` pour une étape, du champ `slug` pour un lieu à
visiter, et `ville-<slug>` pour une ville. Les clés d'hébergement sont
`hotel-delhi-aerocity`, `hotel-hyderabad`, `hotel-jaipur`, `hotel-udaipur`,
`hotel-delhi-hosteller`, `hotel-rishikesh` et `hotel-agra`.

Si un fichier porte un autre nom, la table `ALIAS` en tête de `outils/build.py`
fait le lien. Le build signale tout hébergement resté sans photo.

Format attendu : JPEG, 1000×667 environ. Le compteur en bas de la vignette
indique le nombre d'images disponibles.

## Photos et coordonnées

    python outils/photos.py               télécharge ce qui manque
    python outils/photos.py --reprendre   refait les images listées dans REPRENDRE
    python outils/lieux.py                complète les coordonnées
    python outils/fond.py                 refabrique le fond de carte

Les illustrations viennent de Wikipedia et Wikimedia Commons, sous licence
libre ; auteurs et licences sont notés dans `photos/credits.json`.

Les hôtels et les arrêts de bus privés ne figurent dans aucune base publique :
les saisir dans le dictionnaire `MANUEL` de `outils/lieux.py`.

## Fuseau

L'étape en cours est déduite de l'horloge, en UTC+5:30. Aucun état n'est
stocké : les deux téléphones affichent la même chose sans rien synchroniser.
