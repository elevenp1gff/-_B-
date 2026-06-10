"""
B题 求解引擎 v3 — 完整修复版
=============================
修复：
1. 问题3利润按服务分项实算（非硬编码avg_margin）
2. 灵敏度三组真跑（非硬编码估算）
3. 统一数据输出为JSON，供figures脚本读取
"""
import numpy as np
import json, os, sys
from itertools import product, combinations

# ============================================================
# 0. 原始数据（从附件Excel核实）
# ============================================================
COMMUNITIES = ['A','B','C','D','E','F','G','H','I','J']
N_COMM = 10

# 附件1：当前人口 (总人口,60+老人,自理,半失能,失能,人均月收入)
INIT = {
    'A':(3200,712,496,152,64,3400),'B':(2800,608,408,136,64,3100),
    'C':(4100,920,632,208,80,3800),'D':(2500,544,368,120,56,2900),
    'E':(3600,784,536,176,72,3500),'F':(2200,472,328,104,40,2700),
    'G':(3900,864,592,192,80,3600),'H':(2600,568,392,128,48,3000),
    'I':(3400,736,504,168,64,3300),'J':(3000,656,456,144,56,3200),
}
P_S2M=0.045; P_M2D=0.10; DEATH=0.05; GROWTH=0.07

# 附件2：服务数据
SVC = ['助餐','日间照料','上门护理','康复理疗','助浴','紧急救助']
PAID = ['助餐','日间照料','上门护理','康复理疗','助浴']  # 5项付费

# 人均月需求 (自理,半失能,失能)
PC_DEMAND = {
    '助餐':(14,20,22),'日间照料':(8,14,18),'上门护理':(0,6,12),
    '康复理疗':(2,4,6),'助浴':(0,2,4),'紧急救助':(0.15,1,3)
}
# (单价, 直接成本)
PRICE_COST = {
    '助餐':(10,8),'日间照料':(20,16),'上门护理':(30,24),
    '康复理疗':(28,23),'助浴':(25,20),'紧急救助':(0,8)
}
CAP_RATIO = {'自理':0.20,'半失能':0.25,'失能':0.30}

# 附件3：站点参数
STATION = {
    '小型':{'build':18,'daily_mgmt':2000,'cap':1000,'subsidy_cap':1000},
    '中型':{'build':32,'daily_mgmt':3200,'cap':2000,'subsidy_cap':1800},
    '大型':{'build':45,'daily_mgmt':4400,'cap':3000,'subsidy_cap':2600},
}

# 附件4：距离矩阵
DIST = np.array([
    [0,600,1200,900,1500,1800,1300,700,1100,500],
    [600,0,800,500,1100,1400,900,400,700,300],
    [1200,800,0,700,600,900,500,900,600,700],
    [900,500,700,0,800,1100,600,300,500,400],
    [1500,1100,600,800,0,500,400,1000,500,800],
    [1800,1400,900,1100,500,0,500,1200,700,1100],
    [1300,900,500,600,400,500,0,800,400,600],
    [700,400,900,300,1000,1200,800,0,600,300],
    [1100,700,600,500,500,700,400,600,0,400],
    [500,300,700,400,800,1100,600,300,400,0],
])

# 满意度分段函数
def S1(d):
    if d is None or d>1000: return None
    if d<=300: return 1.00
    if d<=500: return 0.90
    if d<=650: return 0.75
    return 0.60

def S2(rho):
    if rho<=0.60: return 1.00
    if rho<=0.75: return 0.93
    if rho<=0.85: return 0.85
    if rho<=0.95: return 0.72
    return 0.60

def S3(ratio):
    if ratio<=1.00: return 1.00
    if ratio<=1.10: return 0.90
    if ratio<=1.20: return 0.75
    return 0.60

def ST(s1,s2,s3): 
    return np.clip(0.2*s1+0.3*s2+0.5*s3, 0.60, 1.0)

# ============================================================
# 1. 人口预测
# ============================================================
def predict_one(sc0,sm0,ds0, yrs=5):
    hist=[(sc0,sm0,ds0)]
    for _ in range(yrs):
        sc,sm,ds=hist[-1]; tot=sc+sm+ds
        sc2=sc+tot*GROWTH
        to_sm=sc2*P_S2M; to_d=sm*P_M2D
        sc3=(sc2-to_sm)*(1-DEATH)
        sm3=(sm+to_sm-to_d)*(1-DEATH)
        ds3=(ds+to_d)*(1-DEATH)
        hist.append((sc3,sm3,ds3))
    return hist

