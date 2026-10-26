"""Static discovery map, explicitly separate from held-out confirmation."""
import csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;D=R/'results'
rows=list(csv.DictReader((D/'scan_summary.csv').open()))
fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True)
for ax,kind,title in zip(axes,['attention','mlp'],['Attention restorations (22/23 already tested separately)','MLP restorations']):
    by={int(x['layer']):x for x in rows if x['kind']==kind}
    y=[100*float(by[i]['reduction']) if i in by else float('nan') for i in range(28)]
    ax.plot(range(28),y,color='#316d9b',marker='o',markersize=4)
    for i,x in by.items():
        if x['eligible']=='True':ax.scatter(i,100*float(x['reduction']),color='#19816b',marker='*',s=150,zorder=4)
        elif x['neutral_preserved']=='False':ax.scatter(i,100*float(x['reduction']),color='#b34745',marker='x',s=55,zorder=4)
    ax.axhline(0,color='black',linewidth=.8);ax.axhline(5,color='#19816b',linestyle=':',linewidth=1)
    ax.set_title(title,fontsize=11);ax.set_ylabel('Excess-preference reduction (pp)');ax.grid(alpha=.18)
axes[-1].set_xticks(range(28));axes[-1].set_xlabel('Zero-based transformer block')
fig.suptitle('Discovery screen: one Qwen module restored in Dolos at a time',fontsize=13)
fig.text(.5,.012,'8 reused base pairs × 2 wordings; all neutral controls retained. Green stars meet every screen criterion; red crosses fail neutral preservation.\nPositive reductions favor truth. Scan maxima are exploratory; only untouched reserve results can confirm a selected contributor.',ha='center',fontsize=8)
fig.tight_layout(rect=[0,.075,1,.95]);fig.savefig(D/'discovery_map.png',dpi=180);plt.close(fig)
