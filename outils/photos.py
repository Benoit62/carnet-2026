#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Télécharge les illustrations depuis Wikipedia / Wikimedia Commons.

    python outils/photos.py            télécharge ce qui manque
    python outils/photos.py --reprendre  refait les images listées dans REPRENDRE

Écrit dans photos/ et note auteurs et licences dans photos/credits.json.
Aucune dépendance : Python 3.8+.

Les requêtes de recherche sont groupées (2 appels au lieu d'un par lieu) et
espacées : c'est ce qui évite le blocage anti-robot de Wikimedia.
"""

import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

RACINE  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTOS  = os.path.join(RACINE, "photos")
WIKI    = "https://en.wikipedia.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
UA      = "Carnet2026/1.0 (https://github.com/Benoit62/carnet-2026) Python-urllib"
LARGEUR = 1200
PAUSE   = 1.5

# slug d'image -> source.
#   "commons:…"  recherche d'image sur Wikimedia Commons
#   sinon        titre d'article Wikipedia, dont on prend l'image principale
SOURCES = {
 "ville-delhi":"New Delhi", "ville-hyderabad":"Charminar",
 "ville-jaipur":"Hawa Mahal", "ville-udaipur":"Udaipur",
 "ville-rishikesh":"Rishikesh", "ville-agra":"Agra",

 "golconde":"commons:Golconda Fort Hyderabad view", "charminar":"Charminar",
 "laad-bazaar":"Laad Bazaar", "mecca-masjid":"Makkah Masjid, Hyderabad",
 "qutb-shahi":"Qutb Shahi tombs", "chowmahalla":"Chowmahalla Palace",
 "salar-jung":"Salar Jung Museum", "tombes-paigah":"Paigah Tombs",
 "nizam-museum":"Nizam Museum", "birla-mandir":"Birla Mandir, Hyderabad",
 "hussain-sagar":"Hussain Sagar", "ramoji":"Ramoji Film City",

 "amber-fort":"Amer Fort", "jaigarh":"Jaigarh Fort",
 "panna-meena":"Panna Meena ka Kund", "nahargarh":"Nahargarh Fort",
 "city-palace-jaipur":"City Palace, Jaipur",
 "jantar-mantar":"commons:Jantar Mantar Jaipur Samrat Yantra",
 "hawa-mahal":"Hawa Mahal", "albert-hall":"Albert Hall Museum",
 "gaitor":"Gaitor ki Chhatriyan", "patrika-gate":"commons:Patrika Gate Jaipur",
 "galtaji":"Galtaji", "jal-mahal":"Jal Mahal",
 "anokhi-museum":"Anokhi Museum of Hand Printing", "rajmandir":"Raj Mandir Cinema",
 "jhalana":"commons:Indian leopard Jhalana Jaipur", "chand-baori":"Chand Baori",
 "bhangarh":"Bhangarh Fort",

 "city-palace-udaipur":"City Palace, Udaipur", "lac-pichola":"Lake Pichola",
 "jagdish-temple":"Jagdish Temple",
 "bagore-ki-haveli":"commons:Bagore ki Haveli Udaipur",
 "monsoon-palace":"commons:Sajjangarh Palace Udaipur",
 "saheliyon-ki-bari":"Saheliyon-ki-Bari", "ahar-cenotaphs":"Ahar, Rajasthan",
 "fateh-sagar":"Fateh Sagar Lake", "doodh-talai":"commons:Doodh Talai Udaipur",
 "vintage-car-museum":"commons:Vintage Car Museum Udaipur",
 "ranakpur":"Ranakpur Jain temple", "kumbhalgarh":"Kumbhalgarh",
 "chittorgarh":"Chittorgarh Fort",
 "eklingji":"commons:Eklingji temple Kailashpuri Rajasthan",

 "humayun":"Humayun's Tomb", "qutb-minar":"Qutb Minar",
 "mehrauli-park":"Mehrauli Archaeological Park", "lodhi-garden":"Lodhi Gardens",
 "lodhi-art":"commons:Lodhi Art District Delhi mural",
 "safdarjung":"Safdarjung's Tomb", "hauz-khas":"Hauz Khas Complex",
 "dilli-haat":"Dilli Haat", "musee-national":"National Museum, New Delhi",
 "india-gate":"India Gate", "jama-masjid":"Jama Masjid, Delhi",
 "chandni-chowk":"Chandni Chowk", "khari-baoli":"Khari Baoli",
 "red-fort":"Red Fort", "bangla-sahib":"Gurudwara Bangla Sahib",
 "agrasen-ki-baoli":"Agrasen ki Baoli", "nizamuddin-dargah":"Nizamuddin Dargah",
 "akshardham":"Akshardham (Delhi)", "lotus-temple":"Lotus Temple",
 "rail-museum":"National Rail Museum, New Delhi",

 "parmarth-niketan":"Parmarth Niketan",
 "ganga-aarti":"commons:Ganga aarti Rishikesh evening ceremony",
 "triveni-ghat":"commons:Triveni Ghat Rishikesh Ganges",
 "beatles-ashram":"Chaurasi Kutia", "lakshman-jhula":"Lakshman Jhula",
 "tera-manzil":"commons:Tera Manzil Temple Rishikesh",
 "neer-garh":"commons:Neer Garh Waterfall Rishikesh",
 "kunjapuri":"Kunjapuri Temple",
 "neelkanth":"commons:Neelkanth Mahadev Temple Rishikesh",
 "vashishta-gufa":"Vashistha Gufa", "haridwar":"Har Ki Pauri",

 "taj-mahal":"Taj Mahal", "fort-agra":"Agra Fort", "mehtab-bagh":"Mehtab Bagh",
 "itmad-ud-daulah":"Tomb of I'timad-ud-Daulah", "akbar-sikandra":"Akbar's tomb",
 "chini-ka-rauza":"Chini Ka Rauza", "kinari-bazaar":"commons:Kinari Bazar Agra",
 "fatehpur-sikri":"Fatehpur Sikri", "keoladeo":"Keoladeo National Park",
 "wildlife-sos":"commons:Elephant Conservation Care Centre Mathura",
 "sur-sarovar":"Sur Sarovar", "chambal":"National Chambal Sanctuary",
}

# à refaire malgré un fichier déjà présent : mauvais sujet, mauvais cadrage,
# résolution insuffisante. Vidé une fois la reprise validée.
REPRENDRE = [
 "ville-delhi", "ville-udaipur", "ville-agra",   # doublons d'une photo de lieu
 "bagore-ki-haveli",   # le panneau du musée
 "eklingji",           # photo d'archive en noir et blanc
 "ganga-aarti",        # un jardin, et 300x225
 "lodhi-art",          # un tombeau des jardins de Lodhi, pas le street art
 "monsoon-palace",     # le palais minuscule au fond d'une photo verticale
 "neelkanth",          # mauvais temple, 384x429
 "wildlife-sos",       # un singe sous une couverture
 "triveni-ghat",       # un char décoratif
 "golconde",           # un pan de mur
 "jantar-mantar",      # vue aérienne lointaine
]


def http(url, binaire=False, essais=5):
    attente = 5
    for n in range(essais):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA, "Accept": "*/*" if binaire else "application/json",
                "Accept-Encoding": "identity"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read() if binaire else json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and n < essais - 1:
                p = int(e.headers.get("Retry-After") or attente)
                print(f"      … limite atteinte, pause de {p} s")
                time.sleep(p); attente = min(attente * 2, 120); continue
            raise
        except Exception:
            if n < essais - 1:
                time.sleep(attente); attente = min(attente * 2, 120); continue
            raise


def lots(seq, n):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def via_wikipedia(titres):
    """Une requête pour 50 articles -> {titre: (url, fichier)}"""
    out = {}
    for lot in lots({t for t in titres if not t.startswith("commons:")}, 50):
        d = http(WIKI + "?" + urllib.parse.urlencode({
            "action": "query", "format": "json", "formatversion": "2",
            "prop": "pageimages", "piprop": "thumbnail|name",
            "pithumbsize": str(LARGEUR), "redirects": "1",
            "titles": "|".join(lot)}))
        alias = {}
        for cle in ("redirects", "normalized"):
            for r in d.get("query", {}).get(cle, []):
                alias[r["to"]] = alias.get(r["from"], r["from"])
        for p in d.get("query", {}).get("pages", []):
            th = (p.get("thumbnail") or {}).get("source")
            if not th:
                continue
            t = p.get("title", "")
            for nom in {t, alias.get(t, t)}:
                out[nom] = (th, p.get("pageimage", ""))
        time.sleep(3)
    return out


def via_commons(terme):
    """Recherche d'image ; on écarte le portrait et la basse résolution."""
    d = http(COMMONS + "?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": "2",
        "generator": "search", "gsrsearch": f"filetype:bitmap {terme}",
        "gsrnamespace": "6", "gsrlimit": "8", "prop": "imageinfo",
        "iiprop": "url|size", "iiurlwidth": str(LARGEUR)}))
    best = None
    for p in d.get("query", {}).get("pages", []):
        ii = (p.get("imageinfo") or [{}])[0]
        w, h = ii.get("width", 0), ii.get("height", 1)
        if not ii.get("thumburl") or w < 900 or w / max(h, 1) < 0.95:
            continue
        score = 3 if 1.2 <= w / h <= 2.0 else 1
        if best is None or score > best[0]:
            best = (score, ii["thumburl"], p.get("title", "").replace("File:", ""))
    time.sleep(3)
    return best[1:] if best else None