# ============================================================
# 2. α 计算（人均）
# ============================================================
def calc_alpha_percapita(comm, prices=None):
    """给定社区和价格字典→{自理α,半失能α,失能α}"""
    if prices is None:
        prices={s:PRICE_COST[s][0] for s in PAID}
    income=INIT[comm][5]
    alphas={}
    for ci,cat in enumerate(['自理','半失能','失能']):
        paid_cost=sum(PC_DEMAND[s][ci]*prices.get(s,PRICE_COST[s][0]) for s in PAID)
        cap=income*CAP_RATIO[cat]
        alphas[cat]=min(1.0, cap/paid_cost) if paid_cost>0 else 1.0
    return alphas

# ============================================================
# 3. 核心分配引擎（返回分服务人次，用于精确利润）
# ============================================================
def iterate_assignment_exact(station_comms, station_types, pop, alphas_dict,
                             price_mult=None, max_iter=20, tol=1e-3, damping=0.5):
    """
    完整分配迭代，返回分服务人次用于精确利润计算
    price_mult: n_st × len(PAID) 价格乘数矩阵（默认全1.0）
    """
    n_st=len(station_comms)
    caps=np.array([STATION[t]['cap'] for t in station_types])
    
    if price_mult is None:
        price_mult=np.ones((n_st,len(PAID)))
    
    # S1矩阵
    S1m=np.zeros((n_st,N_COMM)); valid=np.zeros((n_st,N_COMM),dtype=bool)
    for si,sc in enumerate(station_comms):
        for ci in range(N_COMM):
            s1=S1(DIST[sc][ci])
            if s1 is not None: S1m[si,ci]=s1; valid[si,ci]=True
    
    # S3向量（本站各服务平均价格满意度）
    S3v=np.array([np.mean([S3(price_mult[si,j]) for j in range(len(PAID))]) for si in range(n_st)])
    
    # 预计算各(小区,类别)的各类服务日人均需求（含α缩放）
    # daily_svc[svc_idx][(ci,cat)] = 该小区该类老人的该服务日人均次数
    daily_svc={}
    for ci,comm in enumerate(COMMUNITIES):
        alphas=alphas_dict[comm]
        for cat_idx,cat in enumerate(['自理','半失能','失能']):
            alpha=alphas[cat]
            for si_idx,svc in enumerate(SVC):
                raw=PC_DEMAND[svc][cat_idx]
                if svc in PAID: raw*=alpha
                daily_svc.setdefault(si_idx,{})[(ci,cat)]=raw/30.0
    
    # 各区各类老人数
    elder_counts={}
    for ci,comm in enumerate(COMMUNITIES):
        sc,sm,ds=pop[comm]
        elder_counts[comm]={'自理':sc,'半失能':sm,'失能':ds}
    
    # 不动点迭代
    S2v=np.ones(n_st); prev_S2=S2v.copy()
    assign=None
    
    for it in range(max_iter):
        # 综合满意度
        Sm=np.zeros((n_st,N_COMM))
        for si in range(n_st):
            for ci in range(N_COMM):
                if valid[si,ci]: Sm[si,ci]=ST(S1m[si,ci],S2v[si],S3v[si])
        
        # 分配：每个(小区,类别)选最高满意度站
        assign={}; load_svc={si:np.zeros(len(SVC)) for si in range(n_st)}
        load_total=np.zeros(n_st)
        
        for ci,comm in enumerate(COMMUNITIES):
            for cat in ['自理','半失能','失能']:
                cand=[(si,Sm[si,ci]) for si in range(n_st) if valid[si,ci]]
                if not cand: assign[(ci,cat)]=None; continue
                best_si=max(cand,key=lambda x:x[1])[0]
                assign[(ci,cat)]=best_si
                count=elder_counts[comm][cat]
                for svc_idx in range(len(SVC)):
                    d=count*daily_svc[svc_idx][(ci,cat)]
                    load_svc[best_si][svc_idx]+=d
                    load_total[best_si]+=d
        
        rho=np.clip(load_total/caps,0,1)
        new_S2=np.array([S2(r) for r in rho])
        S2v=damping*new_S2+(1-damping)*prev_S2
        
        if it>0 and np.max(np.abs(S2v-prev_S2))<tol: break
        prev_S2=S2v.copy()
    
    # === 精确利润计算 ===
    total_elderly=sum(sum(v.values()) for v in elder_counts.values())
    covered=0; sat_weighted=0
    
    for ci,comm in enumerate(COMMUNITIES):
        for cat in ['自理','半失能','失能']:
            si=assign.get((ci,cat))
            count=elder_counts[comm][cat]
            if si is not None:
                covered+=count
                sat_weighted+=ST(S1m[si,ci],S2v[si],S3v[si])*count
    
    coverage=covered/total_elderly
    avg_sat=sat_weighted/covered if covered>0 else 0
    
    profits=[]
    for si in range(n_st):
        cfg=STATION[station_types[si]]
        # 年固定成本（万元）
        annual_fixed=cfg['build']/20.0+cfg['daily_mgmt']*365/10000.0
        
        # 各服务年毛利 + 年变动成本（元→万元）
        annual_gross=0.0
        annual_variable=0.0  # 年变动成本总额
        for svc_idx,svc in enumerate(SVC):
            daily_visits=load_svc[si][svc_idx]
            annual_visits=daily_visits*365
            if svc in PAID:
                j=PAID.index(svc)
                revenue=PRICE_COST[svc][0]*price_mult[si,j]
                cost=PRICE_COST[svc][1]
                annual_gross+=annual_visits*(revenue-cost)/10000.0
                annual_variable+=annual_visits*cost/10000.0
            else:  # 紧急救助
                annual_gross+=annual_visits*(-PRICE_COST[svc][1])/10000.0  # -8元/次
                annual_variable+=annual_visits*PRICE_COST[svc][1]/10000.0
        
        # 年补贴（万元）
        daily_effective=load_total[si]  # 总人次（含紧急救助）
        subsidy_per_day=min(daily_effective*2.0, cfg['subsidy_cap'])  # 2元/人次，有日上限
        annual_subsidy=subsidy_per_day*365/10000.0
        
        # 利润率 = (营收-变动-固定+补贴) / (固定+变动)
        annual_net=annual_gross+annual_subsidy-annual_fixed
        total_cost=annual_fixed+annual_variable
        profit_rate=annual_net/total_cost if total_cost>0 else 0
        
        profits.append({
            'station':f'{COMMUNITIES[station_comms[si]]}-{station_types[si]}',
            'annual_fixed_wan':round(annual_fixed,2),
            'annual_variable_wan':round(annual_variable,2),
            'annual_gross_wan':round(annual_gross,2),
            'annual_subsidy_wan':round(annual_subsidy,2),
            'annual_net_wan':round(annual_net,2),
            'profit_rate':round(profit_rate,4),
            'daily_load':round(load_total[si],1),
            'utilization':round(rho[si],4),
            'load_by_svc':{SVC[j]:round(load_svc[si][j],1) for j in range(len(SVC))}
        })
    
    return {
        'assign':assign,'coverage':coverage,'avg_satisfaction':avg_sat,
        'S2':S2v.tolist(),'utilization':rho.tolist(),'profits':profits,
        'iterations':it+1,'n_st':n_st,
        'station_comms':station_comms,
        'station_types':station_types,
    }

