"""Download and render a reproducible three-hour Meteosat cloud-screening pilot.
Requires Pillow. Network needed only without --offline. Times are UTC internally.
"""
import argparse, csv, hashlib, io, json, math, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'maps'/'weather-2026-11-05'; RAW=OUT/'raw'; WIDTH,HEIGHT=1400,1020
BBOX=(-12,35,41,61); BASE='https://view.eumetsat.int/geoserver/wms'
TIMES=[datetime(2026,11,5,8,45,tzinfo=timezone.utc)+timedelta(minutes=15*i) for i in range(13)]
def iso(t):return t.isoformat().replace('+00:00','Z')
def pos(lon,lat):return (lon-BBOX[0])/(BBOX[2]-BBOX[0])*WIDTH,(BBOX[3]-lat)/(BBOX[3]-BBOX[1])*HEIGHT
def font(size,bold=False):
 p=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf')
 return ImageFont.truetype(str(p),size) if p.exists() else ImageFont.load_default(size=size)
def fetch(task):
 t,kind=task;layer='msg_fes:rgb_natural' if kind=='rgb' else 'msg_fes:clm'
 name=f'{t:%Y%m%dT%H%MZ}-{kind}.png';path=RAW/name
 q=dict(service='WMS',version='1.3.0',request='GetMap',layers=layer,styles='',crs='CRS:84',bbox=','.join(map(str,BBOX)),width=WIDTH,height=HEIGHT,format='image/png',time=iso(t),transparent='false',interpolations='nearest neighbor')
 url=BASE+'?'+urllib.parse.urlencode(q)
 if not path.exists():
  if ARGS.offline:raise RuntimeError(f'Missing cached frame: {name}')
  for attempt in range(3):
   try:
    with urllib.request.urlopen(url,timeout=55) as r:b=r.read()
    im=Image.open(io.BytesIO(b));im.load()
    if im.size!=(WIDTH,HEIGHT):raise ValueError('Unexpected image dimensions')
    path.write_bytes(b);break
   except Exception:
    if attempt==2:raise
    time.sleep(1)
 b=path.read_bytes();im=Image.open(io.BytesIO(b));im.load()
 if im.getbbox() is None:raise ValueError(f'Empty frame: {name}')
 return dict(requested_time_utc=iso(t),kind=kind,layer=layer,url=url,file='raw/'+name,sha256=hashlib.sha256(b).hexdigest())
