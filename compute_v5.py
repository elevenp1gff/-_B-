"""
v5 增强计算：3D Gini + 补贴杠杆图 + 联合压力 + Monte Carlo
"""
import sys; sys.path.insert(0,'.')
from solver_b_v3 import *
import json, os, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = r'C:\Users\eleve\Desktop\OH-WorkSpace\figures_v3'

# 读数据
pop5 = {}; alphas_base = {}
for comm in COMMUNITIES:
    sc0,sm0,ds0 = INIT[comm][2],INIT[comm][3],INIT[comm][4]
    hist = predict_one(sc0,sm0,ds0,5)
    pop5[comm] = (round(hist[5][0]),round(hist[5][1]),round(hist[5][2]))
for comm in COMMUNITIES:
    alphas_base[comm] = calc_alpha_percapita(comm)

# ============ 任务1: 3D Gini ============
print("=== 任务1: 三维Gini ===")

def gini_calc(x):
    x = np.array(sorted(x))
    n = len(x)
    if np.sum(x) == 0: return 0
    return (2*np.sum((np.arange(1,n+1))*x)/(n*np.sum(x)))-(n+1)/n

# 维度1: 满意度Gini — 从距离推算S1
stations_best = ['A','C','G','I','J']
station_idx = [COMMUNITIES.index(s) for s in stations_best]
DIST_M = np.array([[0,600,1200,900,1500,1800,1300,700,1100,500],
    [600,0,800,500,1100,1400,900,400,700,300],[1200,800,0,700,600,900,500,900,600,700],
    [900,500,700,0,800,1100,600,300,500,400],[1500,1100,600,800,0,500,400,1000,500,800],
    [1800,1400,900,1100,500,0,500,1200,700,1100],[1300,900,500,600,400,500,0,800,400,600],
    [700,400,900,300,1000,1200,800,0,600,300],[1100,700,600,500,500,700,400,600,0,400],
    [500,300,700,400,800,1100,600,300,400,0]])

sat_per = []
dist_per = []
for ci in range(10):
    min_d = min(DIST_M[ci][si] for si in station_idx)
    dist_per.append(min_d)
    if min_d <= 300: s = 1.0
    elif min_d <= 500: s = 0.9
    elif min_d <= 650: s = 0.75
    elif min_d <= 1000: s = 0.6
    else: s = 0.5
    sat_per.append(s)

alpha_per = []
for c in COMMUNITIES:
    a = alphas_base[c]
    avg_a = (a['自理']+a['半失能']+a['失能'])/3
    alpha_per.append(avg_a)

g_sat = gini_calc(sat_per)
g_acc = gini_calc(dist_per)
# 可负担性: (1-α)的Gini, 越小越好
g_aff = gini_calc([1-a for a in alpha_per])

print(f"  满意度Gini: {g_sat:.4f}")
print(f"  可达性Gini: {g_acc:.4f}")
print(f"  可负担性Gini: {g_aff:.4f}")

# ============ 任务2: 补贴杠杆图 ============
print("\n=== 任务2: 补贴杠杆图 ===")
# 读无补贴反事实
best2, _, _ = solve_p2(pop5, alphas_base, budget=120)
cf = counterfactual_no_subsidy(pop5, alphas_base, best2['station_comms'], best2['station_types'])

with_rates = [p['profit_rate']*100 for p in best2['profits']]
without_rates = [p['profit_rate']*100 for p in cf['result']['profits']]
labels = [p['station'] for p in best2['profits']]

print(f"  有补贴: {[f'{r:.1f}%' for r in with_rates]}")
print(f"  无补贴: {[f'{r:.1f}%' for r in without_rates]}")

# 画图
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
x = np.arange(len(labels)); w = 0.35
ax.bar(x-w/2, with_rates, w, label='With subsidy', color='#3A7BBF', edgecolor='white', lw=0.5)
ax.bar(x+w/2, without_rates, w, label='Without subsidy', color='#D4845A', edgecolor='white', lw=0.5)
ax.axhline(y=8, color='#C44E52', ls='--', lw=1.5, alpha=0.8)
ax.text(4.5, 8.5, '8% policy line', fontsize=9, color='#C44E52', fontstyle='italic')
ax.axhline(y=0, color='black', lw=0.8)
# G站翻转标注
g_idx = 2  # G站位置
ax.annotate('Profit→Loss', xy=(g_idx, without_rates[g_idx]), xytext=(g_idx+0.3, -12),
           arrowprops=dict(arrowstyle='->', color='#C44E52', lw=1.5),
           color='#C44E52', fontsize=10, fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10)