# ============================================================
# 4. 问题2：枚举选址
# ============================================================
def solve_p2(pop, alphas, budget=120, cov_threshold=0.85):
    all_cand=[(ci,t) for ci in range(N_COMM) for t in ['小型','中型','大型']]
    best=None; best_sat=-1; all_res=[]
    
    max_n=min(6,int(budget/min(c['build'] for c in STATION.values())))
    for n_st in range(1,max_n+1):
        for combo in combinations(all_cand,n_st):
            cost=sum(STATION[t]['build'] for _,t in combo)
            if cost>budget: continue
            comms=[ci for ci,_ in combo]
            if len(comms)!=len(set(comms)): continue  # 同小区不重复
            
            res=iterate_assignment_exact(comms,[t for _,t in combo],pop,alphas)
            all_res.append({'n_st':n_st,'comms':comms,'types':[t for _,t in combo],
                          'cost':cost,'coverage':res['coverage'],
                          'satisfaction':res['avg_satisfaction'],'result':res})
            
            if res['coverage']>=cov_threshold and res['avg_satisfaction']>best_sat:
                best_sat=res['avg_satisfaction']; best=res
    
    if best is None:
        all_res.sort(key=lambda x:(-x['coverage'],-x['satisfaction']))
        best=all_res[0]['result']
    
    # Pareto
    pareto=[]
    sorted_r=sorted(all_res,key=lambda x:x['coverage'])
    max_s=-1
    for r in sorted_r:
        if r['satisfaction']>max_s+0.0005:
            max_s=r['satisfaction']
            pareto.append({'coverage':round(r['coverage'],4),'satisfaction':round(r['satisfaction'],4),
                          'n_st':r['n_st'],'cost':r['cost'],'comms':[COMMUNITIES[c] for c in r['comms']]})
    
    return best, pareto, all_res

