#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Construit le carnet à partir des fichiers de source/.

    python outils/build.py

Lit    source/villes.json, activites.json, etapes.json, lieux.json,
       reglages.json, prive.json
Écrit  donnees/voyage.json    contenu public, servi par GitHub Pages
       donnees/prive.json     PNR et places, jamais poussé
       hors-ligne.html        fichier unique autonome, photos intégrées

Ne jamais éditer donnees/ ni hors-ligne.html : ils sont écrasés à chaque build.
Pillow est nécessaire pour hors-ligne.html uniquement : pip install pillow
"""

import base64, glob, io, json, os, sys

RACINE  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE  = os.path.join(RACINE, "source")
DONNEES = os.path.join(RACINE, "donnees")
PHOTOS  = os.path.join(RACINE, "photos")

# motifs interdits dans le fichier public : le build s'arrête s'il en trouve un
INTERDITS = ("pnr", "sieges", "docs", ".pdf")


def lire(nom, defaut=None):
    p = os.path.join(SOURCE, nom)
    if not os.path.exists(p):
        if defaut is None:
            sys.exit(f"Fichier manquant : source/{nom}")
        print(f"  source/{nom} absent, ignoré")
        return defaut
    try:
        return json.load(open(p, encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"source/{nom} illisible ligne {e.lineno} : {e.msg}")


def main():
    villes    = lire("villes.json")
    activites = lire("activites.json")
    etapes    = lire("etapes.json")
    lieux     = lire("lieux.json")
    reglages  = lire("reglages.json")
    prive     = lire("prive.json", {})

    photos = {os.path.basename(p)[:-4] for p in glob.glob(PHOTOS + "/*.jpg")}
    # une photo peut porter un nom différent du slug qu'elle illustre
    ALIAS = {"har-ki-pauri": "haridwar", "ram-jhula": "lakshman-jhula",
             "mathura": "wildlife-sos", "taj-falaknuma": "chowmahalla"}

    def img(slug):
        for s in (slug, ALIAS.get(slug)):
            if s and s in photos:
                return f"photos/{s}.jpg"
        return None

    def pos(cle):
        return lieux.get(cle)

    nomville = {v["slug"]: v["nom"] for v in villes}
    alertes = []

    # ---------- villes ----------
    for v in villes:
        v["photo"] = img("ville-" + v["slug"])
        v["position"] = pos(v["slug"]) or pos("gare-" + v["slug"])

    # ---------- activités ----------
    for a in activites:
        if a["ville"] not in nomville:
            alertes.append(f"{a['slug']} : ville inconnue « {a['ville']} »")
        a["photo"] = img(a["slug"])
        a["position"] = pos(a["slug"])
        # sans coordonnées, le bouton bascule sur une recherche par nom
        a["recherche"] = None if a["position"] else \
            f"{a['nom']} {nomville.get(a['ville'], '')}".strip()

    # ---------- étapes ----------
    for e in etapes:
        for champ, cle in (("lieu", "position"),
                           ("lieu_depart", "position_depart"),
                           ("lieu_arrivee", "position_arrivee")):
            if champ in e:
                e[cle] = pos(e[champ])
                if not e[cle]:
                    alertes.append(f"{e['id']} : lieu « {e[champ]} » sans coordonnées")
        e["a_des_details"] = e["id"] in prive
    etapes.sort(key=lambda e: e["depart"])

    # ---------- assemblage ----------
    public = dict(version=3, **{k: reglages[k] for k in
                  ("titre", "debut", "fin", "fuseau", "a_reserver", "urgence")},
                  villes=villes, activites=activites, etapes=etapes)

    os.makedirs(DONNEES, exist_ok=True)
    for nom, obj in (("voyage.json", public),
                     ("prive.json", dict(version=3, details=prive))):
        p = os.path.join(DONNEES, nom)
        json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  donnees/{nom:14} {os.path.getsize(p)/1024:6.1f} Ko")

    # ---------- contrôle d'étanchéité ----------
    brut = json.dumps(public, ensure_ascii=False)
    fuites = [m for m in INTERDITS if m in brut]
    for d in prive.values():
        for v in (d.get("pnr"), d.get("sieges")):
            if v and v in brut:
                fuites.append(v)
    if fuites:
        sys.exit(f"ARRÊT — donnée sensible dans le fichier public : {fuites}")

    print(f"\n  {len(villes)} villes · {len(activites)} lieux · {len(etapes)} étapes")
    print(f"  photos    {sum(1 for a in activites if a['photo'])}/{len(activites)}")
    print(f"  positions {sum(1 for a in activites if a['position'])}/{len(activites)}")
    print("  étanchéité : aucune donnée sensible dans donnees/voyage.json")
    if alertes:
        print(f"\n  {len(alertes)} avertissements :")
        for a in alertes[:12]:
            print(f"    · {a}")
        if len(alertes) > 12:
            print(f"    · … et {len(alertes)-12} autres")

    # ---------- version hors ligne ----------
    try:
        from PIL import Image
    except ImportError:
        print("\n  Pillow absent : hors-ligne.html non généré (pip install pillow)")
        return

    html = open(os.path.join(RACINE, "index.html"), encoding="utf-8").read()
    images = {}
    for f in sorted(glob.glob(PHOTOS + "/*.jpg")):
        im = Image.open(f).convert("RGB").resize((700, 467), Image.LANCZOS)
        b = io.BytesIO()
        im.save(b, "JPEG", quality=72, optimize=True, progressive=True)
        images["photos/" + os.path.basename(f)] = \
            "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()

    html = html.replace(
"""    D=await (await fetch("donnees/voyage.json")).json();
    try{prive=await (await fetch("donnees/prive.json")).json()}catch(_){prive=null}""",
"""    D=EMBARQUE.voyage; prive=EMBARQUE.prive;
    const IMG=EMBARQUE.images;
    const remplace=o=>{if(o&&o.photo&&IMG[o.photo])o.photo=IMG[o.photo]};
    D.villes.forEach(remplace); D.activites.forEach(remplace);""")
    html = html.replace('<link rel="manifest" href="manifest.json">', "")
    html = html.replace('if("serviceWorker" in navigator)\n'
        '  navigator.serviceWorker.register("sw.js").catch(()=>{});', "")
    html = html.replace("<title>Inde 2026</title>",
        '<title>Inde 2026 — hors ligne</title>\n<link rel="icon" href="data:,">')
    html = html.replace("<script>",
        "<script>const EMBARQUE={voyage:" + json.dumps(public, ensure_ascii=False)
        + ",prive:" + json.dumps(dict(version=3, details=prive), ensure_ascii=False)
        + ",images:" + json.dumps(images) + "};</script>\n<script>", 1)

    out = os.path.join(RACINE, "hors-ligne.html")
    open(out, "w", encoding="utf-8").write(html)
    print(f"\n  hors-ligne.html  {os.path.getsize(out)/1e6:5.1f} Mo "
          f"· {len(images)} photos intégrées")


if __name__ == "__main__":
    main()
