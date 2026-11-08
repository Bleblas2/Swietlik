"""Create a gateway cloud-state timeline and results report from the 48h CSVs."""
import csv,json
from datetime import datetime
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'maps/weather-48h-2026-11-08'
C={'clear':'#34d399','cloudy':'#fb7185','mixed':'#fbbf24','unknown':'#94a3b8'}
def font(n,bold=False):
 p=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf')
 return ImageFont.truetype(str(p),n) if p.exists() else ImageFont.load_default(size=n)
def main():
 rows=list(csv.DictReader((OUT/'gateway-cloud-timeseries.csv').open()));summary=list(csv.DictReader((OUT/'gateway-summary.csv').open()));info=json.loads((OUT/'results.json').read_text())
 times=sorted({r['time_utc'] for r in rows});lookup={(r['gateway_id'],r['time_utc']):r for r in rows};network=list(csv.DictReader((OUT/'network-timeseries.csv').open()))
 left,top,cell,rh=310,140,5,27;width=left+cell*len(times)+100;height=top+rh*len(summary)+170
 im=Image.new('RGB',(width,height),'#0f172a');d=ImageDraw.Draw(im)
 d.text((24,18),'SWIETLIK / gateway cloud-state timeline / 48 hours',font=font(24,True),fill='white')
 d.text((24,56),f'{info["start_poland"][:16]} to {info["end_poland"][:16]} CET | {len(summary)} gateways | 193 samples, every 15 min',font=font(15),fill='#cbd5e1')
 d.text((left,94),'Time in Poland (CET)',font=font(12),fill='#94a3b8');d.text((left+len(times)*cell+12,94),'Clear %*',font=font(12),fill='white')
 for col in list(range(0,len(times),24)):
  x=left+col*cell;t=datetime.fromisoformat(times[col].replace('Z','+00:00'))
  from zoneinfo import ZoneInfo
  label=t.astimezone(ZoneInfo('Europe/Warsaw')).strftime('%d Nov %H:%M')
  d.text((x-25,117),label,font=font(11),fill='#cbd5e1')
 for row,s in enumerate(summary):
  y=top+row*rh;d.text((20,y+3),s['gateway_id']+' '+s['gateway'],font=font(12),fill='white')
  for col,t in enumerate(times):d.rectangle((left+col*cell,y,left+(col+1)*cell-1,y+rh-5),fill=C[lookup[(s['gateway_id'],t)]['cloud_state']])
  d.text((left+len(times)*cell+14,y+2),f'{float(s["clear_estimated_percent_48h"]):.1f}',font=font(12),fill='#34d399')
 y=top+rh*len(summary)+14;d.text((20,y),'Clear gateways',font=font(12),fill='white')
 for col,n in enumerate(network):
  x=left+col*cell;count=int(n['clear']);bar=34*count/len(summary)
  d.rectangle((x,y+35-bar,x+cell-1,y+35),fill='#34d399')
 y+=55
 for x,(state,label) in zip([24,270,450,690],[('clear','Clear neighbourhood'),('cloudy','Cloudy'),('mixed','Mixed / uncertain'),('unknown','No data')]):
  d.rectangle((x,y,x+12,y+12),fill=C[state]);d.text((x+20,y-3),label,font=font(13),fill='white')
 d.text((24,y+25),'Each column = one requested satellite slot. Clear requires all 25 surrounding mask pixels clear; other states stay separate.',font=font(12),fill='#cbd5e1')
 d.text((24,y+45),'* Estimated time share: 15-min left-endpoint hold over 192 intervals. No optical link or satellite visibility claim.',font=font(12),fill='#94a3b8')
 d.text((24,y+65),'Contains modified EUMETSAT data © EUMETSAT 2026 | Approximate community-reported gateway coordinates.',font=font(12),fill='#94a3b8')
 im.save(OUT/'gateway-timeline.png')
 lines=['# Gateway cloud-screening results — 6–8 November 2026','',f'Window: **{info["start_poland"]} → {info["end_poland"]}** (Poland), exactly 48 hours.','',f'{info["gateways"]} reported-operational gateways × {info["samples"]} requested quarter-hour slots = {info["records"]} records. No PoPs or reported planned gateways.','',f'Clear neighbourhoods per sample: **{info["min_clear_gateways"]}–{info["max_clear_gateways"]}**. Samples with none clear: **{info["samples_without_any_clear_gateway"]}/{info["samples"]}**. Missing cloud masks: {info["missing_mask_frames"]}; missing infrared frames: {info["missing_infrared_frames"]}; ambiguous mask slots withheld: {info["ambiguous_mask_frames"]}.','', f'Fully unknown samples: **{info["samples_fully_unknown"]}**. Among complete-data samples, clear gateways range from **{info["min_clear_with_complete_data"]} to {info["max_clear_with_complete_data"]}**; samples with no clear gateway and complete data: **{info["samples_without_clear_and_complete_data"]}**.', '', '![Gateway cloud-state timeline](gateway-timeline.png)','', '| Gateway | Clear samples | Cloudy samples | Mixed samples | Unknown samples | Estimated clear hours* |','|---|---:|---:|---:|---:|---:|']
 for s in sorted(summary,key=lambda s:float(s['clear_estimated_hours']),reverse=True):
  lines.append(f'| {s["gateway"]} | {s["clear_samples"]} | {s["cloudy_samples"]} | {s["mixed_samples"]} | {s["unknown_samples"]} | {float(s["clear_estimated_hours"]):.2f} |')
 lines+=['','*Hours use each sample as an estimate for the following 15-minute interval. The final endpoint is not given a further 15 minutes, so each site totals exactly 48 hours across all four states. Changes between scans are not observed. Clear sky above an approximate site is not proven laser-link availability.','', 'Definitions, source details and limitations: [README](README.md).']
 (OUT/'RESULTS.md').write_text('\n'.join(lines)+'\n')
 print('Wrote gateway-timeline.png and RESULTS.md')
if __name__=='__main__':main()