def screen(mask,lon,lat):
 x,y=pos(lon,lat);x,y=int(x),int(y)
 # Exact WMS palette only. Other colours are unknown, never assumed clear.
 lookup={(0,192,0):'clear',(0,0,255):'clear',(255,255,255):'cloudy'}
 if not(0<=x<WIDTH and 0<=y<HEIGHT):return 'unknown',None,None
 centre=lookup.get(mask.getpixel((x,y)),'unknown')
 samples=[lookup.get(mask.getpixel((i,j)),'unknown') for i in range(max(0,x-2),min(WIDTH,x+3)) for j in range(max(0,y-2),min(HEIGHT,y+3))]
 valid=[s for s in samples if s!='unknown'];fraction=round(valid.count('cloudy')/len(valid),3) if valid else None
 # Conservative screen: require all 25 nearby map pixels clear. Mixed = uncertain.
 state='unknown' if len(valid)!=len(samples) else ('clear' if fraction==0 else 'cloudy' if fraction==1 else 'mixed')
 return state,centre,fraction
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--offline',action='store_true');ARGS=parser.parse_args()
 RAW.mkdir(parents=True,exist_ok=True)
 tasks=[(t,k) for t in TIMES for k in ['rgb','mask']]
 with ThreadPoolExecutor(max_workers=3) as pool:
  manifest=list(pool.map(fetch,tasks))
 print('Downloaded/validated',len(manifest),'images',flush=True)
 for kind in ['rgb','mask']:
  assert len({m['sha256'] for m in manifest if m['kind']==kind})==len(TIMES),'Repeated frames: check service time selection'
 (OUT/'manifest.json').write_text(json.dumps({'retrieved_date':'2026-11-08','bbox_crs84':BBOX,'size':[WIDTH,HEIGHT],'attribution':'Contains modified EUMETSAT data © EUMETSAT 2026','time_note':'Requested quarter-hour slots; WMS advertises nearestValue=1. Exact source acquisition times have not been independently verified.','frames':manifest},indent=2)+'\n')
 sites=[]
 for file,kind in [('pops.geojson','pop'),('gateways.geojson','gateway')]:
  for i,f in enumerate(json.loads((ROOT/'data'/file).read_text())['features'],1):
   sites.append(dict(id=('P' if kind=='pop' else 'G')+f'{i:02}',kind=kind,name=f['properties']['name'],coordinates=f['geometry']['coordinates'],source_status=f['properties'].get('source_status','listed')))
 countries=json.loads((ROOT/'data/source-countries.json').read_text())['features']
 cities=json.loads((ROOT/'data/source-cities.json').read_text())['features']
 rows=[];frames=[]
 colors={'clear':'#34d399','cloudy':'#fb7185','mixed':'#fbbf24','unknown':'#94a3b8'}
 for idx,t in enumerate(TIMES):
  rgb=Image.open(RAW/f'{t:%Y%m%dT%H%MZ}-rgb.png').convert('RGB');mask=Image.open(RAW/f'{t:%Y%m%dT%H%MZ}-mask.png').convert('RGB')
  frame=Image.new('RGB',(WIDTH,HEIGHT+190),'#0f172a');frame.paste(rgb,(0,85));d=ImageDraw.Draw(frame)
  d.text((24,12),'SWIETLIK / 3-hour cloud-screening pilot',font=font(23,True),fill='white')
  local=t+timedelta(hours=1)
  d.text((24,47),f'05 Nov 2026 | {local:%H:%M} CET / {t:%H:%M} UTC | {idx+1:02}/13 | Meteosat observations',font=font(17),fill='#cbd5e1')
  for f in countries:
   g=f['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
   for poly in polys:
    for ring in poly:
     pts=[(pos(x,y)[0],pos(x,y)[1]+85) for x,y,*_ in ring]
     # Clip by drawing into the map image, not the header/footer.
     md=ImageDraw.Draw(rgb);md.line([(a,b-85) for a,b in pts],fill='#64748b',width=1)
  frame.paste(rgb,(0,85));d=ImageDraw.Draw(frame)
  for f in cities:
   p=f['properties'];lon,lat=f['geometry']['coordinates'][:2]
   if not(-10<lon<40 and 36<lat<60) or not(p['adm0cap']==1 or p['pop_max']>1500000):continue
   x,y=pos(lon,lat);y+=85
   d.ellipse((x-2,y-2,x+2,y+2),fill='white');d.text((x+5,y+3),p['name'],font=font(11),fill='white',stroke_width=2,stroke_fill='#263445')
  totals=Counter()
  for s in sites:
   lon,lat=s['coordinates'];state,centre,fraction=screen(mask,lon,lat);totals[state]+=1
   rows.append(dict(time_utc=iso(t),time_cet=f'{local:%Y-%m-%dT%H:%M}:00+01:00',site_id=s['id'],name=s['name'],kind=s['kind'],longitude=lon,latitude=lat,source_status=s['source_status'],cloud_screen=state,centre_class=centre,neighbourhood_cloud_fraction=fraction))
   x,y=pos(lon,lat);y+=85;c=colors[state]
   if s['kind']=='pop':d.ellipse((x-7,y-7,x+7,y+7),fill=c,outline='#0f172a',width=2)
   else:d.polygon([(x,y-7),(x-7,y+6),(x+7,y+6)],fill=c,outline='#0f172a',width=2)
   if s['kind']=='pop' or s['name'].startswith('Wola'):
    label=s['name'].split(',')[0]+' ~';dy=-23 if s['kind']=='pop' else 10
    d.text((x+9,y+dy),label,font=font(13,True),fill=c,stroke_width=2,stroke_fill='#0f172a')
  y=HEIGHT+98
  for x,(state,label) in zip([24,270,520,790],[('clear','Clear neighbourhood'),('cloudy','Cloudy'),('mixed','Mixed / uncertain'),('unknown','No data')]):
   d.ellipse((x,y,x+12,y+12),fill=colors[state]);d.text((x+20,y-3),label,font=font(15),fill='white')
  d.text((24,y+25),'Circles: PoP cities ~ | Triangles: reported gateways ~ | Cloud screen only; no satellite line-of-sight test.',font=font(14),fill='#cbd5e1')
  d.text((24,y+47),'Contains modified EUMETSAT data © EUMETSAT 2026 | Borders/cities: Natural Earth | Sites: PeeringDB + community',font=font(12),fill='#94a3b8')
  d.text((24,y+66),'Approximate sites; 5×5 map-pixel neighbourhood. Planned sites included for weather comparison only.',font=font(12),fill='#94a3b8')
  frame.save(OUT/f'frame-{idx:02}.png');frames.append(frame)
 with (OUT/'site-cloud-screen.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 frames[0].save(OUT/'preview.png')
 frames[0].save(OUT/'animation.gif',save_all=True,append_images=frames[1:],duration=650,loop=0,optimize=False)
 with (OUT/'summary.csv').open('w') as f:
  fields=['site_id','name','kind','source_status','clear_frames','cloudy_frames','mixed_frames','unknown_frames'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for s in sites:
   counts=Counter(r['cloud_screen'] for r in rows if r['site_id']==s['id'])
   w.writerow({'site_id':s['id'],'name':s['name'],'kind':s['kind'],'source_status':s['source_status']}|{k+'_frames':counts[k] for k in colors})
 print(f'Built {len(frames)} distinct frames; {len(rows)} site-time records. Output: {OUT}',flush=True)
