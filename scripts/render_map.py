"""Render the repository's offline SVG map using Python's standard library."""
import json, math, html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(name): return json.loads((ROOT/'data'/name).read_text())
def esc(s):return html.escape(str(s),quote=True)
def xy(lon,lat):return 40+(lon+12)*28,100+(math.asinh(math.tan(math.radians(61)))-math.asinh(math.tan(math.radians(lat))))*28*180/math.pi
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1560" height="1300" viewBox="0 0 1560 1300" role="img" aria-labelledby="title desc"><title id="title">Swietlik — European Starlink reference sites</title><desc id="desc">Country outlines, major cities, community-reported gateways. Not a complete or live inventory.</desc><style>text{font-family:Arial,sans-serif}.city{font-size:12px;fill:#475569;paint-order:stroke;stroke:white;stroke-width:3px;stroke-linejoin:round}.site{font-size:12px;fill:#92400e;paint-order:stroke;stroke:white;stroke-width:3px}.pop{font-size:14px;font-weight:bold;fill:#1d4ed8;paint-order:stroke;stroke:white;stroke-width:3px}</style><rect width="1560" height="1300" fill="white"/><text x="40" y="40" font-size="26" font-weight="bold" fill="#0f172a">SWIETLIK / Earth-to-Orbit Laser Communications</text><text x="40" y="68" font-size="15" fill="#475569">Europe · Lisbon to Ukraine · approximate reference locations · 2026-11-08</text><defs><clipPath id="bounds"><rect x="40" y="100" width="1484" height="1030"/></clipPath></defs><g clip-path="url(#bounds)">']
for f in read('source-countries.json')['features']:
 g=f['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
 for poly in polys:
  if not any(-13<=x<=42 and 30<=y<=65 for x,y,*_ in poly[0]):continue
  d=' '.join('M'+' L'.join(f'{xy(x,y)[0]:.1f},{xy(x,y)[1]:.1f}' for x,y,*_ in ring)+' Z' for ring in poly)
  parts.append(f'<path d="{d}" fill="none" stroke="#94a3b8" stroke-width="0.8"/>')
gates=read('gateways.geojson')['features']
occupied=[]
for f in sorted(read('source-cities.json')['features'],key=lambda f:f['properties']['pop_max'],reverse=True):
 p=f['properties'];lon,lat=f['geometry']['coordinates'][:2]
 if not(-10<lon<40.5 and 36<lat<60.5) or not(p['pop_max']>=700000 or p['adm0cap']==1):continue
 x,y=xy(lon,lat)
 if any(abs(x-a)<85 and abs(y-b)<18 for a,b in occupied):continue
 occupied.append((x,y));parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="#475569"/><text class="city" x="{x+6:.1f}" y="{y-5:.1f}">{esc(p["name"])}</text>')
for i,f in enumerate(gates,1):
 x,y=xy(*f['geometry']['coordinates']);p=f['properties'];fill='white' if p['source_status']=='planned' else '#f59e0b'
 parts.append(f'<g><title>G{i:02}: {esc(p["name"])} — {esc(p["note"])}</title><path d="M{x:.1f},{y-6:.1f} l-5,9 h10 Z" fill="{fill}" stroke="#b45309" stroke-width="1.2"/></g>')
 # Number labels are deliberately compact in dense UK clusters.
 if p['name'].startswith('Wola'):
  parts.append(f'<path d="M{x},{y} l25,26 h140" fill="none" stroke="#b45309"/><text class="site" x="{x+28}" y="{y+23}">Wola Krobowska ~</text>')
parts+=['</g><rect x="40" y="1150" width="1484" height="120" rx="8" fill="#f1f5f9"/>','<path d="M65,1194 l-5,9 h10 Z" fill="#f59e0b" stroke="#b45309"/><text x="82" y="1204" font-size="14">Gateway: community report, unverified; hollow triangle = reported planned</text>','<text x="55" y="1230" font-size="13" fill="#475569">Natural Earth: country outlines and cities (public domain). Boundary depiction follows the Natural Earth source dataset.</text>','<text x="55" y="1252" font-size="13" fill="#475569">Incomplete reference inventory. No live operational status. ~ = approximate. Wola Krobowska uses the village centre.</text></svg>']
(ROOT/'maps'/'europe.svg').write_text('\n'.join(parts))
print(f'Rendered {len(gates)} reported gateways, {len(occupied)} cities.')
