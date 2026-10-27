import pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
D="../data"; F="../figures"
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9.5,
 'xtick.labelsize':8.5,'ytick.labelsize':8.2,'axes.spines.top':False,'axes.spines.right':False,
 'axes.linewidth':.8,'figure.dpi':300,'savefig.bbox':'tight','savefig.pad_inches':.06})
CASE='#B2182B'; SUSC='#2166AC'
sens=pd.read_csv(f"{D}/sensitivity_analyses.csv")
coh=pd.read_csv(f"{D}/bgd_cohort_susceptibility.csv")
w=coh[coh.coverage_source=='wuenic'].sort_values('birth_cohort')
base=sens.iloc[0].n_susceptible/1e6

names={1:'VE reduced 1 point (0.84 / 0.94)',2:'Campaign reach 0.80',3:'Campaign reach 0.95',
       4:'Maternal protection 0.33',5:'Denominator: UN WPP live births',
       6:'Coverage source: official',7:'Coverage source: administrative'}
sub=sens.iloc[1:8].copy(); sub['lbl']=[names[i] for i in range(1,8)]

fig,(a1,a2)=plt.subplots(1,2,figsize=(9.4,3.8),gridspec_kw={'width_ratios':[1.55,1],'wspace':.55})

a1.barh(range(len(sub)),sub.n_susceptible/1e6,color='#9E9E9E',height=.62)
a1.axvline(base,color=CASE,ls='--',lw=1.3,zorder=3)
a1.set_yticks(range(len(sub))); a1.set_yticklabels(sub.lbl); a1.invert_yaxis()
for i,(v,d) in enumerate(zip(sub.n_susceptible/1e6,sub.delta_from_baseline_n)):
    a1.text(v+.07,i,f'{v:.2f}M  ({d/1000:+,.0f}k)',va='center',fontsize=7.6)
a1.set_xlim(0,4.2); a1.set_xlabel('Susceptible children (millions)')
a1.text(base+.06,-0.78,f'baseline {base:.2f}M',fontsize=7.8,color=CASE)
a1.set_title('A.  Sensitivity analyses',loc='left',fontweight='bold',pad=14)

cs=[w[w.birth_cohort==y].susceptible_n.iloc[0]/1e6 for y in range(2015,2026)]
cols=[SUSC if y>=2021 else '#C4C4C4' for y in range(2015,2026)]
a2.barh(range(11),cs,color=cols,height=.72)
a2.set_yticks(range(11)); a2.set_yticklabels(range(2015,2026)); a2.invert_yaxis()
a2.set_xlabel('Susceptible children (millions)'); a2.set_ylabel('Birth cohort')
a2.set_xlim(0,1.15)
a2.annotate('no campaign dose\nbefore the outbreak',xy=(.34,8.0),fontsize=7.8,color=SUSC,fontweight='bold')
a2.text(cs[-1]-.03,10,f'{cs[-1]:.2f}M',va='center',ha='right',fontsize=7.6,color='white',fontweight='bold')
a2.set_title('B.  Contribution by birth cohort',loc='left',fontweight='bold',pad=14)
for e in ('png','pdf'): fig.savefig(f"{F}/figure4_sensitivity.{e}")
print('figure4_sensitivity rebuilt')
