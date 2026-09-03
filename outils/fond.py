#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabrique source/fond.json, le fond de carte vectoriel de l'itinéraire.

    python outils/fond.py

Les frontières viennent de Natural Earth (domaine public), échelle 1:50 M.
Le script les télécharge, ne garde que la fenêtre utile, simplifie les
contours puis les projette en Mercator, l'unité valant un radian × 1000.
Les chemins sont écrits en commandes relatives, bien plus courtes.

Il n'y a pas de raison de le relancer, sauf pour changer la fenêtre ou le
degré de simplification. Le résultat est versionné.
"""

import json, math, os, urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "source", "fond.json")
DEPOT  = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
CACHE  = os.path.join(RACINE, ".cache-naturalearth")


def telecharger(nom):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, nom)
    if not os.path.exists(p):
        print(f"  téléchargement de {nom}")
        urllib.request.urlretrieve(DEPOT + nom, p)
    return json.load(open(p, encoding="utf-8"))


K = 1000.0
def proj(lng, lat):
    lat = max(-85.0, min(85.0, lat))
    return (math.radians(lng) * K,
            -math.log(math.tan(math.pi/4 + math.radians(lat)/2)) * K)

def dp(pts, tol):
    """Douglas-Peucker sur des degrés."""
    if len(pts) < 3: return pts
    dmax, idx = 0.0, 0
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2-x1, y2-y1
    n2 = dx*dx + dy*dy
    for i in range(1, len(pts)-1):
        px, py = pts[i]
        if n2 == 0: d = math.hypot(px-x1, py-y1)
        else:
            t = max(0.0, min(1.0, ((px-x1)*dx + (py-y1)*dy)/n2))
            d = math.hypot(px-(x1+t*dx), py-(y1+t*dy))
        if d > dmax: dmax, idx = d, i
    if dmax > tol:
        return dp(pts[:idx+1], tol)[:-1] + dp(pts[idx:], tol)
    return [pts[0], pts[-1]]

def aire(ring):
    s = 0.0
    for i in range(len(ring)-1):
        s += ring[i][0]*ring[i+1][1] - ring[i+1][0]*ring[i][1]
    return abs(s)/2

def anneaux(geom):
    t, c = geom["type"], geom["coordinates"]
    return [r for poly in ([c] if t == "Polygon" else c) for r in poly]

def rogne(ring, boite):
    """Sutherland-Hodgman : coupe un anneau sur un rectangle en degrés."""
    lo_lng, lo_lat, hi_lng, hi_lat = boite
    def passe(pts, dedans, inter):
        out = []
        for i in range(len(pts)):
            a, b = pts[i-1], pts[i]
            da, db = dedans(a), dedans(b)
            if db:
                if not da: out.append(inter(a, b))
                out.append(b)
            elif da:
                out.append(inter(a, b))
        return out
    def couple(t, a, b): return (a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1]))
    r = ring[:-1] if ring[0] == ring[-1] else ring[:]
    for dedans, inter in (
        (lambda p: p[0] >= lo_lng, lambda a,b: couple((lo_lng-a[0])/(b[0]-a[0]), a, b)),
        (lambda p: p[0] <= hi_lng, lambda a,b: couple((hi_lng-a[0])/(b[0]-a[0]), a, b)),
        (lambda p: p[1] >= lo_lat, lambda a,b: couple((lo_lat-a[1])/(b[1]-a[1]), a, b)),
        (lambda p: p[1] <= hi_lat, lambda a,b: couple((hi_lat-a[1])/(b[1]-a[1]), a, b))):
        if not r: return []
        r = passe(r, dedans, inter)
    return r + [r[0]] if r else []


def chemin(geom, tol, aire_min, boite=None):
    out = []
    for r in anneaux(geom):
        r = [(round(x, 5), round(y, 5)) for x, y in r]
        if aire(r) < aire_min: continue
        if boite:
            r = rogne(r, boite)
            if len(r) < 4 or aire(r) < aire_min: continue
        s = dp(r, tol)
        if len(s) < 4: continue
        pts = [proj(lng, lat) for lng, lat in s]
        d = [f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"]
        px, py = pts[0]
        for x, y in pts[1:]:
            dx, dy = round(x - px, 1), round(y - py, 1)
            if dx == 0 and dy == 0: continue
            d.append(f"l{dx:g} {dy:g}")
            px, py = px + dx, py + dy
        out.append("".join(d) + "z")
    return "".join(out)

etats = telecharger("ne_50m_admin_1_states_provinces.geojson")["features"]
pays  = telecharger("ne_50m_admin_0_countries.geojson")["features"]

# fenêtre utile : sous-continent indien, Paris arrive par le tracé de l'itinéraire
BOITE = (63.5, 4.0, 101.0, 38.5)
VOISINS = {"Pakistan", "Nepal", "Bhutan", "Bangladesh", "Sri Lanka", "China",
           "Myanmar", "Afghanistan", "Oman", "Tajikistan", "Laos", "Thailand"}

res = {"etats": [], "pays": [], "inde": ""}
for f in etats:
    p = f["properties"]
    if p.get("admin") != "India": continue
    d = chemin(f["geometry"], 0.035, 0.02, BOITE)
    if d: res["etats"].append({"nom": p.get("name"), "d": d})

for f in pays:
    p = f["properties"]
    nom = p.get("NAME") or p.get("name")
    if nom == "India":
        res["inde"] = chemin(f["geometry"], 0.018, 0.02, BOITE)
    elif nom in VOISINS:
        d = chemin(f["geometry"], 0.09, 0.15, BOITE)
        if d: res["pays"].append({"nom": nom, "d": d})

json.dump(res, open(SORTIE, "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))

print(f"états    {len(res['etats']):3}  {sum(len(e['d']) for e in res['etats'])/1024:6.1f} Ko")
print(f"voisins  {len(res['pays']):3}  {sum(len(e['d']) for e in res['pays'])/1024:6.1f} Ko")
print(f"Inde          {len(res['inde'])/1024:6.1f} Ko")
print(f"total         {os.path.getsize(SORTIE)/1024:6.1f} Ko  → source/fond.json")
