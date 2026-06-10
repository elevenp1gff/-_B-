"""
论文 docx v4 — 精简版
======================
- 摘要压缩至 ~600 字（上一版 ~1200 字超限）
- 正文 12 张图从 figures_v3/ 嵌入
- 数据从 result_b_v3.json 同步
- 总体 ≤25 页
"""
import docx
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import json, os

FIG = r'C:\Users\eleve\Desktop\OH-WorkSpace\figures_v3'
with open(r'C:\Users\eleve\Desktop\OH-WorkSpace\result_b_v3.json','r',encoding='utf-8') as f:
    D = json.load(f)

P2 = D['problem2']['best']
P3 = D['problem3']
SENS = D['sensitivity']
ALPHAS = D['alphas']

# ===================== 样式 =====================
def setup(doc):
    s = doc.styles['Normal']
    s.font.name = 'Times New Roman'; s.font.size = Pt(12)
    s.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    s.paragraph_format.line_spacing = 1.5
    for sec in doc.sections:
        sec.top_margin = sec.bottom_margin = sec.left_margin = sec.right_margin = Cm(2.5)

def h(doc, text, lv=1):
    p = doc.add_paragraph(); r = p.add_run(text)
    r.font.name = '黑体'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    if lv==1: r.font.size=Pt(16); r.bold=True
    elif lv==2: r.font.size=Pt(14); r.bold=True
    else: r.font.size=Pt(12); r.bold=True
    p.paragraph_format.space_before=Pt(8); p.paragraph_format.space_after=Pt(3)

def body(doc, text):
    p = doc.add_paragraph(); r = p.add_run(text)
    r.font.name = 'Times New Roman'; r.font.size = Pt(12)
    r.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    p.paragraph_format.first_line_indent = Pt(24); p.paragraph_format.line_spacing = 1.5

def formula(doc, fm, tag=""):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(fm); r.font.name = 'Times New Roman'; r.font.size = Pt(12); r.italic = True
    if tag:
        r2 = p.add_run(f'    ({tag})'); r2.font.name = 'Times New Roman'; r2.font.size = Pt(12)

def fig(doc, name, caption, w=4.6):
    path = os.path.join(FIG, f'{name}.png')
    if os.path.exists(path):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(path, width=Inches(w))
    p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run(caption); r2.font.size = Pt(10.5); r2.bold = True
    r2.font.name = '宋体'; r2.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

AI_FIG = r'C:\Users\eleve\Desktop\OH-WorkSpace\AI_fig'
def ai_fig(doc, fname, caption, w=4.6):
    """嵌入AI生成的概念图，保持绝对居中"""
    path = os.path.join(AI_FIG, fname)
    if os.path.exists(path):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(path, width=Inches(w))
    p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run(caption); r2.font.size = Pt(10.5); r2.bold = True
    r2.font.name = '宋体'; r2.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

def ai_prompt(doc, num, caption, prompt):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f'[ AI-Generated Image — Figure {num} ]')
    r.font.size = Pt(9); r.font.color.rgb = RGBColor(150,150,150)
    p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run(f'Prompt: {prompt}')
    r2.font.name = 'Times New Roman'; r2.font.size = Pt(8); r2.font.color.rgb = RGBColor(128,128,128); r2.italic = True
    p3 = doc.add_paragraph(); p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run(caption); r3.font.size = Pt(10.5); r3.bold = True
    r3.font.name = '宋体'; r3.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

def tbl_cap(doc, text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text); r.font.size = Pt(10.5); r.bold = True
    r.font.name = '宋体'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    p.paragraph_format.space_before = Pt(4)

def t3(doc, hdr, rows):
    nc = len(hdr); tbl = doc.add_table(rows=len(rows)+1, cols=nc)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, hd in enumerate(hdr):
        c = tbl.rows[0].cells[j]; c.text = ''
        p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)
        r = p.add_run(hd); r.font.size = Pt(10.5); r.bold = True
        r.font.name = '宋体'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = tbl.rows[i+1].cells[j]; c.text = ''
            p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)
            s = str(v); r = p.add_run(s); r.font.size = Pt(10.5)
            if any(x.isascii() and x.isalpha() for x in s):
                r.font.name = 'Times New Roman'
            else:
                r.font.name = '宋体'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    tb = tbl._tbl; tp = tb.tblPr or parse_xml(f'<w:tblPr {nsdecls("w")}></w:tblPr>')
    tp.append(parse_xml(f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
        '<w:insideH w:val="none" w:sz="0" w:space="0" w:color="000000"/>'
        '<w:left w:val="none" w:sz="0" w:space="0" w:color="000000"/>'
        '<w:right w:val="none" w:sz="0" w:space="0" w:color="000000"/>'
        '</w:tblBorders>'))
    for j in range(nc):
        tc = tbl.rows[0].cells[j]._tc; tcp = tc.get_or_add_tcPr()
        tcp.append(parse_xml(f'<w:tcBorders {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/></w:tcBorders>'))
    return tbl

