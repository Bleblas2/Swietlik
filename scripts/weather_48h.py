"""Gateway-only 48-hour MSG infrared + categorical cloud-mask study.
Requires Pillow; use --download-only to cache/analyse, --offline to re-render.
"""
import argparse,csv,hashlib,io,json,math,subprocess,time,urllib.request,urllib.parse,xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'maps/weather-48h-2026-11-08';RAW=OUT/'raw'
BASE='https://view.eumetsat.int/geoserver/wms';W,H=1100,800;BBOX=(-12,35,41,61);CET=ZoneInfo('Europe/Warsaw')
LAYERS={'infrared':'msg_fes:ir108','mask':'msg_fes:clm'}
COLORS={'clear':'#39ff14','cloudy':'#fb7185','mixed':'#fbbf24','unknown':'#94a3b8'}
def iso(t):return t.isoformat().replace('+00:00','Z')
def dt(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
def xy(lon,lat):return (lon+12)/53*W,(61-lat)/26*H
def download(url):
 with urllib.request.urlopen(url,timeout=45) as r:return r.read()
def read(name):return json.loads((ROOT/'data'/name).read_text())
def writecsv(name,rows):
 if not rows:raise ValueError('No rows')
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def font(n,bold=False):
 p=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf')
 return ImageFont.truetype(str(p),n) if p.exists() else ImageFont.load_default(size=n)
def screen(mask,lon,lat):
 x,y=map(math.floor,xy(lon,lat));lookup={(0,192,0):'clear',(0,0,255):'clear',(255,255,255):'cloudy'}
 if x<2 or x>=W-2 or y<2 or y>=H-2:return 'unknown','unknown',None,0
 centre=lookup.get(mask.getpixel((x,y)),'unknown');vals=[lookup.get(mask.getpixel((i,j)),'unknown') for i in range(x-2,x+3) for j in range(y-2,y+3)]
 valid=[v for v in vals if v!='unknown'];fraction=valid.count('cloudy')/len(valid) if valid else None
 state='unknown' if len(valid)!=25 else 'clear' if fraction==0 else 'cloudy' if fraction==1 else 'mixed'
 return state,centre,fraction,len(valid)
def fetch(task):
 t,kind=task;filename=f'{t:%Y%m%dT%H%MZ}-{kind}.png';p=RAW/filename
 q=dict(service='WMS',version='1.3.0',request='GetMap',layers=LAYERS[kind],styles='',crs='CRS:84',bbox=','.join(map(str,BBOX)),width=W,height=H,format='image/png',time=iso(t),transparent='false',interpolations='nearest neighbor')
 url=BASE+'?'+urllib.parse.urlencode(q)
 record=dict(time_utc=iso(t),kind=kind,layer=LAYERS[kind],file='raw/'+filename,url=url,status='ok',sha256=None,error=None)
 try:
  if not p.exists():
   if ARGS.offline:raise RuntimeError('Cached file missing')
   for attempt in range(3):
    try:
     b=download(url);im=Image.open(io.BytesIO(b));im.load()
     if im.size!=(W,H):raise ValueError('Unexpected image dimensions')
     p.write_bytes(b);break
    except Exception:
     if attempt==2:raise
     time.sleep(1+attempt)
  b=p.read_bytes();im=Image.open(io.BytesIO(b));im.load()
  if im.size!=(W,H) or not im.getbbox():raise ValueError('Invalid or empty frame')
  if kind=='mask':
   counts=Counter(im.convert('RGB').get_flattened_data());record['mask_palette']={','.join(map(str,k)):v for k,v in counts.items()}
  record['sha256']=hashlib.sha256(b).hexdigest()
 except Exception as e:record.update(status='missing',error=str(e))
 return record

def analyse(times,sites,records):
 index={(r['time_utc'],r['kind']):r for r in records};rows=[];network=[]
 for t in times:
  key=iso(t);rec=index[(key,'mask')];mask=Image.open(OUT/rec['file']).convert('RGB') if rec['status']=='ok' else None
  count=Counter()
  for s in sites:
   state,centre,fraction,known=screen(mask,*s['coordinates']) if mask else ('unknown','unknown',None,0);count[state]+=1
   rows.append(dict(time_utc=key,time_poland=t.astimezone(CET).isoformat(),gateway_id=s['id'],gateway=s['name'],longitude=s['coordinates'][0],latitude=s['coordinates'][1],source_status=s['source_status'],cloud_state=state,centre_class=centre,cloud_fraction_known_pixels='' if fraction is None else fraction,known_pixels=known,total_pixels=25,mask_frame=rec['file'] if mask else '',mask_requested_time_utc=key,mask_data_status=rec['status'],mask_quality_note=rec.get('error') or '',classification_source='EUMETSAT MSG CLM rendered categorical mask',location_precision='approximate'))
  network.append(dict(time_utc=key,time_poland=t.astimezone(CET).isoformat(),**{s:count[s] for s in COLORS},gateways=len(sites)))
 writecsv('gateway-cloud-timeseries.csv',rows);writecsv('network-timeseries.csv',network)
 summary=[];intervals=[]
 for s in sites:
  sr=[r for r in rows if r['gateway_id']==s['id']];counts=Counter(r['cloud_state'] for r in sr)
  # Left endpoint sample represents a 15-minute interval; the last endpoint has zero weight.
  weights=Counter(r['cloud_state'] for r in sr[:-1]);start=0
  for i in range(1,len(sr)+1):
   if i==len(sr) or sr[i]['cloud_state']!=sr[start]['cloud_state']:
    last=i-1;intervals.append(dict(gateway_id=s['id'],gateway=s['name'],cloud_state=sr[start]['cloud_state'],first_sample_utc=sr[start]['time_utc'],last_sample_utc=sr[last]['time_utc'],first_sample_poland=sr[start]['time_poland'],last_sample_poland=sr[last]['time_poland'],sample_count=i-start,observed_span_minutes=(last-start)*15));start=i
  summary.append(dict(gateway_id=s['id'],gateway=s['name'],source_status=s['source_status'],samples=len(sr),**{state+'_samples':counts[state] for state in COLORS},**{state+'_estimated_hours':weights[state]/4 for state in COLORS},clear_sample_percent=round(100*counts['clear']/len(sr),2),clear_estimated_percent_48h=round(100*weights['clear']/(len(sr)-1),2)))
 writecsv('gateway-summary.csv',summary);writecsv('gateway-state-runs.csv',intervals)
 info=dict(start_utc=iso(times[0]),end_utc=iso(times[-1]),start_poland=times[0].astimezone(CET).isoformat(),end_poland=times[-1].astimezone(CET).isoformat(),duration_hours=(times[-1]-times[0]).total_seconds()/3600,samples=len(times),gateways=len(sites),records=len(rows),min_clear_gateways=min(r['clear'] for r in network),max_clear_gateways=max(r['clear'] for r in network),samples_without_any_clear_gateway=sum(r['clear']==0 for r in network),samples_fully_unknown=sum(r['unknown']==len(sites) for r in network),samples_without_clear_and_complete_data=sum(r['clear']==0 and r['unknown']==0 for r in network),min_clear_with_complete_data=min((r['clear'] for r in network if r['unknown']==0),default=None),max_clear_with_complete_data=max((r['clear'] for r in network if r['unknown']==0),default=None),missing_mask_frames=sum(r['kind']=='mask' and r['status']=='missing' for r in records),ambiguous_mask_frames=sum(r['kind']=='mask' and r['status']=='ambiguous_time' for r in records),missing_infrared_frames=sum(r['kind']=='infrared' and r['status']!='ok' for r in records),clear_hours_method='15-minute left-endpoint sample hold over 192 intervals; illustrative estimate, not continuous observation',all_clear_hours_any_gateway_estimate=sum(r['clear']>0 for r in network[:-1])/4)
 (OUT/'results.json').write_text(json.dumps(info,indent=2)+'\n');return rows,network,summary,info

def render(times,sites,records,rows,network):
 frames=OUT/'frames';frames.mkdir(exist_ok=True);index={(r['time_utc'],r['kind']):r for r in records};states={(r['time_utc'],r['gateway_id']):r for r in rows}
 countries=read('source-countries.json')['features'];cities=read('source-cities.json')['features']
 # Draw static cartography once. RGBA overlay is clipped to the map extent.
 overlay=Image.new('RGBA',(W,H));od=ImageDraw.Draw(overlay)
 for f in countries:
  g=f['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
  for poly in polys:
   for ring in poly:od.line([xy(x,y) for x,y,*_ in ring],fill=(90,140,160,200),width=1)
 occupied=[]
 for f in sorted(cities,key=lambda f:f['properties']['pop_max'],reverse=True):
  p=f['properties'];lon,lat=f['geometry']['coordinates'][:2]
  if not(-10<lon<40 and 36<lat<60) or not(p['adm0cap']==1 or p['pop_max']>1500000):continue
  x,y=xy(lon,lat)
  if any(abs(x-a)<75 and abs(y-b)<14 for a,b in occupied):continue
  occupied.append((x,y));od.ellipse((x-2,y-2,x+2,y+2),fill='white');od.text((x+5,y+3),p['name'],font=font(10),fill='white',stroke_width=1,stroke_fill='#0f172a')
 for i,t in enumerate(times):
  record=index[(iso(t),'infrared')]
  if record['status']=='ok':rgb=Image.open(OUT/record['file']).convert('RGBA')
  else:
   rgb=Image.new('RGBA',(W,H),'#1e293b');ImageDraw.Draw(rgb).text((20,20),'INFRARED IMAGE MISSING — cloud mask analysed separately',font=font(18),fill='white')
  rgb.alpha_composite(overlay);frame=Image.new('RGB',(W,H+180),'#0f172a');frame.paste(rgb.convert('RGB'),(0,85));d=ImageDraw.Draw(frame)
  d.text((18,9),'SWIETLIK / gateway cloud screen / last 48 hours',font=font(22,True),fill='white')
  local=t.astimezone(CET);d.text((18,41),f'{local:%d Nov %Y %H:%M} CET | {t:%H:%M} UTC | {i+1}/{len(times)} | MSG infrared + cloud mask',font=font(14),fill='#cbd5e1')
  n=network[i];d.text((18,62),f'Clear: {n["clear"]}/{len(sites)}   Cloudy: {n["cloudy"]}   Mixed: {n["mixed"]}   Unknown: {n["unknown"]}',font=font(13),fill='white')
  # Paint clear sites last so their fluorescent markers remain above nearby sites.
  for s in sorted(sites,key=lambda site:states[(iso(t),site['id'])]['cloud_state']=='clear'):
   state=states[(iso(t),s['id'])]['cloud_state'];c=COLORS[state];x,y=xy(*s['coordinates']);y+=85
   if state=='clear':
    d.ellipse((x-16,y-16,x+16,y+16),fill='#0b1220',outline=c,width=2)
    d.polygon([(x,y-12),(x-12,y+10),(x+12,y+10)],fill=c,outline='#0b1220',width=2)
   else:
    d.polygon([(x,y-6),(x-6,y+5),(x+6,y+5)],fill=c,outline='#0f172a',width=1)
   if s['name'].startswith('Wola'):
    d.text((x+8,y+8),'Wola Krobowska ~',font=font(12,True),fill=c,stroke_width=2,stroke_fill='#0f172a')
  y=H+98
  for x,(state,label) in zip([18,220,400,650],[('clear','Clear neighbourhood'),('cloudy','Cloudy'),('mixed','Mixed / uncertain'),('unknown','No data')]):
   d.ellipse((x,y,x+10,y+10),fill=COLORS[state]);d.text((x+17,y-4),label,font=font(13),fill='white')
  d.text((18,y+22),'Gateways only; approximate locations. 5x5 map pixels. No satellite visibility or optical link-budget test.',font=font(12),fill='#cbd5e1')
  d.text((18,y+43),'Contains modified EUMETSAT data © EUMETSAT 2026 | Borders/cities: Natural Earth | Gateway reports: community',font=font(10),fill='#94a3b8')
  d.text((18,y+61),'Reported planned gateways excluded. Infrared background supports day/night; marker colours use the cloud mask.',font=font(10),fill='#94a3b8')
  frame.save(frames/f'{i:03}.png')
  if i in [0,len(times)-1]:frame.save(OUT/('preview.png' if i==0 else 'last-frame.png'))
  if i%32==0:print(f'Rendered {i+1}/{len(times)}',flush=True)
 # Video contains every 15-minute frame. Streaming ffmpeg avoids retaining 193 full frames in RAM.
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','6','-i',str(frames/'%03d.png'),'-c:v','libx264','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'animation.mp4')],check=True)
 # Lightweight GitHub-compatible GIF: every hour, with the exact final endpoint.
 selected=list(range(0,len(times),4));selected+=[] if selected[-1]==len(times)-1 else [len(times)-1]
 # Reserve saturated marker colours explicitly; adaptive palettes can discard
 # small coloured markers when most of the image is monochrome infrared.
 palette=Image.new('P',(1,1));entries=[]
 for i in range(224):entries.extend([round(i*255/223)]*3)
 special=[]
 for colour in COLORS.values():
  rgb=tuple(int(colour[j:j+2],16) for j in (1,3,5))
  for factor in (1,.8,.6,.4):special.append(tuple(round(v*factor) for v in rgb))
 special.extend([(15,23,42),(11,18,32),(90,140,160),(203,213,225),(148,163,184)])
 special.extend([(57,255,20)]*(32-len(special)))
 for colour in special:entries.extend(colour)
 palette.putpalette(entries)
 gif=[]
 for i in selected:
  im=Image.open(frames/f'{i:03}.png').convert('RGB');im.thumbnail((880,784));gif.append(im.quantize(palette=palette,dither=Image.Dither.NONE))
 gif[0].save(OUT/'animation-hourly.gif',save_all=True,append_images=gif[1:],duration=300,loop=0,optimize=False)
 print('Video and hourly GIF complete.',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');p.add_argument('--download-only',action='store_true');p.add_argument('--as-of',default='2026-11-08T19:38:07Z');ARGS=p.parse_args()
 RAW.mkdir(parents=True,exist_ok=True);caps_path=OUT/'capabilities.xml';manifest_path=OUT/'manifest.json'
 if manifest_path.exists():
  previous=json.loads(manifest_path.read_text());end=dt(previous['end_utc']);start=dt(previous['start_utc'])
 else:
  caps=download(BASE+'?service=WMS&version=1.3.0&request=GetCapabilities');caps_path.write_bytes(caps);r=ET.fromstring(caps);ns={'w':'http://www.opengis.net/wms'};latest={}
  for layer in r.findall('.//w:Layer',ns):
   name=layer.findtext('w:Name','',ns)
   if name in LAYERS.values():
    dimension=layer.find('w:Dimension',ns);latest[name]=dt(dimension.text.split('/')[1])
  end=min([dt(ARGS.as_of),*latest.values()]);end=end.replace(minute=end.minute//15*15,second=0,microsecond=0);start=end-timedelta(hours=48)
 times=[start+timedelta(minutes=15*i) for i in range(193)]
 sites=[]
 for i,f in enumerate(read('gateways.geojson')['features'],1):
  prop=f['properties']
  if prop.get('source_status')!='operational':continue
  sites.append(dict(id=f'G{i:02}',name=prop['name'],coordinates=f['geometry']['coordinates'],source_status=prop['source_status']))
 tasks=[(t,k) for t in times for k in LAYERS];records=[]
 print(f'Range: {iso(start)} to {iso(end)}; {len(sites)} gateways; {len(tasks)} images',flush=True)
 with ThreadPoolExecutor(max_workers=4) as pool:
  futures=[pool.submit(fetch,task) for task in tasks]
  for completed,future in enumerate(as_completed(futures),1):
   records.append(future.result())
   if completed%20==0 or completed==len(tasks):print(f'Fetched/checked {completed}/{len(tasks)}; missing={sum(r["status"]!="ok" for r in records)}',flush=True)
 records.sort(key=lambda r:(r['time_utc'],r['kind']))
 repeats={kind:len([r for r in records if r['kind']==kind and r['status']=='ok'])-len({r['sha256'] for r in records if r['kind']==kind and r['status']=='ok'}) for kind in LAYERS}
 # Identical regional masks at different requested slots cannot establish independent acquisitions.
 # Conservatively withhold every member of a duplicate group; retain the original images for review.
 mask_groups={}
 for record in records:
  if record['kind']=='mask' and record['status']=='ok':mask_groups.setdefault(record['sha256'],[]).append(record)
 for group in mask_groups.values():
  if len(group)>1:
   slots=', '.join(record['time_utc'] for record in group)
   for record in group:record.update(status='ambiguous_time',error='Identical mask image at multiple requested slots; independent acquisition not verified: '+slots)
 manifest=dict(retrieved_as_of_utc=ARGS.as_of,start_utc=iso(start),end_utc=iso(end),bbox_crs84=BBOX,size=[W,H],interval_minutes=15,sites=sites,excluded_statuses=['planned'],repeated_hash_counts=repeats,time_note='Quarter-hour WMS requests; nearestValue=1 is advertised. Underlying scan acquisition times not independently verified; timestamps are requested slots.',attribution='Contains modified EUMETSAT data © EUMETSAT 2026',frames=records)
 manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
 rows,network,summary,info=analyse(times,sites,records);print(json.dumps(info),flush=True)
 if not ARGS.download_only:render(times,sites,records,rows,network)
