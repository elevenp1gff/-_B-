"""
论文配图 v3 — 从 JSON 读数据 + SimHei 中文字体 + Nature 极简审美
=================================================================
12 张图，SVG+PDF+PNG 三格式
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Circle, FancyBboxPatch
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches
from sklearn.manifold import MDS
from matplotlib.font_manager import FontProperties
import numpy as np
import json, os

# ============================================================
# 字体配置
# ============================================================
import matplotlib.font_manager as fm

# 强制注册 SimHei
SIMHEI_PATH = None
for f in fm.fontManager.ttflist:
    if 'simhei' in f.name.lower() or 'SimHei' in f.name:
        SIMHEI_PATH = f.fname
        break
if not SIMHEI_PATH:
    # fallback
    for f in fm.fontManager.ttflist:
        if 'msyh' in f.name.lower() or 'Microsoft YaHei' in f.name:
            SIMHEI_PATH = f.fname
            break
if not SIMHEI_PATH:
    SIMHEI_PATH = r'C:\Windows\Fonts\simhei.ttf'

fm.fontManager.addfont(SIMHEI_PATH)
hei = FontProperties(fname=SIMHEI_PATH)

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
    'font.size': 8,
    'axes.spines.right': False,
    'axes.spines.top': False,
    'axes.linewidth': 0.6,
    'legend.frameon': False,
    'figure.dpi': 150,
})

# ============================================================
# 配色（Nature-minimal: 蓝灰+暖橙+深红中性族）
# ============================================================
C = {
    'self':   '#3A6B8C',  # 自理-蓝灰
    'semi':   '#D4845A',  # 半失能-暖橙  
    'dis':    '#B8454B',  # 失能-深红
    'total':  '#4A4A4A',  # 合计-深灰
    'blue1':  '#1F4E79',  # 深蓝
    'blue2':  '#3A7BBF',  # 中蓝
    'blue3':  '#6BAED6',  # 浅蓝
    'blue4':  '#BDD7EE',  # 最浅蓝
    'green':  '#3A7D5A',  # 增益绿
    'red':    '#B8454B',  # 下降红
    'orange': '#D4845A',  # 补贴橙
    'grey':   '#8C8C8C',
    'light':  '#D0D0D0',
}

# ============================================================
# 数据加载
# ============================================================
with open(r'C:\Users\eleve\Desktop\OH-WorkSpace\result_b_v3.json', 'r', encoding='utf-8') as f:
    DATA = json.load(f)

POP = DATA['population']
ALPHAS = DATA['alphas']
P2 = DATA['problem2']['best']
PARETO = DATA['problem2']['pareto']
P3 = DATA['problem3']
SENS = DATA['sensitivity']

OUT = r'C:\Users\eleve\Desktop\OH-WorkSpace\figures_v3'
os.makedirs(OUT, exist_ok=True)

def save(fig, name):
    b = os.path.join(OUT, name)
    fig.savefig(f'{b}.svg', bbox_inches='tight', dpi=150)
    fig.savefig(f'{b}.pdf', bbox_inches='tight', dpi=150)
    fig.savefig(f'{b}.png', bbox_inches='tight', dpi=300)
    print(f'  ✓ {name}')

# ============================================================
# 图 1：人口趋势折线图
# ============================================================
COMMS = ['A','B','C','D','E','F','G','H','I','J']
def fig1():
    fig, ax = plt.subplots(figsize=(5.2, 3.3))
    # 手工数据—逐年预测（从solver population历史获取）
    # Using incremental build from solver logic
    years = [1, 2, 3, 4, 5]
    self_c = [5072, 5058, 4999, 4915, 4774]
    semi_c = [1425, 1467, 1497, 1521, 1534]
    dis_c  = [709, 837, 939, 1019, 1141]
    total_c = [sum(x) for x in zip(self_c, semi_c, dis_c)]
    
    ax.plot(years, self_c, 'o-', color=C['self'], lw=1.8, ms=5, label='Self-care')
    ax.plot(years, semi_c, 's-', color=C['semi'], lw=1.8, ms=5, label='Semi-disabled')
    ax.plot(years, dis_c, 'D-', color=C['dis'], lw=2.2, ms=6, label='Disabled')
    ax.plot(years, total_c, '^--', color=C['total'], lw=1.2, ms=5, alpha=0.5, label='Total')
    
    # 端点标注
    for yv, xv, lbl, clr in [(self_c,5,'4,774',C['self']),(semi_c,5,'1,534',C['semi']),
                               (dis_c,5,'1,141',C['dis']),(total_c,5,'7,449',C['total'])]:
        ax.text(5.15, yv[-1], lbl, fontsize=6.5, color=clr, va='center', fontweight='bold')
    
    # 增长标注
    ax.annotate('+78%', xy=(5,1141), xytext=(3.5,1500), fontsize=7,
               color=C['dis'], ha='center', fontweight='bold',
               arrowprops=dict(arrowstyle='->', color=C['dis'], lw=1))
    
    ax.set_xlabel('Year', fontsize=9)
    ax.set_ylabel('Elderly population', fontsize=9)
    ax.set_xticks(years)
    ax.set_ylim(0, 8200)
    ax.legend(fontsize=7, loc='upper left', framealpha=0.9)
    ax.set_title('Elderly population projection (Year 1–5)', fontsize=10, fontweight='bold', pad=10)
    save(fig, 'fig1_population_trend')

# ============================================================
# 图 2：α 热力图
# ============================================================
def fig2():
    fig, ax = plt.subplots(figsize=(5, 3))
    cats = ['Self-care', 'Semi-disabled', 'Disabled']
    data = np.array([[ALPHAS[c][cat] for cat in ['自理','半失能','失能']] for c in COMMS])
    
    im = ax.imshow(data, cmap='YlOrRd', aspect='auto', vmin=0.65, vmax=1.0)
    ax.set_xticks(range(3)); ax.set_xticklabels(cats, fontsize=8)
    ax.set_yticks(range(10)); ax.set_yticklabels(COMMS, fontsize=8)
    
    for i in range(10):
        for j in range(3):
            v = data[i,j]
            c = 'white' if v < 0.88 else 'black'
            ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=7, color=c, fontweight='bold')
    
    cbar = plt.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
    cbar.set_label('Scaling factor α', fontsize=8)
    ax.set_title('Consumption constraint α matrix', fontsize=10, fontweight='bold', pad=10)
    save(fig, 'fig2_alpha_heatmap')

# ============================================================
# 图 3：月消费构成
# ============================================================
def fig3():
    """月消费构成 — 点线剖面图 + 上限参考线"""
    fig, ax = plt.subplots(figsize=(5.2, 3.5))
    svcs = ['Meal', 'Daycare', 'Nursing', 'Rehab', 'Bath']
    self_c = [140,160,0,56,0]; semi_c = [200,280,180,112,50]; dis_c = [220,360,360,168,100]
    x = np.arange(len(svcs))
    markers = ['o','s','D']; colors = [C['self'],C['semi'],C['dis']]; labels = ['Self-care','Semi-disabled','Disabled']
    datasets = [self_c, semi_c, dis_c]
    for i,(d,mk,cl,lb) in enumerate(zip(datasets,markers,colors,labels)):
        ax.plot(x, d, '-', color=cl, lw=1.5, alpha=0.5, zorder=2)
        ax.scatter(x, d, s=55, c=cl, marker=mk, zorder=3, edgecolors='white', lw=0.8, label=lb)
        for xi,di in zip(x,d):
            if di > 0:
                ax.text(xi, di+10, str(di), ha='center', fontsize=6.5, color=cl, fontweight='bold')
    # 消费上限线
    ax.axhline(y=356, color=C['self'], ls=':', lw=1.2, alpha=0.7)
    ax.text(4.2, 362, 'Self-care cap (356)', fontsize=6.5, color=C['self'])
    ax.axhline(y=822, color=C['semi'], ls=':', lw=1.2, alpha=0.7)
    ax.text(4.2, 828, 'Semi-dis. cap (822)', fontsize=6.5, color=C['semi'])
    ax.set_xticks(x); ax.set_xticklabels(svcs, fontsize=7.5)
    ax.set_ylabel('Monthly cost per capita (yuan)', fontsize=8)
    ax.legend(fontsize=7, loc='upper left')
    ax.set_title('Per-capita monthly service consumption', fontsize=10, fontweight='bold', pad=10)
    save(fig, 'fig3_consumption')

# ============================================================
# 图 4：S1 分段函数
# ============================================================
def fig4():
    fig, ax = plt.subplots(figsize=(5, 2.8))
    segs = [(0,300,1.00,'#2E6B3E'),(300,500,0.90,'#4A9B5E'),(500,650,0.75,'#7DC08B'),(650,1000,0.60,'#B5DDBB')]
    for x0,x1,y,clr in segs:
        ax.hlines(y, x0, x1, colors=clr, lw=3)
        ax.vlines(x1, y, segs[segs.index((x0,x1,y,clr))+1][2] if x1<1000 else 0.55, colors=clr, ls=':', lw=1.5)
        ax.scatter([x0,x1],[y,y], s=30, color=clr, zorder=5)
        ax.text((x0+x1)/2, y+0.022, f'{y:.2f}', ha='center', fontsize=8, color=clr, fontweight='bold')
    ax.axvline(1000, color=C['red'], ls='-.', lw=0.8)
    ax.text(1010, 0.55, '>1000 m:\nno service', fontsize=7, color=C['red'])
    ax.set_xlabel('Distance (m)', fontsize=9); ax.set_ylabel('S1 score', fontsize=9)
    ax.set_xlim(-20,1080); ax.set_ylim(0.5,1.08)
    ax.set_title('Distance satisfaction S1 — piecewise step function', fontsize=10, fontweight='bold', pad=10)
    save(fig, 'fig4_S1_function')

# ============================================================
# 图 5：空间布局（MDS + 真实距离）
# ============================================================
def fig5():
    """空间布局：MDS真实距离降维坐标 + 真实比例覆盖圆 + SCI级排版"""
    fig, ax = plt.subplots(figsize=(7, 5.5), dpi=300)

    COMMS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    stations = ['A', 'C', 'G', 'I', 'J']
    idx = {c: i for i, c in enumerate(COMMS)}

    DM = [[0,600,1200,900,1500,1800,1300,700,1100,500],
          [600,0,800,500,1100,1400,900,400,700,300],
          [1200,800,0,700,600,900,500,900,600,700],
          [900,500,700,0,800,1100,600,300,500,400],
          [1500,1100,600,800,0,500,400,1000,500,800],
          [1800,1400,900,1100,500,0,500,1200,700,1100],
          [1300,900,500,600,400,500,0,800,400,600],
          [700,400,900,300,1000,1200,800,0,600,300],
          [1100,700,600,500,500,700,400,600,0,400],
          [500,300,700,400,800,1100,600,300,400,0]]

    # MDS 降维：利用距离矩阵生成具有真实物理意义的 2D 相对坐标 (单位: m)
    DM_arr = np.array(DM)
    mds = MDS(n_components=2, dissimilarity="precomputed", random_state=42)
    pos = mds.fit_transform(DM_arr)
    coords = {comm: (pos[i, 0], pos[i, 1]) for i, comm in enumerate(COMMS)}

    # 绘制通信/连接虚线 (<= 1000m)
    for c1 in COMMS:
        for c2 in COMMS:
            if idx[c1] < idx[c2] and DM[idx[c1]][idx[c2]] <= 1000:
                ax.plot([coords[c1][0], coords[c2][0]], 
                        [coords[c1][1], coords[c2][1]],
                        '--', color=C['grey'], lw=0.8, alpha=0.5, zorder=0)

    # 绘制站点覆盖面 (半径为 1000m)
    for comm in stations:
        x, y = coords[comm]
        circle = Circle((x, y), 1000, fill=True, facecolor=C['blue4'],
                        edgecolor=C['blue2'], lw=1.5, alpha=0.25, zorder=1)
        ax.add_patch(circle)

    # 绘制节点及标签
    for comm in COMMS:
        x, y = coords[comm]
        is_st = comm in stations
        if is_st:
            ax.scatter(x, y, s=160, c=C['blue1'], marker='s', zorder=5, edgecolors='white', lw=1.2)
            ax.text(x, y - 120, comm, ha='center', va='top', fontsize=11, 
                    fontweight='bold', fontname='Times New Roman', zorder=6)
        else:
            ax.scatter(x, y, s=60, c=C['light'], marker='o', zorder=4, edgecolors=C['grey'], lw=1.0)
            ax.text(x, y - 100, comm, ha='center', va='top', fontsize=10, 
                    fontname='Times New Roman', zorder=6)

    # 图例优化设计
    leg_elements = [
        Line2D([0], [0], marker='s', color='w', markerfacecolor=C['blue1'], markersize=9, label='Service Station'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=C['light'], markeredgecolor=C['grey'], markersize=7, label='Demand Community'),
        Line2D([0], [0], linestyle='--', color=C['grey'], lw=1.0, alpha=0.6, label='Distance ≤ 1000 m'),
        mpatches.Patch(facecolor=C['blue4'], edgecolor=C['blue2'], lw=1.5, alpha=0.25, label='1000 m Coverage')
    ]
    ax.legend(handles=leg_elements, loc='best', fontsize=10, framealpha=0.9, edgecolor='black', fancybox=False)

    # SCI 风格坐标轴配置
    ax.set_aspect('equal')
    ax.set_xlabel('Relative Coordinate X (m)', fontname='Times New Roman', fontsize=12)
    ax.set_ylabel('Relative Coordinate Y (m)', fontname='Times New Roman', fontsize=12)
    
    x_vals = [c[0] for c in coords.values()]
    y_vals = [c[1] for c in coords.values()]
    ax.set_xlim(min(x_vals) - 1200, max(x_vals) + 1200)
    ax.set_ylim(min(y_vals) - 1200, max(y_vals) + 1200)

    for spine in ax.spines.values():
        spine.set_linewidth(1.2)
        spine.set_color('black')
    ax.tick_params(direction='in', length=4, width=1.0, labelsize=10, top=True, right=True)

    for tick in ax.get_xticklabels() + ax.get_yticklabels():
        tick.set_fontname('Times New Roman')

    ax.set_title('Optimal Spatial Layout of Service Stations', fontsize=13, fontweight='bold', fontname='Times New Roman', pad=12)

    fig.tight_layout()
    save(fig, 'fig5_spatial_layout')

# ============================================================
# 图 6：站点利用率
# ============================================================
def fig6():
    """棒棒糖图：横轴=利用率，圆点大小=利润率"""
    fig = plt.figure(figsize=(6.4, 3.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[4.2, 1.0], wspace=0.05)
    ax  = fig.add_subplot(gs[0])
    lax = fig.add_subplot(gs[1])
    fig.subplots_adjust(left=0.10, right=0.97, top=0.86, bottom=0.16)

    # 数据 + 按利用率降序排
    labels = [p['station'] for p in P2['profits']]
    utils  = np.array([p['utilization']  for p in P2['profits']])
    rates  = np.array([p['profit_rate']  for p in P2['profits']])
    is_mid = np.array(['中' in s for s in labels])

    order  = np.argsort(-utils)
    labels = [labels[i] for i in order]
    utils, rates, is_mid = utils[order], rates[order], is_mid[order]
    clrs   = [C['blue1'] if m else C['blue2'] for m in is_mid]

    # 圆点尺寸：profit_rate 真实区间 [5%, 20%] → 面积 [90, 380]
    def r2sz(r):
        return np.interp(r, [0.05, 0.20], [90, 380])
    sz = [r2sz(r) for r in rates]
    y  = np.arange(len(labels))

    # 浅竖向网格
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, ls=':', lw=0.5, color='#DCDCDC')

    # 棒棒糖杆
    for i, (u, cl) in enumerate(zip(utils, clrs)):
        ax.plot([0, u], [i, i], '-', color=cl, lw=1.2, alpha=0.45, zorder=2)

    # 圆点
    ax.scatter(utils, y, s=sz, c=clrs, zorder=4,
               edgecolors='white', lw=1.5)

    # 圆点内：利润率数值
    for i, r in enumerate(rates):
        ax.text(utils[i], i, f'{r*100:.1f}', ha='center', va='center',
                fontsize=6.8, fontweight='bold', color='white', zorder=5)

    # 圆点右：利用率
    for i, u in enumerate(utils):
        ax.text(u + 0.025, i, f'{u:.0%}', va='center',
                fontsize=8.5, color='#2A2A2A', fontweight='bold')

    # y轴：站点名
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.tick_params(axis='y', length=0)

    # 容量上限参考线 ρ=1.0
    ax.axvline(1.0, color=C['red'], ls='--', lw=0.7, alpha=0.65, zorder=1)
    ax.text(1.005, -0.45, 'capacity', fontsize=6.8, color=C['red'],
            ha='left', va='bottom', style='italic')

    # 坐标轴
    ax.set_xlim(-0.02, 1.13)
    ax.set_ylim(-0.65, len(labels) - 0.35)
    ax.invert_yaxis()
    ax.set_xticks(np.arange(0, 1.01, 0.2))
    ax.set_xticklabels([f'{x:.0%}' for x in np.arange(0, 1.01, 0.2)])
    ax.set_xlabel('Utilization rate  ρ', fontsize=9)

    ax.set_title('Station utilization & profit rate',
                 fontsize=10.5, fontweight='bold', pad=8, loc='left')

    # 右侧图例区
    lax.set_axis_off()
    lax.set_xlim(0, 1); lax.set_ylim(0, 1)

    lax.text(0.5, 0.96, 'Profit rate', ha='center',
             fontsize=8.5, fontweight='bold')
    lax.text(0.5, 0.90, '(dot size)', ha='center',
             fontsize=6.8, color=C['grey'], style='italic')

    ref_pts = [(0.06, 0.78), (0.12, 0.60), (0.20, 0.38)]
    for r_ref, y_ref in ref_pts:
        lax.scatter(0.32, y_ref, s=r2sz(r_ref), c=C['grey'],
                    alpha=0.45, edgecolors='white', lw=1)
        lax.text(0.62, y_ref, f'{r_ref:.0%}', va='center', fontsize=8)

    # 8% 政策线提示
    lax.axhline(0.27, xmin=0.10, xmax=0.90, color=C['red'],
                ls=':', lw=0.9)
    lax.text(0.5, 0.21, '8% policy line', ha='center',
             fontsize=6.8, color=C['red'], style='italic')

    # 站型图例
    lax.text(0.5, 0.11, 'Type', ha='center',
             fontsize=8.5, fontweight='bold')
    lax.scatter(0.22, 0.03, s=70, c=C['blue1'], edgecolors='white', lw=1)
    lax.text(0.32, 0.03, 'Mid',   va='center', fontsize=7.5)
    lax.scatter(0.58, 0.03, s=70, c=C['blue2'], edgecolors='white', lw=1)
    lax.text(0.68, 0.03, 'Small', va='center', fontsize=7.5)

    # 突破8%红线的站点加★角标
    for i, r in enumerate(rates):
        if r > 0.08:
            ax.plot(utils[i] + 0.018, i - 0.18, marker='*',
                    color=C['red'], markersize=5, zorder=6)

    # ρ=0.6 S2饱和区
    ax.axvspan(0, 0.6, alpha=0.06, color=C['green'], zorder=0)
    ax.text(0.3, -0.45, 'S2 saturated', fontsize=6.5,
            color=C['green'], ha='center', style='italic')

    save(fig, 'fig6_utilization')

# ============================================================
# 图 7：Pareto 前沿
# ============================================================
def fig7():
    """图8：Pareto 前沿图 - SCI级别重构"""
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=300)
    cov = [p['coverage'] for p in PARETO]
    sat = [p['satisfaction'] for p in PARETO]
    
    ax.grid(True, linestyle='--', color=C['light'], alpha=0.5, zorder=0)
    ax.plot(cov, sat, '-', color=C['blue2'], lw=1.5, alpha=0.7, zorder=3)
    ax.scatter(cov, sat, s=50, c=C['light'], alpha=0.4, zorder=2)
    
    for i in range(len(cov)):
        clr = C['blue1'] if cov[i] >= 0.85 else C['blue3']
        ax.scatter(cov[i], sat[i], s=75, c=clr, zorder=4, edgecolors='white', lw=0.8)
    
    ax.scatter(1.0, 0.926, s=180, c=C['red'], marker='*', zorder=5, edgecolors='black', lw=0.8)
    bbox_props = dict(boxstyle="round,pad=0.4", fc="white", ec=C['red'], lw=1.2, alpha=0.9)
    arrow_props = dict(arrowstyle='->', lw=1.5, color=C['red'], connectionstyle="arc3,rad=-0.15")
    ax.annotate('Optimal\n(100%, 0.926)\n5 stations', xy=(1.0, 0.926), xytext=(0.83, 0.915),
                fontsize=10, fontname='Times New Roman', ha='center', va='center',
                bbox=bbox_props, arrowprops=arrow_props, zorder=6)
    
    ax.axvline(0.85, color=C['orange'], ls='--', lw=1.8, alpha=0.8, zorder=1)
    ax.text(0.855, 0.835, 'Constraint: >=85%', fontsize=11, color=C['orange'],
            fontweight='bold', fontname='Times New Roman')
    
    ax.set_xlabel('Coverage Rate', fontsize=12, fontname='Times New Roman')
    ax.set_ylabel('Weighted Average Satisfaction', fontsize=12, fontname='Times New Roman')
    ax.set_xlim(0.40, 1.05)
    ax.set_ylim(0.83, 0.94)
    ax.set_title('Pareto Frontier: Coverage vs. Satisfaction', fontsize=13, fontweight='bold', fontname='Times New Roman', pad=12)
    
    for spine in ax.spines.values():
        spine.set_linewidth(1.2)
        spine.set_color('black')
    ax.tick_params(direction='in', length=4, width=1.0, labelsize=11, top=True, right=True)
    for tick in ax.get_xticklabels() + ax.get_yticklabels():
        tick.set_fontname('Times New Roman')
        
    fig.tight_layout()
    save(fig, 'fig7_pareto')

# ============================================================
# 图 8：成本-收入-补贴构成
# ============================================================
def fig8():
    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    labels = [p['station'].split('-')[0] for p in P2['profits']]
    fixed = [p['annual_fixed_wan'] for p in P2['profits']]
    gross = [p['annual_gross_wan'] for p in P2['profits']]
    sub = [p['annual_subsidy_wan'] for p in P2['profits']]
    x = np.arange(len(labels)); w = 0.25
    ax.bar(x-w, fixed, w, color=C['grey'], label='Fixed cost', edgecolor='white', lw=0.3)
    ax.bar(x, gross, w, color=C['green'], label='Gross profit', edgecolor='white', lw=0.3)
    ax.bar(x+w, sub, w, color=C['orange'], label='Subsidy', edgecolor='white', lw=0.3)
    # 净利标注 — 放在柱群上方留足间距
    for i in range(len(labels)):
        top = max(fixed[i], gross[i], sub[i])
        net = P2['profits'][i]['annual_net_wan']
        ax.annotate(f'Net: {net:.0f}', xy=(i, top), xytext=(i, top+25),
                   ha='center', fontsize=7, fontweight='bold', color=C['blue1'],
                   arrowprops=dict(arrowstyle='->', lw=0.8, color=C['blue1']))
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel('Annual amount (10k yuan)', fontsize=9)
    ax.legend(fontsize=7, loc='upper left')
    ax.set_ylim(0, max(max(fixed),max(gross),max(sub))*1.35)
    ax.set_title('Cost – revenue – subsidy breakdown by station', fontsize=10, fontweight='bold', pad=10)
    save(fig, 'fig8_cost_revenue')

# ============================================================
# 图 9：灵敏度对比
# ============================================================
def fig9():
    """灵敏度 — 平行坐标图，4轴4线"""
    fig, ax = plt.subplots(figsize=(7, 3.8))
    scens = ['Baseline', 'Demographic Δ', 'Cost +20%', 'Budget 140']
    # 四个指标归一化到[0,1]
    raw = [
        [5, 0.926, 1.0, 109],   # baseline
        [SENS['a_demographic']['n_stations'], SENS['a_demographic']['avg_satisfaction'], 1.0, 109],
        [SENS['b_cost_up']['n_stations'], SENS['b_cost_up']['avg_satisfaction'], 1.0, 109],
        [SENS['c_budget140']['n_stations'], SENS['c_budget140']['avg_satisfaction'], 1.0, 140],
    ]
    # 归一化
    mins = [3, 0.915, 0.95, 100]; maxs = [7, 0.945, 1.05, 150]
    normed = [[(v-mn)/(mx-mn) for v,mn,mx in zip(row,mins,maxs)] for row in raw]
    axes_pos = [1,2,3,4]
    colors = [C['blue1'], C['blue2'], C['blue3'], C['blue4']]
    for i,(row,cl,sc) in enumerate(zip(normed, colors, scens)):
        lw = 2.5 if i == 0 else 1.5
        ax.plot(axes_pos, row, 'o-', color=cl, lw=lw, ms=7 if i==0 else 5, label=sc,
               markeredgecolor='white', markeredgewidth=0.8)
    # 轴标签
    ax.set_xticks(axes_pos)
    ax.set_xticklabels(['Stations', 'Satisfaction', 'Coverage', 'Budget (10k)'], fontsize=8)
    # 在各轴上标注实际值范围
    for j,(ax_pos,mn,mx,unit) in enumerate(zip(axes_pos,mins,maxs,['','','',''])):
        # 标几个刻度
        for t in np.linspace(0,1,4):
            val = mn + t*(mx-mn)
            if j==0: s = f'{val:.0f}'
            elif j==1: s = f'{val:.3f}'
            elif j==2: s = f'{val:.0%}'
            else: s = f'{val:.0f}'
            ax.text(ax_pos-0.08, t, s, ha='right', va='center', fontsize=5.5, color=C['grey'])
    ax.set_ylim(-0.05, 1.05)
    ax.legend(fontsize=7, loc='upper left', framealpha=0.85)
    ax.set_title('Sensitivity analysis — parallel coordinates', fontsize=10, fontweight='bold', pad=10)
    save(fig, 'fig9_sensitivity')

# ============================================================
# 图 10：人口结构环形图
# ============================================================
def fig10():
    """图12：人口结构演化环形图 - SCI级别重构"""
    fig, axes = plt.subplots(1, 5, figsize=(9, 3), dpi=300)
    yrs = [1, 2, 3, 4, 5]
    data_y = [(5072,1425,709),(5058,1467,837),(4999,1497,939),(4915,1521,1019),(4774,1534,1141)]
    clrs_pie = [C['self'], C['semi'], C['dis']]
    labels = ['Self-care', 'Semi-disabled', 'Disabled']
    
    wedges_list = []
    for ax_i, (yr, (s, m, d)) in enumerate(zip(yrs, data_y)):
        ax = axes[ax_i]
        total = s + m + d
        wedges, _ = ax.pie([s/total, m/total, d/total], colors=clrs_pie, startangle=90,
                           wedgeprops=dict(width=0.35, edgecolor='white', lw=1.5))
        if ax_i == 0:
            wedges_list = wedges
        ax.text(0, 0, f'Year {yr}\n{total}', ha='center', va='center',
                fontsize=11, fontweight='bold', fontname='Times New Roman')
    
    fig.legend(wedges_list, labels, loc='lower center', fontsize=11, ncol=3,
               bbox_to_anchor=(0.5, 0.02), frameon=False)
    fig.suptitle('Population Structure Evolution', fontsize=14, fontweight='bold', fontname='Times New Roman', y=1.02)
    plt.subplots_adjust(bottom=0.25, top=0.85, wspace=0.1)
    save(fig, 'fig10_structure')

# ============================================================
# 图 11：α vs 收入散点
# ============================================================
def fig11():
    """图13：α vs 收入散点图 - SCI级别重构"""
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=300)
    incomes = {'A':3400,'B':3100,'C':3800,'D':2900,'E':3500,'F':2700,'G':3600,'H':3000,'I':3300,'J':3200}
    
    ax.grid(True, linestyle='--', color=C['light'], alpha=0.5, zorder=0)
    
    json_keys = [('Self-care', '自理', C['self'], 'o'),
                 ('Semi-disabled', '半失能', C['semi'], 's'),
                 ('Disabled', '失能', C['dis'], 'D')]
                 
    for label, jkey, clr, mk in json_keys:
        xs = [incomes[c] for c in COMMS]
        ys = [ALPHAS[c][jkey] for c in COMMS]
        ax.scatter(xs, ys, s=65, c=clr, marker=mk, label=label, edgecolors='black', lw=0.8, zorder=4)
        z = np.polyfit(xs, ys, 1)
        p = np.poly1d(z)
        x_line = np.linspace(min(xs) - 100, max(xs) + 100, 100)
        ax.plot(x_line, p(x_line), color=clr, ls='-', lw=1.5, alpha=0.35, zorder=3)
    
    ax.set_xlabel('Monthly Income per Capita (Yuan)', fontsize=12, fontname='Times New Roman')
    ax.set_ylabel(r'Scaling Factor α', fontsize=12, fontname='Times New Roman')
    ax.legend(fontsize=10, loc='best', framealpha=0.9, edgecolor='black', fancybox=False)
    ax.set_title('Correlation between α and Community Income', fontsize=13, fontweight='bold', fontname='Times New Roman', pad=12)
    
    for spine in ax.spines.values():
        spine.set_linewidth(1.2)
        spine.set_color('black')
    ax.tick_params(direction='in', length=4, width=1.0, labelsize=11, top=True, right=True)
    for tick in ax.get_xticklabels() + ax.get_yticklabels():
        tick.set_fontname('Times New Roman')
        
    fig.tight_layout()
    save(fig, 'fig11_alpha_income')

# ============================================================
# 图 12：服务需求结构
# ============================================================
def fig12():
    """服务需求结构 — 改用水平柱状图，避免环形标注重叠"""
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    svcs = ['Meal assist', 'Daycare', 'Home nursing', 'Rehab therapy', 'Bathing', 'Emergency']
    total_self = sum(POP['year5'][c][0] for c in COMMS)
    total_semi = sum(POP['year5'][c][1] for c in COMMS)
    total_dis = sum(POP['year5'][c][2] for c in COMMS)
    pc = {'助餐':(14,20,22),'日间照料':(8,14,18),'上门护理':(0,6,12),'康复理疗':(2,4,6),'助浴':(0,2,4),'紧急救助':(0.15,1,3)}
    dems = []
    for svc in ['助餐','日间照料','上门护理','康复理疗','助浴','紧急救助']:
        d = total_self*pc[svc][0] + total_semi*pc[svc][1] + total_dis*pc[svc][2]
        dems.append(d)
    total_d = sum(dems)
    sizes = [d/total_d*100 for d in dems]
    clrs_s = [C['blue1'],C['blue2'],C['blue3'],C['blue4'],C['light'],C['orange']]
    
    bars = ax.barh(range(len(svcs)), sizes, color=clrs_s, height=0.55, edgecolor='white', lw=0.5)
    for i,(b,s) in enumerate(zip(bars, sizes)):
        ax.text(b.get_width()+0.5, i, f'{s:.1f}%', va='center', fontsize=8, fontweight='bold')
    ax.set_yticks(range(len(svcs)))
    ax.set_yticklabels(svcs, fontsize=8)
    ax.set_xlabel('Share of total monthly visits (%)', fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, max(sizes)*1.18)
    ax.set_title('Service demand composition (Year 5)', fontsize=10, fontweight='bold', pad=10)
    save(fig, 'fig12_service_mix')

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    print('Generating 12 figures (Nature-minimal style, JSON-driven)...\n')
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6()
    fig7(); fig8(); fig9(); fig10(); fig11(); fig12()
    print(f'\nDone. All figures in {OUT}/')
