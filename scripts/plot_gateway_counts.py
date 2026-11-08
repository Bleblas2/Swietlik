"""Plot cloud-free gateway counts with time on X and gateway count on Y.
Requires matplotlib. Reads cached CSV only; no network or source-image processing.
"""
import csv
from collections import Counter
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'maps/weather-48h-2026-11-08';TZ=ZoneInfo('Europe/Warsaw')
def main():
 rows=list(csv.DictReader((OUT/'network-timeseries.csv').open()))
 dates=[datetime.fromisoformat(r['time_poland']) for r in rows];ys=mdates.date2num(dates);known=[int(r['unknown'])==0 for r in rows];total=int(rows[0]['gateways']);duration=(dates[-1]-dates[0]).total_seconds()/3600
 assert len(rows)==193 and duration==48
 assert all(sum(int(r[k]) for k in ['clear','cloudy','mixed','unknown'])==total for r in rows)
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
 fig,ax=plt.subplots(figsize=(12,7));fig.subplots_adjust(left=.10,right=.95,top=.78,bottom=.29)
 values=[int(r['clear']) if k else float('nan') for r,k in zip(rows,known)]
 ax.step(ys,values,where='mid',color='#009E73',linewidth=1.8)
 ax.fill_between(ys,values,step='mid',color='#009E73',alpha=.18)
 for x,k in zip(ys,known):
  if not k:ax.axvspan(x-7.5/(24*60),x+7.5/(24*60),color='#9CA3AF',alpha=.65,lw=0)
 ax.set_xlim(ys[0],ys[-1]);ax.set_ylim(0,total);ax.set_yticks(range(0,total+1,2));ax.set_ylabel('Number of cloud-free gateways (out of 24)',labelpad=10)
 ticks=[dates[0]+timedelta(hours=i) for i in range(0,49,6)];ax.set_xticks(mdates.date2num(ticks));ax.xaxis.set_major_formatter(mdates.DateFormatter('%d Nov\n%H:%M',tz=TZ));ax.set_xlabel('Time in Poland (CET, UTC+01:00)',labelpad=12)
 ax.grid(alpha=.2);ax.set_axisbelow(True)
 fig.suptitle('SWIETLIK / cloud-free gateway candidates',fontsize=18,fontweight='bold',y=.97)
 fig.text(.10,.89,'6 Nov 2026 20:15 to 8 Nov 2026 20:15 CET | 193 quarter-hour samples',fontsize=11)
 ax.legend(handles=[Patch(color='#009E73',label='Cloud-free 5x5-pixel neighbourhood'),Patch(color='#9CA3AF',label='Uncertain source time: count withheld')],loc='lower center',bbox_to_anchor=(.5,1.015),frameon=False,fontsize=9,ncol=2)
 fig.text(.10,.075,'Complete-data samples: 1-9 clear candidates. Two slots are withheld, not counted as zero.\nApproximate community-reported gateways; 2 planned sites excluded.\nCloud screening only: satellite visibility and optical link budget are not evaluated.',fontsize=9,linespacing=1.5,color='#475569')
 fig.text(.10,.022,'Derived from EUMETSAT MSG cloud mask | Contains modified EUMETSAT data © EUMETSAT 2026',fontsize=8,color='#64748b')
 for ext in ['png','svg']:fig.savefig(OUT/f'gateway-count-by-time.{ext}',dpi=170,facecolor='white')
 plt.close(fig)
 counts=Counter(int(r['clear']) for r in rows if int(r['unknown'])==0)
 intervals=Counter(int(r['clear']) for r in rows[:-1] if int(r['unknown'])==0)
 missing_hours=sum(int(r['unknown'])>0 for r in rows[:-1])/4
 dist=[dict(clear_gateways=i,complete_data_samples=counts[i],estimated_hours=intervals[i]/4) for i in range(total+1)]
 assert sum(d['complete_data_samples'] for d in dist)==sum(known)
 assert sum(d['estimated_hours'] for d in dist)+missing_hours==48
 with (OUT/'network-clear-count-distribution.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(dist[0]));writer.writeheader();writer.writerows(dist)
 fig,ax=plt.subplots(figsize=(10,7));fig.subplots_adjust(left=.12,right=.98,top=.80,bottom=.22)
 ax.barh([d['clear_gateways'] for d in dist],[d['estimated_hours'] for d in dist],color='#009E73',height=.8)
 ax.set_yticks(range(0,total+1,2));ax.set_ylim(-.7,total+.7);ax.set_ylabel('Number of cloud-free gateways (out of 24)');ax.set_xlabel('Estimated time (hours)');ax.xaxis.set_major_locator(MaxNLocator(integer=True));ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
 fig.suptitle('Time with exactly N gateways cloud-free at once',fontsize=16,fontweight='bold',y=.96)
 fig.text(.12,.84,f'Each row is a simultaneous count, not a gateway ID | {48-missing_hours:.1f} h classified + {missing_hours:.1f} h unknown',fontsize=10)
 fig.text(.12,.075,'Time estimate: hold each sample for the following 15-minute interval; the final endpoint adds no time.\nThis is cloud-screening coverage, not measured laser-link availability. EUMETSAT MSG cloud mask, 6-8 Nov 2026.',fontsize=9,color='#475569')
 for ext in ['png','svg']:fig.savefig(OUT/f'gateway-count-duration.{ext}',dpi=170,facecolor='white')
 plt.close(fig)
 summaries=list(csv.DictReader((OUT/'gateway-summary.csv').open()))
 summaries.sort(key=lambda row:(-float(row['clear_estimated_hours']),row['gateway']))
 assert len(summaries)==total
 for row in summaries:
  assert abs(sum(float(row[state+'_estimated_hours']) for state in ['clear','cloudy','mixed','unknown'])-duration)<1e-9
 fig,ax=plt.subplots(figsize=(12,10));fig.subplots_adjust(left=.32,right=.95,top=.85,bottom=.21)
 positions=list(range(len(summaries)));hours=[float(row['clear_estimated_hours']) for row in summaries]
 ax.barh(positions,hours,color='#009E73',height=.68)
 ax.set_yticks(positions,[row['gateway'] for row in summaries],fontsize=10);ax.invert_yaxis()
 ax.set_xlim(0,duration);ax.set_xticks(range(0,49,6));ax.set_xlabel('Total estimated cloud-free time (hours out of 48)',labelpad=12)
 ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
 for y,hours_value in zip(positions,hours):ax.text(hours_value+.4,y,f'{hours_value:.2f} h',va='center',fontsize=10)
 fig.suptitle('Total cloud-free hours for each gateway',fontsize=20,fontweight='bold',y=.96)
 fig.text(.32,.89,'All 24 gateway locations | 6-8 November 2026 | Sorted by clear time',fontsize=11)
 fig.text(.32,.065,'Each row is a named gateway. Clear requires all 25 surrounding mask pixels clear.\nMixed, cloudy and unknown intervals are excluded; each site has 0.5 h unknown.\nHours use 15-minute sample hold, not continuous optical-link measurements.',fontsize=9,color='#475569',linespacing=1.5)
 fig.text(.32,.02,'Derived from EUMETSAT MSG cloud mask | © EUMETSAT 2026',fontsize=8,color='#64748b')
 for ext in ['png','svg']:fig.savefig(OUT/f'gateway-clear-hours.{ext}',dpi=170,facecolor='white')
 plt.close(fig)
 print('Wrote 3 plots (PNG + SVG) and network-clear-count-distribution.csv')
if __name__=='__main__':main()
