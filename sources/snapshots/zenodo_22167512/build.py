"""Coverage series assembly and numerator/denominator decomposition.
Source: WHO xMart WIISE public API, tables AD_COVERAGES and AD_DENOMINATORS,
plus the WUENIC 2025 revision Bangladesh country profile. Retrieved 2026-08-27.
Sentinels -9999/-4444/-2222 are JRF missing-data codes and are excluded."""
import csv, math
OUT = "../data"

# ADMIN category: year -> (target, doses, reported pct)
mcv1 = {2012:(3283685,3653134,111.0),2013:(3328672,3604266,108.279400),
2014:(3374274,3662758,108.549510),2015:(3089542.434,3713374,120.191710),
2016:(3138712,3698573,117.837280),2017:(3184230,3708164,116.0),
2018:(3225508,3722510,115.408490),2019:(3262044,3823144,117.200000),
2020:(3293482,3570965,108.425217),2021:(3319225,3912190,117.864562),
2022:(3345170,4002376,119.650000),2023:(3269440,4095382,125.300000),
2024:(3292000,4065933,123.509508),2025:(4091813,3791393,92.658022)}
mcv2 = {2013:(3328672,3284229,98.664840),2014:(3374274,3519743,104.311120),
2015:(3089542.434,3549650,114.892420),2016:(3138712,3614228,115.150040),
2017:(3184230,3638745,114.0),2018:(3225508,3648553,113.115610),
2019:(3262044,3745124,114.810000),2020:(3293482,3522323,106.948300),
2021:(3319225,3816789,114.990367),2022:(3345170,3896696,116.490000),
2023:(3269440,4016916,122.900000),2024:(3292000,3995682,121.375516),
2025:(4091813,3711076,90.695152)}
wuenic1={2014:94,2015:97,2016:97,2017:97,2018:97,2019:97,2020:97,2021:97,2022:96,2023:96,2024:96,2025:90}
wuenic2={2014:89,2015:90,2016:92,2017:93,2018:93,2019:93,2020:93,2021:93,2022:93,2023:93,2024:93,2025:86}
off1={2014:90.1,2015:90.1,2016:91.7,2017:92,2018:92,2019:92.8,2020:92.8,2021:92.8,2022:None,2023:88.6,2024:86.1,2025:86.1}
off2={2014:70.4,2015:70.4,2016:80.5,2017:83,2018:83,2019:89,2020:89,2021:89,2022:None,2023:89.1,2024:80.7,2025:80.7}
lt1 = {2020:3293482,2021:3319225,2022:3345170,2023:3269440,2024:3291999,2025:3314714}
births={2020:3441465,2021:3468365,2022:3495475,2023:3360164,2024:3383349,2025:3406695}

with open(f"{OUT}/bgd_mcv_coverage_series.csv","w",newline="") as f:
    w=csv.writer(f)
    w.writerow(["year","antigen","admin_target","admin_doses","admin_pct","wuenic_pct",
                "official_pct","denom_lt1yr","denom_births","admin_pct_on_lt1yr"])
    for yr in range(2012,2026):
        for ag,d,wu,of in (("MCV1",mcv1,wuenic1,off1),("MCV2",mcv2,wuenic2,off2)):
            if yr not in d: continue
            t,ds,p=d[yr]; l1=lt1.get(yr)
            w.writerow([yr,ag,t,ds,round(p,3),wu.get(yr,""),
                        of.get(yr) if of.get(yr) is not None else "",
                        l1 or "", births.get(yr,""),
                        round(100*ds/l1,2) if l1 else ""])

def dec(name,d,out):
    t24,ds24,p24=d[2024]; t25,ds25,p25=d[2025]
    dn=math.log(ds25/ds24); dt=math.log(t25/t24); dc=math.log(p25/p24)
    out.append(f"\n### {name}")
    out.append(f"doses    {ds24:,} -> {ds25:,}  {100*(ds25/ds24-1):+.2f}%")
    out.append(f"target   {t24:,.0f} -> {t25:,.0f}  {100*(t25/t24-1):+.2f}%")
    out.append(f"coverage {p24:.2f}% -> {p25:.2f}%  {p25-p24:+.2f} pp")
    out.append(f"identity check: {dn-dt:+.5f} vs {dc:+.5f} -> {'OK' if abs((dn-dt)-dc)<1e-4 else 'MISMATCH'}")
    out.append(f"share from dose decline       : {100*abs(dn)/abs(dc):.1f}%")
    out.append(f"share from denominator change : {100*abs(dt)/abs(dc):.1f}%")
    out.append(f"2025 coverage on 2024 target  : {100*ds25/t24:.2f}%")
    out.append(f"2025 coverage on LT_1_YEAR    : {100*ds25/lt1[2025]:.2f}%")
    pre=ds24*8/12; out.append(f"final 4 months vs 2024 rate   : {100*((ds25-pre)/(ds24*4/12)-1):+.1f}%")

o=["BANGLADESH MCV COVERAGE DECOMPOSITION 2024->2025",
   "Source: WHO xMart WIISE AD_COVERAGES + AD_DENOMINATORS, retrieved 2026-08-27"]
dec("MCV1",mcv1,o); dec("MCV2",mcv2,o)
o.append("\n### Admin target vs independent under-1 denominator")
for yr in sorted(lt1):
    o.append(f"{yr}: admin {mcv1[yr][0]:,.0f} | LT_1_YEAR {lt1[yr]:,} | ratio {mcv1[yr][0]/lt1[yr]:.4f}")
open(f"{OUT}/decomposition_results.txt","w").write("\n".join(o))
print("\n".join(o))