# ============================================================
# 5. 问题3：定价优化
# ============================================================
PRICE_LEVELS=[0.8,0.9,1.0]  # 仅降价维度：涨价必劣化S3+收紧α，只搜≤1.0

def solve_p3(pop, base_alphas, station_comms, station_types):
    """贪心逐站搜索最优定价"""
    n_st=len(station_comms)
    best_pm=np.ones((n_st,len(PAID)))
    
    for si in range(n_st):
        best_sat_si=-1; best_p_si=best_pm[si].copy()
        for pidx in product(range(len(PRICE_LEVELS)),repeat=len(PAID)):
            mul=np.array(PRICE_LEVELS)[list(pidx)]
            test_pm=best_pm.copy(); test_pm[si]=mul
            
            # α用平均价格
            avg_mul=np.mean(test_pm,axis=0)
            alphas={}
            for comm in COMMUNITIES:
                prices={PAID[j]:PRICE_COST[PAID[j]][0]*avg_mul[j] for j in range(len(PAID))}
                alphas[comm]=calc_alpha_percapita(comm,prices)
            
            res=iterate_assignment_exact(station_comms,station_types,pop,alphas,test_pm)
            
            # 利润率检查 −5%~8%
            feasible=all(-0.05<=p['profit_rate']<=0.08 for p in res['profits'])
            if feasible and res['avg_satisfaction']>best_sat_si:
                best_sat_si=res['avg_satisfaction']; best_p_si=mul.copy()
        
        best_pm[si]=best_p_si
    
    # 最终评估
    avg_mul=np.mean(best_pm,axis=0)
    alphas={}
    for comm in COMMUNITIES:
        prices={PAID[j]:PRICE_COST[PAID[j]][0]*avg_mul[j] for j in range(len(PAID))}
        alphas[comm]=calc_alpha_percapita(comm,prices)
    final=iterate_assignment_exact(station_comms,station_types,pop,alphas,best_pm)
    
    return {'price_mult':best_pm.tolist(),'result':final}

# ============================================================
# 5b. 无补贴反事实（Counterfactual）
# ============================================================
def counterfactual_no_subsidy(pop, base_alphas, station_comms, station_types):
    """补贴=0 的反事实情景：临时置零补贴上限"""
    save_caps = {t: STATION[t]['subsidy_cap'] for t in STATION}
    for t in STATION: STATION[t]['subsidy_cap'] = 0
    
    best_pm = np.ones((len(station_comms), len(PAID)))
    for si in range(len(station_comms)):
        best_sat_si = -1; best_p_si = best_pm[si].copy()
        for pidx in product(range(len(PRICE_LEVELS)), repeat=len(PAID)):
            mul = np.array(PRICE_LEVELS)[list(pidx)]
            test_pm = best_pm.copy(); test_pm[si] = mul
            avg_mul = np.mean(test_pm, axis=0)
            alphas = {}
            for comm in COMMUNITIES:
                prices = {PAID[j]: PRICE_COST[PAID[j]][0]*avg_mul[j] for j in range(len(PAID))}
                alphas[comm] = calc_alpha_percapita(comm, prices)
            res = iterate_assignment_exact(station_comms, station_types, pop, alphas, test_pm)
            feasible = all(-0.05 <= p['profit_rate'] <= 0.08 for p in res['profits'])
            if feasible and res['avg_satisfaction'] > best_sat_si:
                best_sat_si = res['avg_satisfaction']; best_p_si = mul.copy()
        best_pm[si] = best_p_si
    
    avg_mul = np.mean(best_pm, axis=0)
    alphas = {}
    for comm in COMMUNITIES:
        prices = {PAID[j]: PRICE_COST[PAID[j]][0]*avg_mul[j] for j in range(len(PAID))}
        alphas[comm] = calc_alpha_percapita(comm, prices)
    final = iterate_assignment_exact(station_comms, station_types, pop, alphas, best_pm)
    
    for t in STATION: STATION[t]['subsidy_cap'] = save_caps[t]
    return {'price_mult': best_pm.tolist(), 'result': final}
    
    best_pm = np.ones((len(station_comms), len(PAID)))
    for si in range(len(station_comms)):
        best_sat_si = -1; best_p_si = best_pm[si].copy()
        for pidx in product(range(len(PRICE_LEVELS)), repeat=len(PAID)):
            mul = np.array(PRICE_LEVELS)[list(pidx)]
            test_pm = best_pm.copy(); test_pm[si] = mul
            avg_mul = np.mean(test_pm, axis=0)
            alphas = {}
            for comm in COMMUNITIES:
                prices = {PAID[j]: PRICE_COST[PAID[j]][0]*avg_mul[j] for j in range(len(PAID))}
                alphas[comm] = calc_alpha_percapita(comm, prices)
            res = iterate_assignment_exact(station_comms, station_types, pop, alphas, test_pm)
            feasible = all(-0.05 <= p['profit_rate'] <= 0.08 for p in res['profits'])
            if feasible and res['avg_satisfaction'] > best_sat_si:
                best_sat_si = res['avg_satisfaction']; best_p_si = mul.copy()
        best_pm[si] = best_p_si
    
    avg_mul = np.mean(best_pm, axis=0)
    alphas = {}
    for comm in COMMUNITIES:
        prices = {PAID[j]: PRICE_COST[PAID[j]][0]*avg_mul[j] for j in range(len(PAID))}
        alphas[comm] = calc_alpha_percapita(comm, prices)
    final = iterate_assignment_exact(station_comms, station_types, pop, alphas, best_pm)
    
    SUBSIDY_PER_VISIT = save_visit
    SUBSIDY_CAP_DAILY = save_cap
    return {'price_mult': best_pm.tolist(), 'result': final}