ax.set_ylabel('Profit rate (%)', fontsize=11)
ax.legend(fontsize=10, loc='upper right')
ax.set_title('Subsidy leverage: station profitability with vs. without subsidy', fontsize=12, fontweight='bold', pad=10)
for spine in ax.spines.values(): spine.set_linewidth(1.1)
ax.tick_params(direction='in', length=4, width=1.0, labelsize=10, top=True, right=True)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'figure16_subsidy_leverage.png'), dpi=300, bbox_inches='tight')
fig.savefig(os.path.join(OUT, 'figure16_subsidy_leverage.pdf'), bbox_inches='tight')
print("  ✓ figure16 saved")

# ============ 任务3: 联合压力情景 ============
print("\n=== 任务3: 联合压力===")
# 中度: γ=10%, cost×1.1, budget=100
global P_S2M,P_M2D,GROWTH,DEATH
save_vals = (P_S2M, P_M2D, GROWTH, DEATH)
scenarios = [
    ('Baseline', 0.045, 0.10, 0.07, 0.05, 1.0, 109),
    ('Moderate', 0.050, 0.11, 0.10, 0.05, 1.10, 100),
    ('Severe', 0.055, 0.12, 0.12, 0.05, 1.20, 90),
]
for name, psm, pmd, gr, dr, cost_f, budget in scenarios:
    P_S2M, P_M2D, GROWTH, DEATH = psm, pmd, gr, dr
    # 调成本
    save_cost = {t: STATION[t]['daily_mgmt'] for t in STATION}
    for t in STATION: STATION[t]['daily_mgmt'] = int(save_cost[t] * cost_f)
    
    pop_t = {}
    for comm in COMMUNITIES:
        sc0,sm0,ds0 = INIT[comm][2],INIT[comm][3],INIT[comm][4]
        hist = predict_one(sc0,sm0,ds0,5)
        pop_t[comm] = (round(hist[5][0]),round(hist[5][1]),round(hist[5][2]))
    
    best_t, _, _ = solve_p2(pop_t, alphas_base, budget=budget)
    avg_prof = np.mean([p['profit_rate'] for p in best_t['profits']])
    total_cap = sum(STATION[t]['cap'] for t in best_t['station_types'])
    
    # Reset
    for t in STATION: STATION[t]['daily_mgmt'] = save_cost[t]
    
    print(f"  {name}: {best_t['n_st']}站, sat={best_t['avg_satisfaction']:.3f}, avg_profit={avg_prof:.1%}")

P_S2M,P_M2D,GROWTH,DEATH = save_vals

# ============ 任务5: Monte Carlo (降级版 — 只用现有方案重算满意度) ============
print("\n=== 任务5: Monte Carlo ===")
np.random.seed(42)
N = 100
sat_samples = []
best2_comms = best2['station_comms']
best2_types = best2['station_types']
for _ in range(N):
    P_S2M = np.random.normal(0.045, 0.0045)
    P_M2D = np.random.normal(0.10, 0.010)
    GROWTH = np.random.normal(0.07, 0.007)
    pop_mc = {}
    for comm in COMMUNITIES:
        sc0,sm0,ds0 = INIT[comm][2],INIT[comm][3],INIT[comm][4]
        hist = predict_one(sc0,sm0,ds0,5)
        pop_mc[comm] = (round(hist[5][0]),round(hist[5][1]),round(hist[5][2]))
    res = iterate_assignment_exact(best2_comms, best2_types, pop_mc, alphas_base)
    sat_samples.append(res['avg_satisfaction'])

sat_samples = np.array(sat_samples)
ci_low, ci_high = np.percentile(sat_samples, [2.5, 97.5])
print(f"  Satisfaction: {np.mean(sat_samples):.4f} ± {np.std(sat_samples):.4f}")
print(f"  95% CI: [{ci_low:.4f}, {ci_high:.4f}]")

P_S2M,P_M2D,GROWTH,DEATH = save_vals

print("\n✓ v5 增强计算完成")