def main():
    os.makedirs(PHOTOS, exist_ok=True)
    reprendre = "--reprendre" in sys.argv
    cible = REPRENDRE if reprendre else list(SOURCES)
    if reprendre and not cible:
        return print("REPRENDRE est vide : rien à refaire.")

    todo = {}
    for slug in cible:
        f = os.path.join(PHOTOS, slug + ".jpg")
        if reprendre or not (os.path.exists(f) and os.path.getsize(f) > 5000):
            todo[slug] = SOURCES[slug]
    if not todo:
        return print(f"Les {len(SOURCES)} photos sont déjà là.")

    chemin = os.path.join(PHOTOS, "credits.json")
    credits = json.load(open(chemin, encoding="utf-8")) \
        if os.path.exists(chemin) else {}

    print(f"{len(todo)} à télécharger.\nRecherche groupée…")
    trouves = via_wikipedia(todo.values())

    ok, echec = 0, []
    for i, (slug, src) in enumerate(todo.items(), 1):
        try:
            if src.startswith("commons:"):
                r = via_commons(src[8:])
                if not r:
                    raise RuntimeError("aucun résultat")
                url, nom = r
            else:
                if src not in trouves:
                    r = via_commons(src)
                    if not r:
                        raise RuntimeError("aucun résultat")
                    url, nom = r
                else:
                    url, nom = trouves[src]
            data = http(url, binaire=True)
            if len(data) < 20000:
                raise RuntimeError(f"image trop petite ({len(data)} o)")
            open(os.path.join(PHOTOS, slug + ".jpg"), "wb").write(data)
            credits[slug] = {"source": nom, "recherche": src}
            ok += 1
            print(f"[{i:3}/{len(todo)}] + {slug:22} {len(data)//1024:4} Ko")
        except Exception as e:
            echec.append((slug, src, str(e)))
            print(f"[{i:3}/{len(todo)}] ! {slug:22} {e}")
        time.sleep(PAUSE)

    json.dump(credits, open(chemin, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n{ok} téléchargées, {len(echec)} en échec.")
    for s, t, e in echec:
        print(f"  {s:22} <- {t}")
    if echec:
        print("\nCorriger la source dans SOURCES puis relancer.")


if __name__ == "__main__":
    main()