# ============================================================
# 6. 问题4：灵敏度（三组真跑 + 极端压力测试）
# ============================================================
def sensitivity_analysis(pop_default, alphas_default):
    """三组单因素实验，真跑"""
    results={}
    
    # (a) 人口结构变化
    print("  灵敏度(a): 人口结构...")
    global P_S2M,P_M2D,GROWTH
    P_S2M_save,P_M2D_save,GROWTH_save=P_S2M,P_M2D,GROWTH
    P_S2M=0.055; P_M2D=0.095; GROWTH=0.08
    
    pop_a={}
    for comm in COMMUNITIES:
        sc0,sm0,ds0=INIT[comm][2],INIT[comm][3],INIT[comm][4]
        hist=predict_one(sc0,sm0,ds0,5)
        pop_a[comm]=(round(hist[5][0]),round(hist[5][1]),round(hist[5][2]))
    alphas_a={comm:calc_alpha_percapita(comm) for comm in COMMUNITIES}
    best_a,pareto_a,all_a=solve_p2(pop_a,alphas_a)
    results['a_demographic']={'best':best_a,'pareto':pareto_a}
    
    P_S2M,P_M2D,GROWTH=P_S2M_save,P_M2D_save,GROWTH_save
    
    # (b) 成本+20%
    print("  灵敏度(b): 成本+20%...")
    STATION_save={k:v.copy() for k,v in STATION.items()}
    for t in STATION: STATION[t]['daily_mgmt']=int(STATION[t]['daily_mgmt']*1.2)
    best_b,pareto_b,all_b=solve_p2(pop_default,alphas_default)
    results['b_cost_up']={'best':best_b,'pareto':pareto_b}
    for k in STATION: STATION[k]=STATION_save[k]
    
    # (c) 预算140万
    print("  灵敏度(c): 预算140万...")
    best_c,pareto_c,all_c=solve_p2(pop_default,alphas_default,budget=140)
    results['c_budget140']={'best':best_c,'pareto':pareto_c}
    
    return results

