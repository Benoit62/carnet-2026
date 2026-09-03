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
      faits.json         slugs des lieux visités et des tables essayées
      prive.json         PNR et places — non versionné

    outils/          ← les scripts
      build.py           construit tout
      photos.py          télécharge les illustrations
      lieux.py           récupère les coordonnées GPS

    donnees/         ← généré, ne pas éditer
    photos/          les illustrations, 1000×667
    index.html       l'application, CSS et JS inclus
    sw.js            mise en cache hors ligne

## Construire

    python outils/build.py

Une seule commande, trois sorties cohérentes :

    donnees/voyage.json   le contenu public, servi par GitHub Pages
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

Les tables se distinguent des visites par leur `categorie`, qui vaut
`restaurant` : la coche devient une fourchette et l'encadré passe à l'orange.
Pour ajouter une table, un bloc dans `source/activites.json` suffit.

```json
{
 "slug": "ambrai",
 "ville": "udaipur",
 "nom": "Ambrai",
 "etoile": 0,
 "categorie": "restaurant",
 "description": "…",
 "pratique": null,
 "reservation": null
}
```

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

Les illustrations viennent de Wikipedia et Wikimedia Commons, sous licence
libre ; auteurs et licences sont notés dans `photos/credits.json`.

Les hôtels et les arrêts de bus privés ne figurent dans aucune base publique :
les saisir dans le dictionnaire `MANUEL` de `outils/lieux.py`.

## Fuseau

L'étape en cours est déduite de l'horloge, en UTC+5:30. Aucun état n'est
stocké : les deux téléphones affichent la même chose sans rien synchroniser.
