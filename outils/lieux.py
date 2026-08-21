#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complète source/lieux.json : les coordonnées GPS de chaque lieu.

    python outils/lieux.py

Sans coordonnées, le bouton « S'y rendre » bascule sur une recherche Google Maps
par nom, qui demande du réseau. Avec, il fonctionne en mode avion.

Deux sources, dans cet ordre :
  1. Wikidata, via l'API Wikipedia — coordonnées officielles des monuments,
     groupées par 50. C'est de loin la plus fiable en Inde.
  2. Nominatim / OpenStreetMap, en texte libre. Sans virgule : une virgule fait
     basculer l'API en analyse d'adresse structurée et la recherche échoue.

Les hôtels et les arrêts de bus privés ne figurent dans aucune base publique :
les saisir à la main dans MANUEL ci-dessous. Sur Google Maps, clic droit sur le
point, la première ligne du menu donne les coordonnées, un clic les copie.

Aucune dépendance : Python 3.8+.
"""

import json, os, sys, time, urllib.error, urllib.parse, urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "source", "lieux.json")
WIKI      = "https://en.wikipedia.org/w/api.php"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
UA = "Carnet2026/1.0 (https://github.com/Benoit62/carnet-2026)"

MANUEL = {
 # "hotel-rishikesh": [30.1234, 78.2345],
 # "hotel-agra":      [27.1600, 78.0420],
}

# clé : (article Wikipedia | None, requête Nominatim sans virgule)
LIEUX = {
 "aeroport-cdg":("Charles de Gaulle Airport","Charles de Gaulle Airport"),
 "aeroport-delhi-t3":("Indira Gandhi International Airport","Indira Gandhi International Airport Delhi"),
 "aeroport-hyderabad":("Rajiv Gandhi International Airport","Rajiv Gandhi International Airport Hyderabad"),
 "aeroport-jaipur":("Jaipur International Airport","Jaipur International Airport"),
 "gare-jaipur":("Jaipur Junction railway station","Jaipur Junction railway station"),
 "gare-udaipur":("Udaipur City railway station","Udaipur City railway station"),
 "gare-nizamuddin":("Hazrat Nizamuddin railway station","Hazrat Nizamuddin railway station"),
 "gare-agra-cantt":("Agra Cantonment railway station","Agra Cantt railway station"),
 "gare-new-delhi":("New Delhi railway station","New Delhi railway station"),
 "isbt-kashmere-gate":("Kashmere Gate ISBT","Kashmere Gate ISBT Delhi"),
 "tapovan":(None,"Tapovan Rishikesh"),
 "taj-ganj":(None,"Taj Ganj Agra"),
}


def http(url, essais=4):
    attente = 5
    for n in range(essais):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA, "Accept": "application/json",
                "Accept-Language": "en", "Accept-Encoding": "identity"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and n < essais - 1:
                p = int(e.headers.get("Retry-After") or attente)
                print(f"      … pause de {p} s"); time.sleep(p)
                attente = min(attente * 2, 120); continue
            raise
        except Exception:
            if n < essais - 1:
                time.sleep(attente); attente = min(attente * 2, 120); continue
            raise


def main():
    res = json.load(open(SORTIE, encoding="utf-8")) \
        if os.path.exists(SORTIE) else {}

    for cle, v in MANUEL.items():
        if v:
            res[cle] = {"lat": round(float(v[0]), 6), "lng": round(float(v[1]), 6)}
            print(f"  = {cle:24} saisi à la main")

    todo = {k: v for k, v in LIEUX.items() if k not in res}
    if not todo:
        print(f"Tout est géocodé ({len(res)} lieux).")
    else:
        # --- Wikidata, groupé ---
        titres = sorted({t for t, _ in todo.values() if t})
        wiki = {}
        for i in range(0, len(titres), 50):
            d = http(WIKI + "?" + urllib.parse.urlencode({
                "action": "query", "format": "json", "formatversion": "2",
                "prop": "coordinates", "redirects": "1",
                "titles": "|".join(titres[i:i+50])}))
            alias = {}
            for c in ("redirects", "normalized"):
                for r in d.get("query", {}).get(c, []):
                    alias[r["to"]] = alias.get(r["from"], r["from"])
            for p in d.get("query", {}).get("pages", []):
                co = (p.get("coordinates") or [None])[0]
                if not co:
                    continue
                t = p.get("title", "")
                for nom in {t, alias.get(t, t)}:
                    wiki[nom] = (round(co["lat"], 6), round(co["lon"], 6))
            time.sleep(2)

        echec = []
        for cle, (titre, requete) in todo.items():
            if titre and titre in wiki:
                lat, lng = wiki[titre]
                res[cle] = {"lat": lat, "lng": lng}
                print(f"  + {cle:24} {lat:9.5f} {lng:9.5f}  wikidata")
                continue
            try:
                d = http(NOMINATIM + "?" + urllib.parse.urlencode(
                    {"q": requete, "format": "jsonv2", "limit": "1"}))
                time.sleep(1.2)
                if not d:
                    raise RuntimeError("introuvable")
                res[cle] = {"lat": round(float(d[0]["lat"]), 6),
                            "lng": round(float(d[0]["lon"]), 6)}
                print(f"  + {cle:24} {res[cle]['lat']:9.5f} "
                      f"{res[cle]['lng']:9.5f}  osm")
            except Exception as e:
                echec.append((cle, requete, str(e)))
                print(f"  ! {cle:24} {e}")

        if echec:
            print("\nÉchecs — ajuster la requête dans LIEUX, ou saisir dans MANUEL :")
            for c, r, e in echec:
                print(f"  {c:24} <- \"{r}\"")

    json.dump(dict(sorted(res.items())), open(SORTIE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nsource/lieux.json : {len(res)} lieux")


if __name__ == "__main__":
    main()