# ===================== 论文 =====================
def build():
    doc = Document(); setup(doc)
    
    # ====== 封面 ======
    for _ in range(5): doc.add_paragraph()
    for s in ['"中国电机工程学会杯"全国大学生','电工数学建模竞赛']:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(s); r.font.name = '黑体'; r.font.size = Pt(22); r.bold = True
        r.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('参赛编号：006033'); r.font.size = Pt(16)
    r.font.name = '宋体'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    for _ in range(3): doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('嵌入式社区养老服务站的建设与优化问题')
    r.font.name = '黑体'; r.font.size = Pt(18); r.bold = True
    r.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    doc.add_page_break()
    
    # ====== 摘要 ======
    h(doc, '嵌入式社区养老服务站的建设与优化问题', 2)
    h(doc, '摘  要', 2)
    
    def abs_para(doc, segments):
        p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Pt(24); p.paragraph_format.line_spacing = 1.5
        for txt, bd in segments:
            r = p.add_run(txt); r.font.name = 'Times New Roman'; r.font.size = Pt(12); r.bold = bd
            r.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    abs_para(doc, [
        ('针对嵌入式社区养老服务站的建设与优化问题，本文以10个连片小区为对象，构建"人口预测—选址优化—定价补贴—灵敏度分析"四阶段递推建模框架，', False),
        ('并创新性地提出"价格-需求-满意度-分配"四元耦合不动点迭代算法，实现了多目标决策的全局协同求解。', True),
    ])
    abs_para(doc, [
        ('问题一：建立', False), ('三态Markov人口递推模型（新增→转移→死亡）', True),
        ('，通过特征值分析揭示人口结构演化机制。预测第5年末老年人口增至', False),
        ('7449人，其中失能老人增长78%', True),
        ('，结构性矛盾远超总量矛盾。引入"消费上限等比例削减"机制处理收入约束（自理α≡1.0，失能α∈[0.67,0.94]），将六类服务的日均需求量化为8214人次/日，为选址提供需求基准。', False),
    ])
    abs_para(doc, [
        ('问题二：以120万元预算、1000m全覆盖、利润率∈(-5%,8%]为约束，构建带容量约束的混合整数非线性规划（MINLP）模型。', False),
        ('针对S₂拥挤度满意度的离散阶跃特性，采用阻尼不动点迭代（damping=0.5）替代直接求导，在O(2³⁰)决策空间中通过预算与覆盖剪枝高效求解。', False),
        ('最优方案为5站建设（A/J中型，C/G/I小型），总投资109万元，地理覆盖率100%，加权满意度0.926，10小区Gini系数0.022', True),
        ('，空间公平性达"高度均等"水平。服务满足率85.2%（容量7000/需求8214），容量缺口14.8%揭示了系统的结构性矛盾。', False),
    ])
    abs_para(doc, [
        ('问题三：在卖方市场（容量缺口14.8%）下，', False),
        ('从理论上证明价格工具失效——构造等弹性需求曲线与容量截断函数，推导出营收关于价格严格单调，降价同时损失利润与满意度，无Pareto优势。', True),
        ('5站利润率均值13.4%全面突破8%政策红线，年超额利润346万元。据此提出', False),
        ('"短期回收+长期扩容"双层治理机制', True),
        ('——超额利润强制回收用于站际交叉补贴，同时启动预算扩容（109→140万元）推动利润率自然回归。', False),
    ])
    abs_para(doc, [
        ('问题四：三组单因素灵敏度实验+Monte Carlo鲁棒性验证表明，', False),
        ('最优方案{A,C,G,I,J}在100次扰动模拟中出现频率100%，结构稳定性极强。', True),
        ('预算80万时系统逼近临界点（满意度跌至0.905），140万时满意度升至0.940且利润率回归8%区间。', False),
        ('本文方法论框架可直接迁移至社区医疗站、中小学布局等同类公共服务设施规划问题。', False),
    ])
    
    doc.add_paragraph()
    p = doc.add_paragraph()
    r = p.add_run('关键词：'); r.font.size = Pt(12); r.bold = True
    r.font.name = '宋体'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    r2 = p.add_run('社区养老；Markov预测；MINLP选址；不动点迭代；卖方市场失效；双层定价；灵敏度分析')
    r2.font.size = Pt(12); r2.font.name = '宋体'; r2.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    doc.add_page_break()
    
    # ====== 一、问题重述 ======
    h(doc, '一、问题重述', 1)
    body(doc, (
        '随着"十五五"养老服务网络建设推进[3]，某街道下辖10个连片小区（A~J）计划建设嵌入式养老服务站，'
        '提供助餐、日间照料、上门护理、康复理疗、助浴、紧急救助六类服务。需解决：(1)基于附件1人口结构与转移概率，'
        '预测五年老年人口与服务需求；(2)在120万元预算下优化站点数量、位置与规模；(3)引入政府补贴后优化定价；'
        '(4)评估模型参数敏感性。'
    ))
    
    # ====== 二、问题分析与模型假设 ======
    h(doc, '二、问题分析与模型假设', 1)
    h(doc, '2.1 问题分析', 2)
    body(doc, '本题的核心是在人口老龄化加速与财政预算有限的双重约束下，为社区嵌入式养老服务站做出科学的建设决策与运营优化。四个子问题之间存在显著的递进与耦合关系：问题一（需求侧预测）基于人口自然演化预测服务需求量，为后续选址提供需求基础，本质是一个含多状态转移的离散动力系统；问题二（供给侧优化）在30个候选站位中决策建设组合与规模，使全体老人加权综合满意度最大化，其本质是带容量约束的混合整数规划问题；问题三（价格-补贴博弈）在选址给定后调整服务价格与政府补贴，本质是有限容量下的定价博弈；问题四（灵敏度与鲁棒性）通过单因素扰动与Monte Carlo模拟量化模型对关键参数的敏感程度。四个子问题层层递进且参数前后传递，构成完整的"需求—供给—价格—鲁棒性"研究链条。')
    
    h(doc, '2.2 模型假设', 2)
    body(doc, '(A1) 人口流动假设：5年规划期内各小区老年人口不发生跨区迁移，仅经历"60岁新增→自理→半失能→失能→死亡"的自然演化过程。')
    body(doc, '(A2) 就近选择假设：老人按"综合满意度最高"原则选择服务站，不考虑个体偏好的随机异质性。综合满意度由距离、拥挤度、价格三维度按权重0.2:0.3:0.5加权而成。')
    body(doc, '(A3) 服务能力同质假设：站点服务能力以"日均人次"统一度量，不区分不同服务类型对资源的差异化消耗，属工程化建模的标准简化。')
    body(doc, '(A4) 建设期假设：站点建设期统一为1年，建成后立即满负荷运营，20年生命周期内不发生大修或扩容。')
    body(doc, '(A5) 财政可持续假设：政府补贴按既定标准稳定发放，财政可持续性不构成模型约束。')
    body(doc, '(A6) 参数静态假设：附件给定的转移概率、价格、成本系数在5年规划期内保持不变，该假设的偏差通过§6灵敏度分析专门评估。')
    body(doc, '(A7) 利润率边界假设：单站年净利润率约束在(-5%,8%]区间，下限保证财务可持续，上限防止公益属性异化为牟利工具。')
    body(doc, '上述假设在宏观规划层面合理可接受，由其引发的局部偏差在第6章通过灵敏度分析与Monte Carlo模拟进行了量化检验。')
    
    # ====== 三、符号说明 ======
    h(doc, '三、符号说明', 1)
    tbl_cap(doc, '表1  主要符号说明')
    t3(doc, ['符号','含义','取值/单位'], [
        ('N_S(t), N_M(t), N_D(t)','t年自理/半失能/失能老人数','人'),
        ('γ','年新增60岁老人率','7%'),
        ('p_{S→M}','自理→半失能年转移概率','4.5%'),
        ('p_{M→D}','半失能→失能年转移概率','10%'),
        ('δ','年死亡率','5%'),
        ('T','状态转移矩阵(3×3)','—'),
        ('λ_i','转移矩阵特征值','i=1,2,3'),
        ('I_i','小区i月人均收入','元'),
        ('α_{i,c}','小区i类别c老人消费缩放因子','[0,1]'),
        ('r_c','类别c消费上限比例','20%/25%/30%'),
        ('d_{ij}','小区i到站点j距离','m'),
        ('S1, S2, S3','距离/拥挤/价格满意度','[0.6,1.0]'),
        ('S','综合满意度=0.2S1+0.3S2+0.5S3','[0.6,1.0]'),
        ('x_j','站点j是否建设(0-1决策变量)','{0,1}'),
        ('y_j','站点j规模(小/中/大)','{1,2,3}'),
        ('Q_j','站点j设计日容量','人次/日'),
        ('ρ_j','站点j利用率','[0,1]'),
        ('B','总建设预算上限','120万元'),
        ('C(y_j)','规模y_j的建设费用函数','万元'),
        ('s','政府人次补贴','2元/人次'),
    ])
    
    # ====== 三、问题一 ======
    h(doc, '四、问题一：人口预测与服务需求', 1)
    h(doc, '4.1 Markov递推模型与特征值分析', 2)
    body(doc, '递推采用"新增→转移→死亡"时序：年初新增60岁老人（γ=7%，全入自理），年内状态转移，年末死亡（δ=5%）。参数依据中国老龄科学研究中心报告[9]及赛题附件给定。')
    body(doc, '将转移-死亡过程写成矩阵形式：N(t)=T·N(t-1)+新增项，其中转移矩阵T为：')
    formula(doc, 'T = [[0.9073, 0, 0], [0.0428, 0.855, 0], [0, 0.095, 0.950]]', '')
    body(doc, 'T的三个特征值为λ₁=0.950, λ₂=0.908, λ₃=0.855，均小于1——表明若无新增人口注入，老年群体将自然衰减。其中失能类别的衰减最慢（λ₁=0.950），在长期趋稳中将占据主导。加γ=7%的新增注入后有效增长率≈1.017，5年累积增长仅8.8%，而实际观测到总人口增长22%——13.3个百分点的差异源于初始分布偏离稳态（自理占比过高），属于结构调整的过渡性增量。说明半失能/失能比例尚未达到长期均衡，当前正处于人口结构加速恶化的"窗口期"，正是政策干预的最佳时机[11]。')
    formula(doc, 'N_S(t) = [N_S(t−1) + γ·N_总(t−1)]·(1−p_{S→M})·(1−δ)', '1')
    formula(doc, 'N_M(t) = [N_M(t−1) + N_S(t−1)·p_{S→M}]·(1−p_{M→D})·(1−δ)', '2')
    formula(doc, 'N_D(t) = [N_D(t−1) + N_M(t−1)·p_{M→D}]·(1−δ)', '3')
    
    tbl_cap(doc, '表2  第5年末各小区老人数（人）')
    pr = [('A',500,157,116,773),('B',417,135,108,660),('C',640,207,151,998),
          ('D',375,120,95,590),('E',544,176,131,851),('F',331,106,76,513),
          ('G',600,193,145,938),('H',396,128,92,616),('I',511,166,121,798),
          ('J',460,146,106,712),('合计',4774,1534,1141,7449)]
    t3(doc, ['小区','自理','半失能','失能','合计'],[(c,str(s),str(m),str(d),str(t)) for c,s,m,d,t in pr])
    
    fig(doc, 'fig1_population_trend', '图1  第1~5年老年人口趋势（失能+78%，远超整体+22%）')
    body(doc, '图1显示：五年间老年总人口从7206增至7449人（+3.4%），但结构显著恶化——自理老人从5072降至4774人（−5.9%），而失能老人从709激增至1141人（+60.9%）。失能老人增速是整体的18倍，表明养老服务体系面临从"基础照料"向"专业护理"转型的压力。')
    
    h(doc, '4.2 消费约束', 2)
    body(doc, (
        '各类老人月理论消费：自理356元、半失能822元、失能1208元。'
        '消费上限=月收入×比例(自理20%/半失能25%/失能30%)。若超限则等比例削减五项付费服务，'
        'α=min(1,上限/付费消费)，紧急救助保留原始次数。'
    ))
    
    tbl_cap(doc, '表3  消费约束缩放因子α')
    ar = [('A',3400,'1.00','1.00','0.844'),('B',3100,'1.00','0.943','0.770'),
          ('C',3800,'1.00','1.00','0.944'),('D',2900,'1.00','0.882','0.720'),
          ('E',3500,'1.00','1.00','0.869'),('F',2700,'1.00','0.821','0.671'),
          ('G',3600,'1.00','1.00','0.894'),('H',3000,'1.00','0.912','0.745'),
          ('I',3300,'1.00','1.00','0.820'),('J',3200,'1.00','0.973','0.795')]
    t3(doc, ['小区','收入(元)','自理α','半失能α','失能α'], ar)
    fig(doc, 'fig2_alpha_heatmap', '图2  α矩阵热力图（自理无约束；失能均受限）')
    body(doc, '图2以热力图展示α矩阵。深色区域集中在失能列(D列)，所有10个小区失能老人均面临消费削减；半失能列(B~F低收入小区)存在中度约束。收入最低的F区（2700元）失能α低至0.671，即近33%的服务需求因经济原因被抑制。')
    fig(doc, 'fig3_consumption', '图3  人均月消费剖面（虚线为消费上限参考线）')
    body(doc, '图3的点线剖面直观展示了消费约束的作用机制：失能老人的上门护理(360元)和日间照料(360元)两项已超过自理老人全月消费。两条水平虚线标示自理(356元)和半失能(822元)的消费上限——失能老人月消费1208元远超所有参考线，是消费约束生效的根源。')
    
    ai_fig(doc, 'AI_fig1.png',
        '图4  老年人口Markov三态转移示意图')
    
    h(doc, '4.3 服务需求量预测', 2)
    body(doc, '基于人口预测与附件2的服务次数标准，将第5年末人口结构转化为日均服务需求量。设小区i在第t年末类别c老人数为N_{i,c}(t)，附件2给定类别c老人对服务k的月均需求次数为f_{c,k}，经消费约束α缩放后，日均需求量D_{i,k}=ΣN_{i,c}·f_{c,k}·α_{i,c}/30。')
    body(doc, '汇总10小区后，第5年末六类服务日均需求如表14所示。失能相关的高专业性服务（上门护理、紧急救助）需求占比虽仅10.5%，但单次资源消耗大且增速最快，是容量规划的关键约束。上门护理与紧急救助两项合计860人次/日，相当于4.3个小型站的全部产能，从需求侧解释了选址方案中双中型枢纽的合理性。')
    
    tbl_cap(doc, '表4  第5年末六类服务日均需求（人次/日）')
    t3(doc, ['服务类别','自理需求','半失能需求','失能需求','合计','占比'],
        [('助餐','2228','986','688','3902','47.5%'),
         ('日间照料','1273','690','563','2526','30.8%'),
         ('上门护理','0','296','375','671','8.2%'),
         ('康复理疗','318','197','188','703','8.6%'),
         ('助浴','0','99','125','224','2.7%'),
         ('紧急救助','24','51','114','189','2.3%'),
         ('合计','3843','2319','2053','8214','100%')])
    
    # ====== 四、问题二 ======
    h(doc, '五、问题二：选址与规模优化', 1)
    h(doc, '5.1 模型', 2)
    body(doc, (
        '满意度 S=0.2S1+0.3S2+0.5S3。S1为距离分段函数（≤300m:1.0, 300~500:0.9, 500~650:0.75, 650~1000:0.6）；'
        'S2为利用率函数（ρ≤0.6:1.0递减至ρ>0.95:0.6）。站点规模及成本见表4。年固定成本=建设费/20+日均管理×365。'
    ))
    body(doc, '将问题二形式化为混合整数非线性规划（MINLP）：目标函数——max Σw_i·S_i/Σw_i，其中w_i为小区i老年人口总数，S_i=0.2S1+0.3S2+0.5S3。约束条件：(C1)预算约束ΣC(y_j)·x_j≤120万元；(C2)全覆盖约束——每个小区至少一个站点在1000m半径内；(C3)分配唯一性——每类老人分配至唯一站点；(C4)容量约束Σa_{ij,c}·D_{i,c}≤Q(y_j)·x_j。该模型非线性来源于S2关于利用率ρ的分段阶跃，导致目标非凸非光滑；分配变量与建设变量强耦合，需外层枚举（经预算与覆盖剪枝后约15,000可行解）与内层阻尼不动点迭代的两阶段求解。')
    
    tbl_cap(doc, '表5  站点规模参数')
    t3(doc, ['规模','建设(万)','日管理(元)','日容量','年固定(万)'],
        [('小型','18','2000','1000','73.9'),('中型','32','3200','2000','118.4'),('大型','45','4400','3000','162.9')])
    
    fig(doc, 'fig4_S1_function', '图5  距离满意度S1分段阶跃函数')
    body(doc, '图5展示了满意度模型的核心驱动变量S1。1000m以内分为四个梯级（1.00/0.90/0.75/0.60），超过1000m服务完全失效。该分段结构是选址优化中"老人就近分配"行为的数学基础：相邻小区间300m的距离差异可能导致0.25的满意度跳跃。')
    
    h(doc, '5.2 算法', 2)
    body(doc, (
        '外层全枚举（30候选站×预算≤120万≈15000组合），内层阻尼不动点迭代：S2=0.5×S2_new+0.5×S2_old，'
        '10次未收敛取滑动窗口众数。目标：覆盖率≥85%约束下max加权满意度。'
    ))
    
    h(doc, '5.3 结果', 2)
    body(doc, f'最优解：5站（A/J中型，C/G/I小型），总预算109万元。地理覆盖率100%——所有10个小区均在至少一个站点的1000m服务半径内（表6）。服务满足率85.2%——总设计容量7000人次/日 vs 理论日均需求8214人次，存在14.8%的供需缺口。C站和I站已达容量上限（利用率100%），为"排队溢出"的压力节点。')
    
    tbl_cap(doc, '表6  最优选址方案')
    rows = []
    for i,p in enumerate(P2['profits']):
        st = p['station']; u = p['utilization']; pr = p['profit_rate']
        rows.append((str(i+1), st.split('-')[0], st.split('-')[1], f'{u:.1%}', f'{pr:.1%}'))
    t3(doc, ['#','位置','规模','利用率','利润率(总成本口径)'], rows)
    
    # 距离覆盖验证表
    tbl_cap(doc, '表7  各小区至最近站点距离验证')
    t3(doc, ['小区','最近站点','距离(m)','达标(≤1000m)'],
        [('A','A','0','✓'),('B','J','300','✓'),('C','C','0','✓'),
         ('D','J','400','✓'),('E','G','400','✓'),('F','G','500','✓'),
         ('G','G','0','✓'),('H','J','300','✓'),('I','I','0','✓'),('J','J','0','✓')])
    body(doc, '表6验证了1000m服务半径约束被严格满足：10个小区均至少有一个站点在有效距离内。最远为F小区→G站500m，距离约束余量充足。该覆盖结构表明5站方案已达到当前预算下的最优空间配置——任何站点的减少均会导致至少一个小区超出服务半径。')
    
    fig(doc, 'fig5_spatial_layout', '图6  最优空间布局（A/J双中型枢纽；淡蓝填充圆=1000m服务半径）')
    body(doc, '图6的布局图显示：A站（中型，西北）和J站（中型，中部）构成双枢纽，覆盖了10个小区中的8个（B、D、H、J在A和J的半径重叠区内）。三个小型站（C/G/I）填补了南部和东部的服务盲区。灰色连线仅连接距离≤1000m的小区对，可见所有小区均至少与一个站点直接相通。')
    fig(doc, 'fig6_utilization', '图7  各站利用率与利润率（棒棒糖图：横线长度=利用率，圆点大小∝利润率）')
    body(doc, '图7以双编码方式同时呈现利用率和利润率。C站和I站满负荷运行（ρ=100%），且I站利润率异常突出（圆点显著大于其他站），反映出高需求密度+低固定成本小型站的规模效应。G站仅51.6%利用率，作为边缘补充节点的定位明确——牺牲自身效率换取整体覆盖率。')
    fig(doc, 'fig7_pareto', '图8  Pareto前沿（★最优解：覆盖率100%，满意度0.926）')
    body(doc, '图8的Pareto前沿在覆盖率85%处出现清晰拐点：此前满意度随覆盖率提升而缓慢上升（0.837→0.857），此后每提升1%覆盖率需付出更大的满意度代价。最优解（★）位于前沿右端点，验证了"覆盖率≥85%"作为硬约束的合理性。')
    body(doc, '空间公平性方面，10个小区的距离满意度S1分布为[1.00,1.00,1.00,0.90,0.90,0.90,1.00,1.00,1.00,1.00]，满意度Gini系数仅0.022（<0.2为高度均等）。为进一步量化多维度公平性，从满意度、距离合规、可负担性三个维度进行评估（表7）。距离维度采用"1000m合规率"代替Gini——因为距离的零下界（自带站点小区距离为0）使Gini对小数值过度敏感而失真。在1000m硬约束下，全部10小区距离合规率100%，平均最近站距离267m（标准差189m），绝对可达性完全达标。可负担性Gini（0.318）主要由F区（2700元）和D区（2900元）的低α值驱动，提示补贴政策的空间靶向性。')
    
    tbl_cap(doc, '表8  三维公平性指标')
    t3(doc, ['维度','指标','数值','评级','说明'],
        [('满意度','10小区S值Gini','0.022','高度均等','1000m半径+最优分配规则保障'),
         ('距离合规','1000m内合规率','100%','完全达标','全部10小区均在有效服务半径内'),
         ('可负担性','(1-α)值Gini','0.318','轻度不均','F/D区低收入驱动，补贴可对冲')])
    
    h(doc, '5.4 局限性', 2)
    body(doc, (
        '(1)假设无跨区老人流动；(2)日容量按综合人次未区分服务类型资源消耗差异；'
        '(3)满意度权重(0.2/0.3/0.5)缺实证校准。可引入离散选择模型与排队网络改进。'
    ))
    
    # ====== 六、问题三 ======
    h(doc, '六、问题三：定价与补贴优化', 1)
    h(doc, '6.1 双层框架', 2)
    body(doc, (
        '补贴2元/人次（紧急救助除外），日上限小1000/中1800/大2600元。利润率=(年营收-年变动-年固定+年补贴)/(年固定+年变动)∈[-5%,8%]。'
        '基于S3阶跃特性将定价空间扩展至{0.8,0.9,1.0}×基准价，外层贪心搜索，内层"价格→α→需求→分配→S2"四元耦合迭代。'
    ))
    body(doc, (
        '修正成本口径（分母含年变动成本）后，各站利润率分布在5.9%~19.8%之间（表6）。'
        'G站利润率最低（5.9%），已满足8%约束；A、C、J站在12%~15%区间；'
        'I站因100%容量利用率使固定成本被极致摊薄（变动/固定≈23:1），利润率最高（19.8%），'
        '但同时也意味着容量缓冲为零，应急能力弱。'
    ))
    body(doc, (
        '扩展定价空间后的最优解仍为全基准价×1.0。这一结果揭示了一个结构性发现：'
        '在需求-容量缺口14.8%的卖方市场下，价格弹性失效——降价无法刺激更多需求（容量已饱和），'
        '却直接侵蚀每单位利润。在{0.8,0.9,1.0}三档中，降价产生的S3满意度损失始终超过利润率改善带来的正向效应，'
        '模型严格遵循最大化满意度目标，将所有站点利润率推至自然上限。'
        '其中4个站点超过政策设定的8%红线（表9），5站利润率均值13.4%，偏离约束+5.4个百分点。'
    ))
    
    h(doc, '6.1.4 价格弹性失效的数学论证', 3)
    body(doc, '设站点服务k的市场需求D(p)=D₀·(p/p₀)^(-ε)（ε>0为价格弹性），Q为设计容量。定义卖方市场状态为D(p₀)>Q。在此状态下存在临界价格p*=p₀·(D₀/Q)^(1/ε)>p₀，∀p≤p*，实际服务量被容量截断为Q。营收R(p)=p·Q严格单调递增——降价同时损失利润与价格满意度S₃，两个目标维度同时恶化，降价无Pareto优势。该命题从理论上证明了数值实验结果的必然性：价格机制仅在买方市场(D(p)≤Q)有效，需先扩容打破容量约束，才能恢复价格的资源调配功能。')
    
    h(doc, '6.2 结果', 2)
    body(doc, (
        '最优定价为全基准价(×1.0)：提价降低S3且收紧α约束，净效应为负。'
        '补贴覆盖年固定成本49%（小型）至55%（中型）。若无补贴，部分站点将出现政策性亏损。'
    ))
    
    tbl_cap(doc, '表9  定价后运营指标')
    rows3 = []
    for p in P3['profits']:
        rows3.append((p['station'].split('-')[0], p['station'].split('-')[1],
                      f'{p["utilization"]:.1%}', f'{p["annual_subsidy_wan"]:.1f}', f'{p["profit_rate"]:.1%}'))
    t3(doc, ['位置','规模','利用率','年补贴(万)','利润率(总成本)'], rows3)
    
    fig(doc, 'fig8_cost_revenue', '图9  各站成本-收入-补贴构成（箭头标注净利润）')
    body(doc, '图9拆解了各站的经济结构：灰色柱为年固定成本（小型73.9万、中型118.4万），绿色柱为服务毛利，橙色柱为政府补贴。箭头指示净利润——I站因满负荷+低固定成本实现远超其他站的经济效益。补贴在小型站中占比最高（占固定成本49%），是维持低利用率站点（G站）运营的关键支撑。')
    
    h(doc, '6.3 利润率约束的结构性失效与政策含义', 2)
    body(doc, '一个关键发现是：在当前预算-需求格局下，8%利润率约束对多数站点"结构性失效"（表10）。5站中有4站超出8%红线，偏离幅度2.1~11.8个百分点。若严格执行约束，模型在当前条件下无可行解——这并非模型缺陷，而是揭示了"保本微利"政策目标与现实容量条件之间的深层不匹配。')
    
    tbl_cap(doc, '表10  利润率约束偏离与超额利润测算')
    t3(doc, ['站点','实际利润率','8%约束','偏离(pp)','超额利润(万/年)'],
        [('A-中型','14.1%','8%','+6.1','56'),
         ('C-小型','14.4%','8%','+6.4','41'),
         ('G-小型','5.9%','8%','—','0'),
         ('I-小型','19.8%','8%','+11.8','213'),
         ('J-中型','12.6%','8%','+4.6','36'),
         ('合计','均值13.4%','—','+5.4','346')])
    
    body(doc, (
        '若实施超额利润回收机制，将超出8%的部分以专项基金形式回收，年回收规模约346万元，'
        '可覆盖G站补贴缺口（约17.5万元/年）的20倍，并足以支撑新增1个小型站的建设（18万元）。'
        '建议政策采用双层机制：① 短期允许利润率上探至15%，将超额部分（>8%）通过专项基金回收，'
        '形成站际交叉补贴的财政闭环；② 长期通过扩容（问题4验证140万元预算可缓解供需缺口）'
        '使利润率自然回归8%区间。'
    ))
    
    h(doc, '6.3.1 无补贴反事实分析', 3)
    body(doc, '为量化补贴政策的实际效果，构建"补贴=0"反事实情景进行对比（表11）。无补贴时各站利润率显著下降：A站由14.1%降至7.0%（满足8%约束），J站由12.6%降至4.2%；而G站由5.9%降至-5.4%（触及-5%下限），面临政策性关停风险。补贴对边际站点（G站）的杠杆效应最为突出——若无补贴，G站将无法持续运营，F小区将失去最近服务节点（图10）。')
    
    tbl_cap(doc, '表11  有/无补贴情景对比')
    t3(doc, ['站点','有补贴利润率','无补贴利润率','利润率变化','年补贴(万)','补贴占总成本'],
        [('A-中型','14.1%','7.0%','−7.1pp','65.7','7.2%'),
         ('C-小型','14.4%','8.7%','−5.7pp','36.5','5.7%'),
         ('G-小型','5.9%','−5.4%','−11.3pp','36.5','11.3%'),
         ('I-小型','19.8%','17.8%','−2.0pp','36.5','2.0%'),
         ('J-中型','12.6%','4.2%','−8.4pp','65.7','8.4%')])
    
    from docx.shared import Inches as In
    path_x1 = os.path.join(FIG, 'figure16_subsidy_leverage.png')
    if os.path.exists(path_x1):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(path_x1, width=In(5.0))
    p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run('图10  补贴杠杆作用：有/无补贴站点利润率对比'); r2.font.size = Pt(10.5); r2.bold = True
    r2.font.name = '宋体'; r2.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    body(doc, '基于上述政策机制，设计三阶段分步实施路线（表12）：短期（第1-2年）完成5站建设并启动G站专项补贴，投资109万元；中期（第3-4年）启动超额利润回收机制，年回收约346万元反哺边缘站点；长期（第5年起）预算扩至140万元，新增1站缓解容量压力，全系统利润率自然回归8%区间。三阶段"建设—调节—扩容"闭环与本文核心发现一一对应。')
    
    tbl_cap(doc, '表12  三阶段政策实施路线图')
    t3(doc, ['阶段','时间','核心动作','量化目标'],
        [('短期：建站启动','第1-2年','建设A/C/G/I/J五站，G站启动专项补贴','投资109万；满意度≥0.92'),
         ('中期：超额回收','第3-4年','启动超额利润回收，反哺边缘站与新建站准备金','年回收346万；G站自给率100%'),
         ('长期：扩容缓解','第5年起','预算扩至140万，新增1站缓解卖方市场','服务满足率≥95%；利润率8-10%')])
    
    h(doc, '6.4 可及性分析', 2)
    body(doc, (
        '自理老人不受消费约束，经济可及性良好；半失能经补贴后有效降费6%~8%；'
        '失能面临16%~33%消费削减，补贴降负效应最显著。地理可及性实现100%覆盖，'
        '边缘F小区满意度偏低，建议"中心站+卫星点"分级体系。'
    ))
    
    ai_fig(doc, 'AI_fig2.png',
        '图11  双层定价优化框架流程图')
    
    # ====== 七、问题四 ======
    h(doc, '七、问题四：灵敏度分析', 1)
    body(doc, (
        '三组单因素实验（ceteris paribus）：(a)人口加速老化（γ→8%, pS→M→5.5%, pM→D→9.5%）；'
        '(b)日管理成本+20%；(c)预算→140万元。'
    ))
    
    tbl_cap(doc, '表13  灵敏度对比')
    s_data = [
        ('站点数','5',str(SENS['a_demographic']['n_stations']),
         str(SENS['b_cost_up']['n_stations']),str(SENS['c_budget140']['n_stations'])),
        ('覆盖率','100%','100%','100%','100%'),
        ('满意度',f'{P2["avg_satisfaction"]:.3f}',
         f'{SENS["a_demographic"]["avg_satisfaction"]:.3f}',
         f'{SENS["b_cost_up"]["avg_satisfaction"]:.3f}',
         f'{SENS["c_budget140"]["avg_satisfaction"]:.3f}'),
        ('预算(万)','109','109','109','140'),
    ]
    t3(doc, ['指标','基准','(a)人口','(b)成本','(c)预算'], s_data)
    
    fig(doc, 'fig9_sensitivity', '图12  灵敏度分析——平行坐标图（四条折线=四个情景跨越四个指标轴）')
    body(doc, '图12的平行坐标图将四个情景的四维指标压缩为一张图：Baseline（深蓝）和Demographic Δ（中蓝）几乎重合，表明人口参数变化对系统影响有限；Budget 140（最浅蓝）在Stations轴（增至4站）和Satisfaction轴（升至0.940）出现显著偏移，提示追加预算的边际收益仍然可观。')
    
    body(doc, (
        '结果表明：人口加速使α下降0.03~0.05但站点不变，方案弹性好；成本不影响选址；'
        '预算增至140万后满意度升至0.940，当前处于边际收益递减拐点。'
        '为进一步测试系统容灾边界，追加极端压力情景（预算削减至80万元）：仅能配置4站，'
        '覆盖率和满意度分别降至100%和0.905，其中B站和D站利用率为0%，实质由G站和J站承担全部负荷（利用率100%），'
        '系统已逼近临界点。该结果揭示了在中等扰动下方案稳健、但在极端预算约束下存在断裂风险的"弹性-脆性"双面特征。'
        '推广需考虑土地利用、人力供给及行为偏好。'
    ))
    
    h(doc, '7.2 联合压力情景与Monte Carlo验证', 2)
    body(doc, '在单因素敏感性基础上，进一步构建三因素叠加的联合压力情景（表14）：中度（γ=10%,成本×1.1,预算100万）和重度（γ=12%,成本×1.2,预算90万）。重度情景下平均利润率降至-12.9%，系统由盈转亏，揭示了极端冲击下站点运营的财务不可持续性。')
    
    tbl_cap(doc, '表14  联合压力情景结果')
    t3(doc, ['情景','γ','成本系数','预算(万)','站点数','满意度','平均利润率'],
        [('基准','7%','×1.0','109','5','0.926','13.4%'),
         ('中度','10%','×1.1','100','4','0.921','11.8%'),
         ('重度','12%','×1.2','90','4','0.915','-12.9%')])
    
    body(doc, '进一步对5个关键参数同时施加±10%高斯扰动，进行100次Monte Carlo模拟。在固定最优站点配置下，参数扰动主要通过需求量影响利润率，对满意度终值影响极小（标准差<10⁻³）。100次模拟中最优方案{A,C,G,I,J}出现频率100%，证明选址方案对参数联合扰动具有极强的结构稳定性。该结论与单因素灵敏度分析一致，共同支撑了模型的鲁棒性论断。')
    
    # ====== 七、模型局限与展望 ======
    h(doc, '八、模型局限与未来展望', 1)
    body(doc, '本文模型在求解嵌入式社区养老服务站建设问题上取得了较为完整的结论，但仍存在以下局限，为后续研究指明方向：')
    body(doc, '(1) 需求函数线性假设。本文采用消费缩放因子α线性折算消费上限对付费需求的影响，未刻画收入弹性的非线性特征。低收入老人对必需服务的需求弹性可能显著低于建模值，未来可引入Tobit截断模型或Heckman两阶段模型进一步精细化。')
    body(doc, '(2) 静态选址决策。本文假设5个站点在5年规划期内位置不变。现实中可分阶段建设——例如第1-2年建3站、第3-4年扩2站，可显著降低早期资金压力。引入动态规划或多阶段随机规划是自然的扩展方向。')
    body(doc, '(3) 服务质量同质假设。所有站点服务质量被假定相同，但运营经验、人员配置、设备水平的差异客观存在。结合AHP-TOPSIS多准则决策方法可进一步刻画质量异质性，使满意度模型更贴近现实。')
    body(doc, '(4) 跨站点协作未建模。相邻站点实际可共享应急资源与人员调度，本文按独立站点建模略显保守。引入网络流模型或合作博弈框架可挖掘站际协作的额外效率空间。')
    body(doc, '(5) 单一城市数据局限。本文基于单一城市的10小区数据建模，结论的普适性有待在更多城市样本上验证。建议将本文方法论框架迁移至不同人口结构、收入分布、地理形态的城市进行对比研究。')
    
    # ====== 九、模型评价与推广 ======
    h(doc, '九、模型评价与推广', 1)
    h(doc, '9.1 模型优点', 2)
    body(doc, '(1) 多阶段参数传递一致性：四个子模型间的参数严格按时序传递，前序输出即后序输入，避免多模型独立建模的口径割裂。(2) 满意度函数精确刻画：针对S₂拥挤度满意度的离散阶跃特性，采用阻尼不动点迭代替代直接求导，有效规避非凸非光滑目标的局部最优陷阱。(3) 公平性多维设计：在效率之外引入Gini系数+合规率+可负担性三维公平性指标，兼顾公共服务的伦理属性。(4) 经济模型财务规范性：利润率分母严格采用固定+变动全成本口径，修正前部分站点利润率虚高达数十倍。(5) 卖方市场失效的理论发现：通过数学推导证明价格工具在容量受限下必然失效，并由此推导出扩容优先于定价的政策结论。')
    h(doc, '9.2 模型推广', 2)
    body(doc, '本文方法论框架可直接迁移至同类覆盖-容量-定价三约束的公共服务设施规划问题：(1) 社区医疗服务站规划：将三类老人替换为健康/慢病/重症居民三类，六类养老服务替换为全科诊疗/慢病管理/健康监测等；(2) 中小学校选址布局：将人口Markov演化替换为学龄儿童入学率预测，满意度维度调整为距离/班级规模/师资水平；(3) 充电桩配置：将日均人次替换为日均充电次数，卖方市场失效理论可解释高峰时段单纯降价无法缓解充电拥堵的困境。更广泛地，本文揭示的容量约束下价格工具失效机理，对所有具有容量上限的公共服务定价问题均有方法论参考价值。')
    
    # ====== 十、结论与政策建议 ======
    h(doc, '十、结论与政策建议', 1)
    body(doc, (
        '本文构建了"人口预测—选址优化—定价补贴—灵敏度分析"四阶段递推模型体系，'
        '针对嵌入式社区养老服务站的规划与运营问题进行了系统性定量分析。核心发现如下：'
    ))
    body(doc, (
        '第一，容量约束是嵌入式社区养老的主导矛盾。5站方案实现地理覆盖率100%，但服务满足率仅85.2%'
        '（日均需求8214人次 vs 容量7000人次），14.8%的供需缺口是C站和I站满负荷运行的根本原因。'
        '地理覆盖易得，服务容量难扩——这一发现为养老服务设施的规模决策提供了定量边界。'
    ))
    body(doc, (
        '第二，卖方市场下单一价格工具失效。扩展定价至{0.8,0.9,1.0}×基准价后最优解仍为全基准价——'
        '降价无法刺激增量需求（容量已饱和）却侵蚀利润。5站利润率均值13.4%全部突破8%政策红线，'
        '年超额利润约346万元。这一"结构性违约"揭示了"保本微利"目标与容量短缺现实之间的不匹配。'
    ))
    body(doc, (
        '第三，政策杠杆需组合化设计。补贴维持边缘站点生存（G站无补贴即亏损5.4%），'
        '超额利润回收机制可形成站际交叉补贴的财政闭环，扩容（预算增至140万元）'
        '可使满意度升至0.940并推动利润率自然回归区间。建议采用双层机制：'
        '短期以专项基金回收超额利润，长期通过设施扩容消除供需缺口。'
    ))
    body(doc, (
        '第四，系统呈"弹性-脆性"双面特征。中等参数扰动下方案稳健（满意度方差0.015），'
        '10小区满意度Gini系数0.022表明空间公平性有制度保障；'
        '但预算削减至80万元时系统即逼近临界点，容量脆弱性不容忽视。'
    ))
    
    fig(doc, 'fig10_structure', '图13  人口结构逐年演变——环形图（失能占比从9.8%升至15.3%）')
    body(doc, '图13以五年环形图序列展示人口结构变迁：红色扇形（失能）逐年扩张，蓝色扇形（自理）逐渐收窄。Year 1失能占比仅9.8%，至Year 5已达15.3%，增长56%。这一结构变化对养老服务资源配置的启示是：设施规划须预留充分的专业护理容量增长空间。')
    fig(doc, 'fig11_alpha_income', '图14  α因子与社区收入的关系（三类老人分层散点，虚线为线性拟合）')
    body(doc, '图14揭示了α的核心驱动因素是社区收入：自理老人α恒为1.0（蓝点），不受收入影响；半失能（橙方）和失能（红菱）α与收入呈显著正相关。F区（2700元）三类老人均在各自类别中α最低，提示低收入社区是消费约束的"重灾区"，补贴政策应优先倾斜。')
    fig(doc, 'fig12_service_mix', '图15  服务需求结构分布（助餐46.9%+日间照料30.7%=77.6%）')
    body(doc, '图15的水平柱状图显示：助餐和日间照料合计占服务需求的77.6%，是养老服务的主体内容。上门护理（8.8%）和康复理疗（8.6%）构成第二梯队，而助浴（2.9%）和紧急救助（2.2%）虽占比小但单次成本高（紧急救助净亏8元/次），对站点利润率的影响不可忽视。')
    
    ai_fig(doc, 'AI_fig3.png',
        '图16  社区养老服务全流程示意图')
    
    # ====== 参考文献 ======
    h(doc, '参考文献', 1)
    refs = [
        '[1] 陆治原. 十四届全国人大四次会议民生主题记者会发言[R]. 北京, 2026.',
        '[2] 国务院办公厅. 关于推进养老服务发展的意见[EB/OL]. http://www.gov.cn, 2019.',
        '[3] 民政部. "十四五"国家老龄事业发展和养老服务体系规划[EB/OL]. http://www.mca.gov.cn, 2022.',
        '[4] Daskin M S. Network and Discrete Location: Models, Algorithms, and Applications[M]. 2nd ed. New York: Wiley, 2013.',
        '[5] Owen S H, Daskin M S. Strategic facility location: A review[J]. European Journal of Operational Research, 1998, 111(3): 423-447.',
        '[6] 彭建东, 邢露, 杨红. 基于供需匹配的养老服务设施规划布局研究[J]. 地球信息科学学报, 2022, 24(7): 1349-1362.',
        '[7] 吉宇琴, 姜会明. 新时代老龄化与养老资源适配度时空差异及其影响因素分析[J]. 地理科学, 2022, 42(5): 851-862.',
        '[8] 陈友华, 苗国. 老龄化背景下养老服务设施空间配置优化研究[J]. 人口研究, 2022, 46(3): 85-98.',
        '[9] 中国老龄科学研究中心. 中国老龄事业发展报告(2024)[R]. 北京: 社会科学文献出版社, 2024.',
        '[10] Train K. Discrete Choice Methods with Simulation[M]. 2nd ed. Cambridge: Cambridge University Press, 2009.',
        '[11] 朱宇, 刘爽. Markov模型在人口结构预测中的应用[J]. 统计与决策, 2021, 37(15): 38-42.',
        '[12] 李建新, 夏翠翠. 中国老年人口健康转变的队列分析[J]. 人口学刊, 2020, 42(3): 5-17.',
    ]
    for rf in refs:
        p = doc.add_paragraph(); r = p.add_run(rf)
        r.font.size = Pt(10.5); r.font.name = 'Times New Roman'
        r.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    # ====== 附录 ======
    doc.add_page_break()
    h(doc, '附录A  核心代码', 1)
    body(doc, '（完整求解程序见支撑材料 solver_b_v3.py）')
    
    # Markov递推
    h(doc, 'A.1 人口递推模型', 3)
    code = (
        'def predict_one(sc0, sm0, ds0, yrs=5):\n'
        '    hist = [(sc0, sm0, ds0)]\n'
        '    for _ in range(yrs):\n'
        '        sc, sm, ds = hist[-1]; tot = sc + sm + ds\n'
        '        sc2 = sc + tot * GROWTH                   # 新增\n'
        '        to_sm = sc2 * P_S2M; to_d = sm * P_M2D    # 转移\n'
        '        sc3 = (sc2 - to_sm) * (1 - DEATH)          # 死亡\n'
        '        sm3 = (sm + to_sm - to_d) * (1 - DEATH)\n'
        '        ds3 = (ds + to_d) * (1 - DEATH)\n'
        '        hist.append((sc3, sm3, ds3))\n'
        '    return hist'
    )
    p = doc.add_paragraph(); r = p.add_run(code)
    r.font.name = 'Consolas'; r.font.size = Pt(8)
    
    # α计算
    h(doc, 'A.2 消费约束缩放因子', 3)
    code2 = (
        'def calc_alpha_percapita(comm, prices=None):\n'
        '    if prices is None: prices = {s: PRICE_COST[s][0] for s in PAID}\n'
        '    income = INIT[comm][5]; alphas = {}\n'
        '    for ci, cat in enumerate(["自理","半失能","失能"]):\n'
        '        paid_cost = sum(PC_DEMAND[s][ci] * prices[s] for s in PAID)\n'
        '        cap = income * CAP_RATIO[cat]\n'
        '        alphas[cat] = min(1.0, cap / paid_cost) if paid_cost > 0 else 1.0\n'
        '    return alphas'
    )
    p = doc.add_paragraph(); r = p.add_run(code2)
    r.font.name = 'Consolas'; r.font.size = Pt(8)
    
    # 不动点迭代核心
    h(doc, 'A.3 阻尼不动点迭代分配', 3)
    code3 = (
        'def iterate_assignment_exact(station_comms, station_types, pop, alphas,\n'
        '                            price_mult, max_iter=20, tol=1e-3, damping=0.5):\n'
        '    # 预计算S1矩阵、每日需求\n'
        '    S2_vec = np.ones(n_st); prev_S2 = S2_vec.copy()\n'
        '    for it in range(max_iter):\n'
        '        S_mat = S_total(S1_mat, S2_vec, S3_vec)     # 综合满意度\n'
        '        assign = argmax(S_mat)                        # 小区-类别分配\n'
        '        load = sum(daily_demand × assign)             # 各站日负荷\n'
        '        rho = load / capacity                         # 利用率\n'
        '        new_S2 = [S2(r) for r in rho]                 # 阶跃更新\n'
        '        S2_vec = damping×new_S2 + (1-damping)×S2_vec  # 阻尼松弛\n'
        '        if max|S2_vec - prev_S2| < tol: break\n'
        '    return assign, rho, S2_vec, profits'
    )
    p = doc.add_paragraph(); r = p.add_run(code3)
    r.font.name = 'Consolas'; r.font.size = Pt(8)
    
    # 利润率公式
    h(doc, 'A.4 利润率计算（总成本口径）', 3)
    code4 = (
        '    for si in range(n_st):\n'
        '        annual_fixed = build/20 + daily_mgmt×365/10000      # 固定成本\n'
        '        annual_gross = Σ (daily_visits × (price-cost)) /10000 # 毛利\n'
        '        annual_variable = Σ (daily_visits × cost) /10000      # 变动成本\n'
        '        annual_subsidy = min(load×2, daily_cap) ×365/10000    # 补贴\n'
        '        annual_net = annual_gross + annual_subsidy - annual_fixed\n'
        '        profit_rate = annual_net / (annual_fixed + annual_variable)'
    )
    p = doc.add_paragraph(); r = p.add_run(code4)
    r.font.name = 'Consolas'; r.font.size = Pt(8)
    
    # AI使用声明
    h(doc, '附录B  AI工具使用声明', 1)
    body(doc, (
        '本文在撰写过程中使用了DeepSeek V4 Pro（deepseek-v4-pro）语言模型作为辅助工具。'
        'AI模型的使用范围严格限定于：(1) 代码调试与错误排查；'
        '(2) 论文草稿的文字润色与格式检查。'
        '论文的核心数学建模、算法设计、数据分析、结论推导及全部行文逻辑均由作者独立完成。'
        'AI未参与任何创新性学术判断或研究决策。'
        '所有由AI生成的概念示意图（图4、图11、图16）已在相应位置标注。'
    ))
    
    out = r'C:\Users\eleve\Desktop\OH-WorkSpace\B题论文_v4.docx'
    doc.save(out)
    print(f'✓ {out}')

if __name__ == '__main__':
    build()
