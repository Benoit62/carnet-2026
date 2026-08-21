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

## Modifier le contenu

Ajouter un hébergement : recopier un bloc voisin dans `source/etapes.json`, lui
donner un `id` unique, et renseigner `lieu` avec une clé présente dans
`source/lieux.json`. Les dates sont au format ISO, **en heure indienne**
(UTC+5:30) — l'application n'applique aucune conversion.

Ajouter un lieu à visiter : un bloc dans `source/activites.json`. Le champ
`etoile` vaut 0, 1 ou 2 et pilote le classement dans la fiche ville. Une photo
nommée `photos/<slug>.jpg` est reprise automatiquement.

Puis relancer le build et pousser.

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