# ============================================================
# M A I N
# ============================================================
def main():
    print("="*60)
    print("B题 求解引擎 v3 — 完整修复版")
    print("="*60)
    
    # 人口预测
    print("\n[1/5] 人口预测...")
    pop5={}; pop_hist_all={}
    for comm in COMMUNITIES:
        sc0,sm0,ds0=INIT[comm][2],INIT[comm][3],INIT[comm][4]
        hist=predict_one(sc0,sm0,ds0,5)
        pop_hist_all[comm]=hist
        pop5[comm]=(round(hist[5][0]),round(hist[5][1]),round(hist[5][2]))
    
    # α基线
    print("[2/5] 计算α矩阵...")
    alphas_base={comm:calc_alpha_percapita(comm) for comm in COMMUNITIES}
    
    # 问题2
    print("[3/5] 问题2：选址优化...")
    best2,pareto2,all2=solve_p2(pop5,alphas_base)
    
    print(f"  最优: {best2['n_st']}站, 覆盖率{best2['coverage']:.1%}, 满意度{best2['avg_satisfaction']:.3f}")
    for p in best2['profits']:
        print(f"    {p['station']}: 利用率{p['utilization']:.1%}, 利润率{p['profit_rate']:.1%}, 年净利润{p['annual_net_wan']:.1f}万")
    
    # 问题3
    print("[4/5] 问题3：定价优化...")
    p3=solve_p3(pop5,alphas_base,best2['station_comms'],best2['station_types'])
    print(f"  定价后满意度: {p3['result']['avg_satisfaction']:.3f}")
    for p in p3['result']['profits']:
        print(f"    {p['station']}: 利润率{p['profit_rate']:.1%}")
    
    # 问题4
    print("[5/6] 问题4：灵敏度分析...")
    sens=sensitivity_analysis(pop5,alphas_base)
    # 极端压力测试：预算80万
    print("[5+/6] 极端压力测试：预算80万...")
    best_stress, pareto_stress, _ = solve_p2(pop5, alphas_base, budget=80)
    
    # 无补贴反事实
    print("[5++/6] 无补贴反事实...")
    cf = counterfactual_no_subsidy(pop5, alphas_base, best2['station_comms'], best2['station_types'])
    print(f"  无补贴满意度: {cf['result']['avg_satisfaction']:.3f}")
    
    # 构建输出JSON
    output={
        'metadata':{'solver_version':'v3','date':'2026-05-22'},
        'population':{
            'year5':{comm:list(pop5[comm]) for comm in COMMUNITIES},
            'total_year5':sum(sum(v) for v in pop5.values()),
            'total_self':sum(v[0] for v in pop5.values()),
            'total_semi':sum(v[1] for v in pop5.values()),
            'total_dis':sum(v[2] for v in pop5.values()),
        },
        'alphas':{comm:alphas_base[comm] for comm in COMMUNITIES},
        'problem2':{
            'best':{
                'n_stations':best2['n_st'],
                'stations':[{'community':COMMUNITIES[best2['station_comms'][i]],
                            'type':best2['station_types'][i]} for i in range(best2['n_st'])],
                'total_budget':sum(STATION[t]['build'] for t in best2['station_types']),
                'coverage':best2['coverage'],
                'avg_satisfaction':best2['avg_satisfaction'],
                'profits':best2['profits'],
                'iterations':best2['iterations'],
            },
            'pareto':pareto2,
        },
        'problem3':{
            'price_multipliers':p3['price_mult'],
            'avg_satisfaction':p3['result']['avg_satisfaction'],
            'profits':p3['result']['profits'],
        },
        'sensitivity':{
            'a_demographic':{
                'n_stations':sens['a_demographic']['best']['n_st'],
                'coverage':sens['a_demographic']['best']['coverage'],
                'avg_satisfaction':sens['a_demographic']['best']['avg_satisfaction'],
                'profits_summary':[{'station':p['station'],'profit_rate':p['profit_rate'],
                                   'utilization':p['utilization']} for p in sens['a_demographic']['best']['profits']]
            },
            'b_cost_up':{
                'n_stations':sens['b_cost_up']['best']['n_st'],
                'coverage':sens['b_cost_up']['best']['coverage'],
                'avg_satisfaction':sens['b_cost_up']['best']['avg_satisfaction'],
                'profits_summary':[{'station':p['station'],'profit_rate':p['profit_rate'],
                                   'utilization':p['utilization']} for p in sens['b_cost_up']['best']['profits']]
            },
            'c_budget140':{
                'n_stations':sens['c_budget140']['best']['n_st'],
                'coverage':sens['c_budget140']['best']['coverage'],
                'avg_satisfaction':sens['c_budget140']['best']['avg_satisfaction'],
                'profits_summary':[{'station':p['station'],'profit_rate':p['profit_rate'],
                                   'utilization':p['utilization']} for p in sens['c_budget140']['best']['profits']]
            },
        }
    }
    
    with open('result_b_v3.json','w',encoding='utf-8') as f:
        json.dump(output,f,ensure_ascii=False,indent=2)
    print(f"\n✓ result_b_v3.json 已保存")
    return output

if __name__=='__main__':
    main()
