import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
D="../data"; F="../figures"
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9.5,'axes.titlesize':10,
 'xtick.labelsize':8.5,'ytick.labelsize':8.5,'legend.fontsize':8.5,'axes.spines.top':False,
 'axes.spines.right':False,'axes.linewidth':.8,'figure.dpi':300,'savefig.bbox':'tight',
 'savefig.pad_inches':.05,'legend.frameon':False})
CASE='#B2182B'; SUSC='#2166AC'; GREY='#5A5A5A'; LGREY='#D9D9D9'
def save(fig,n):
    for e in ('png','pdf'): fig.savefig(f"{F}/{n}.{e}")
    plt.close(fig); print(' ',n)

mon=pd.read_csv(f"{D}/monthly_measles_bgd_neighbours.csv",parse_dates=['date'])
b=mon[mon.ISO3=='BGD']; ann=b.groupby('Year')['Measles total'].sum()
coh=pd.read_csv(f"{D}/bgd_cohort_susceptibility.csv")
w=coh[coh.coverage_source=='wuenic'].sort_values('birth_cohort')
cum={}; run=0
for r in w.itertuples():
    if r.birth_cohort>=2021: run+=r.susceptible_n; cum[r.birth_cohort]=run

# ---------- FIGURE 1 (rebuilt) ----------
yrs=list(range(2021,2027)); cases=[int(ann.loc[y]) for y in yrs]
sy=sorted(cum); sv=[cum[y]/1e6 for y in sy]
fig,ax=plt.subplots(figsize=(7.0,4.2))
ax.axvspan(2020.6,2025.9,color=LGREY,alpha=.45,zorder=0,lw=0)
ax.text(2023.25,3.1e4,'No measles campaign conducted',ha='center',fontsize=8.5,color=GREY,style='italic')
ax.annotate('',xy=(2020.75,1.55e4),xytext=(2025.8,1.55e4),arrowprops=dict(arrowstyle='<->',color=GREY,lw=.9))
ax.text(2023.25,1.15e4,'5 years, 5 birth cohorts',ha='center',fontsize=8,color=GREY)
ax.plot(yrs,cases,'-o',color=CASE,lw=2.1,ms=6,zorder=4,label='Confirmed measles cases')
ax.set_yscale('log'); ax.set_ylim(60,2.2e5)
ax.set_ylabel('Confirmed measles cases (log scale)',color=CASE); ax.tick_params(axis='y',colors=CASE)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{int(v):,}'))
for y,c in zip(yrs,cases):
    ax.annotate(f'{c:,}',(y,c),textcoords='offset points',xytext=(0,-15) if y<2026 else (0,9),
                ha='center',fontsize=8,color=CASE,fontweight='bold')
ax2=ax.twinx(); ax2.spines['top'].set_visible(False)
ax2.plot(sy,sv,'-s',color=SUSC,lw=2.1,ms=5.5,zorder=4,label='Cumulative susceptible children')
ax2.set_ylabel('Cumulative susceptible children (millions)',color=SUSC)
ax2.tick_params(axis='y',colors=SUSC); ax2.set_ylim(0,2.9)
ax2.annotate(f'{sv[-1]:.2f}M',(2025,sv[-1]),textcoords='offset points',xytext=(-4,9),
             ha='right',fontsize=8,color=SUSC,fontweight='bold')
ax.axvline(2026,color=GREY,ls=':',lw=1.1,zorder=1)
ax.text(2026.04,150,'Emergency\ncampaign\nApr 2026',fontsize=7.8,color=GREY,va='bottom')
ax.set_xlim(2020.55,2026.65); ax.set_xticks(yrs); ax.set_xlabel('Year')
h1,l1=ax.get_legend_handles_labels(); h2,l2=ax2.get_legend_handles_labels()
ax.legend(h1+h2,l1+l2,loc='upper left',bbox_to_anchor=(0.01,0.99))
ax.set_title('Measles incidence fell as susceptibility accumulated, Bangladesh 2021–2026',
             loc='left',fontweight='bold',pad=10)
save(fig,'figure1_divergence')

# ---------- FIGURE 4: sensitivity, 2016-style panels ----------
sens=pd.read_csv(f"{D}/sensitivity_analyses.csv")
base=sens.iloc[0]
fig,axes=plt.subplots(1,3,figsize=(8.6,3.9))
groups=[("Parameter assumptions",[1,2,3,4]),("Data source",[5,6,7]),("Cohort contribution",None)]
for ax,(title,idx) in zip(axes,groups):
    if idx is not None:
        sub=sens.iloc[idx]
        lbl=[s.split('(')[0].strip()[:30] for s in sub.scenario]
        ax.barh(range(len(sub)),sub.n_susceptible/1e6,color='#9E9E9E',height=.6)
        ax.axvline(base.n_susceptible/1e6,color=CASE,ls='--',lw=1.2,zorder=3)
        ax.set_yticks(range(len(sub))); ax.set_yticklabels(lbl,fontsize=7.6)
        ax.invert_yaxis()
        for i,v in enumerate(sub.n_susceptible/1e6):
            ax.text(v+.06,i,f'{v:.2f}M',va='center',fontsize=7.2)
    else:
        cs=[w[w.birth_cohort==y].susceptible_n.iloc[0]/1e6 for y in range(2015,2026)]
        cols=[SUSC if y>=2021 else '#BBBBBB' for y in range(2015,2026)]
        ax.barh(range(11),cs,color=cols,height=.7)
        ax.set_yticks(range(11)); ax.set_yticklabels(range(2015,2026),fontsize=7.6); ax.invert_yaxis()
        ax.text(.55,9.1,'no campaign\ndose',fontsize=7.4,color=SUSC,fontweight='bold')
    ax.set_title(title,fontsize=9,loc='left',fontweight='bold')
    ax.set_xlabel('Susceptible children (millions)',fontsize=8.4)
axes[0].text(base.n_susceptible/1e6+.06,-0.75,'baseline',fontsize=7.2,color=CASE)
fig.subplots_adjust(wspace=0.9)
fig.suptitle('Susceptibility estimate under alternative assumptions and data sources',
             x=.005,ha='left',fontweight='bold',fontsize=10.2,y=1.04)
save(fig,'figure4_sensitivity')
print('\ndone')
