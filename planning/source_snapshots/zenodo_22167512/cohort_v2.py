"""Cohort susceptibility reconstruction, v2.
Adds: transplacental antibody term, age-eligibility for the youngest cohort,
6 prespecified sensitivity analyses. Method follows Bednarczyk et al. AJE 2016;
conditional dose specification follows Gambrell et al. Vaccine 2022.
VE 0.85/0.95 per WHO measles position paper (9-month first dose; lower than the
0.93/0.97 used for US 12-15 month schedules)."""
import csv, itertools
OUT = "../data"

# ---- parameters ----
VE1, VE2, VE_SIA = 0.85, 0.95, 0.85
REACH   = 0.90          # campaign effective reach
MAT_PROT= 0.50          # proportion of the pre-eligible infant group protected by maternal antibody
ELIG_25 = 7/12          # fraction of the 2025 birth cohort aged >=9 months by the April 2026 peak

surv={2015:3089542,2016:3138712,2017:3184230,2018:3225508,2019:3262044,2020:3293482,
      2021:3319225,2022:3345170,2023:3269440,2024:3291999,2025:3314714}
# UN WPP live births, for the denominator sensitivity
births={2020:3441465,2021:3468365,2022:3495475,2023:3360164,2024:3383349,2025:3406695}

wuenic1={2015:97,2016:97,2017:97,2018:97,2019:97,2020:97,2021:97,2022:96,2023:96,2024:96,2025:90}
wuenic2={2015:90,2016:92,2017:93,2018:93,2019:93,2020:93,2021:93,2022:93,2023:93,2024:93,2025:86}
off1={2015:90.1,2016:91.7,2017:92,2018:92,2019:92.8,2020:92.8,2021:92.8,2022:None,2023:88.6,2024:86.1,2025:86.1}
off2={2015:70.4,2016:80.5,2017:83,2018:83,2019:89,2020:89,2021:89,2022:None,2023:89.1,2024:80.7,2025:80.7}
adm1={2015:120.19,2016:117.84,2017:116.0,2018:115.41,2019:117.2,2020:108.43,2021:117.86,2022:119.65,2023:125.3,2024:123.51,2025:114.38}
adm2={2015:114.89,2016:115.15,2017:114.0,2018:113.12,2019:114.81,2020:106.95,2021:114.99,2022:116.49,2023:122.9,2024:121.38,2025:111.96}
SRC={"wuenic":(wuenic1,wuenic2),"official":(off1,off2),"admin":(adm1,adm2)}

def sfrac(c1,c2,sia_cov,ve1,ve2,reach,mat,elig,is_youngest):
    """Susceptible fraction for one birth cohort."""
    if c1 is None or c2 is None: return None
    c1=min(c1/100,1.0); c2=min(min(c2/100,1.0),c1)
    s=(1-c1)+(c1-c2)*(1-ve1)+c2*(1-ve2)
    if sia_cov: s*= (1-reach*VE_SIA)
    if is_youngest:
        # part of the cohort had reached the 9-month first-dose age by the outbreak peak;
        # the remainder were age-ineligible, partially protected by maternal antibody
        s = elig*s + (1-elig)*(1-mat)
    return s

def run(src="wuenic",ve1=VE1,ve2=VE2,reach=REACH,mat=MAT_PROT,elig=ELIG_25,denom=surv):
    d1,d2=SRC[src]; rows=[]
    for y in range(2015,2026):
        n=denom.get(y) or surv[y]
        sia = REACH if y<=2020 else 0.0          # national MR campaign Dec 2020-Feb 2021, ages 9m-<10y
        s=sfrac(d1.get(y),d2.get(y),sia,ve1,ve2,reach,mat,elig,is_youngest=(y==2025))
        rows.append((y,n,s,round(s*n) if s is not None else None))
    tot=sum(r[3] for r in rows if r[3]); pop=sum(r[1] for r in rows)
    return rows,tot,pop

base,tot_b,pop_b=run()
print(f"{'cohort':>7} {'surviving':>11} {'SIA':>4} {'susc frac':>10} {'susceptible':>12}")
for y,n,s,c in base:
    print(f"{y:>7} {n:>11,} {'yes' if y<=2020 else 'no':>4} {s:>10.4f} {c:>12,}")
print(f"\nBASELINE (WUENIC): {tot_b:,} susceptible children ({100*tot_b/pop_b:.1f}% of the 2015-2025 cohorts)")
print(f"Cohorts 2021-2025 (no supplementary dose): {sum(r[3] for r in base if r[0]>=2021):,}"
      f" ({100*sum(r[3] for r in base if r[0]>=2021)/tot_b:.1f}% of the total pool)")

# ---- sensitivity ----
scen=[("Baseline (WUENIC, VE 0.85/0.95, reach 0.90, maternal 0.50)",dict()),
      ("VE reduced 1 point (0.84/0.94)",dict(ve1=0.84,ve2=0.94)),
      ("Campaign reach 0.80",dict(reach=0.80)),
      ("Campaign reach 0.95",dict(reach=0.95)),
      ("Maternal protection 0.33 (~10 month waning)",dict(mat=0.33)),
      ("Denominator: UN WPP live births",dict(denom={**surv,**births})),
      ("Coverage source: government official",dict(src="official")),
      ("Coverage source: administrative (capped)",dict(src="admin"))]
print(f"\n{'scenario':<52} {'N susceptible':>14} {'%':>7} {'delta N':>11}")
res=[]
for lbl,kw in scen:
    r,t,p=run(**kw); res.append((lbl,t,100*t/p,t-tot_b))
    print(f"{lbl:<52} {t:>14,} {100*t/p:>6.1f}% {t-tot_b:>+11,}")

with open(f"{OUT}/bgd_cohort_susceptibility.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["birth_cohort","surviving_infants","sia_dose","susceptible_fraction","susceptible_n","coverage_source"])
    for src in SRC:
        r,_,_=run(src=src)
        for y,n,s,c in r:
            w.writerow([y,n,"YES" if y<=2020 else "NO",round(s,4) if s else "",c if c else "",src])
with open(f"{OUT}/sensitivity_analyses.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["scenario","n_susceptible","pct_susceptible","delta_from_baseline_n"])
    for lbl,t,p,d in res: w.writerow([lbl,t,round(p,2),d])
print("\nwrote bgd_cohort_susceptibility.csv and sensitivity_analyses.csv")
