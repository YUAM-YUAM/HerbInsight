"""Read-only Wujisan case companions beside the relevant teaching steps.

Existing processed tables are evidence of saved results, not evidence that a
particular external tool, threshold or database version was used.
"""
from pathlib import Path
import hashlib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'projects/wujisan_uc'

# Explicit step links avoid showing a second, unrelated course below the lesson.
STEP_CASES = {
    ('collection', 0): 'herbs', ('collection', 3): 'targets', ('collection', 5): 'mapping',
    ('disease', 1): 'disease', ('disease', 4): 'overlap',
    ('ppi', 3): 'edges', ('ppi', 5): 'topology',
    ('enrichment', 5): 'enrichment',
    ('transcriptome', 5): 'expression', ('ml', 4): 'ml',
}

CASES = {
 'herbs': ('从药材清单开始', 'processed/herbs.csv',
    '先确认处方组成和药材身份，再收集成分与靶点。',
    '本案例使用SymMap（研究者已确认）。逐味核对药材详情与条目ID，保存靶点关联导出；处方出处和剂量另从处方资料确认。具体字段见本页SymMap操作单，不另填一套通用表。',
    '本表一行是一味药材；source_file对应原始导出。来源已由研究者确认是SymMap，不再把来源列为未知。species=Homo sapiens为导入脚本统一填写的靶点研究设定，不是药材基原或逐条物种审核结果。',
    '已知来源为SymMap；尚需补齐药材详情ID/URL、实际检索日期、版本与处方出处。没有保存的记录留空并说明，不能猜填。',
    '本站对应：用本课药材登记模板补齐出处，再整理下游关系表。'),
 'targets': ('候选靶点不等于已证实靶点', 'processed/compound_targets.csv',
    '把各药材候选关系整理成可追溯的靶点明细。',
    '本案例来源为SymMap（研究者已确认）：逐味保存靶点关联表，保留Target id、Gene symbol、UniProt id、Relationship及统计字段，再添加药材名与来源信息。',
    '当前表包含herb_name、gene_symbol、uniprot_id、relationship和评分；同一基因可来自多味药，不应把证据行数当作独立靶点数。文件名含compound，但表中没有独立compound_id，不能声称已还原每个成分—靶点关系。',
    '已知来源为SymMap；评分的具体定义/版本和原筛选标准仍需回查文档与记录。不把p_value直接当作本研究的表达差异P值。',
    '本站对应：先完成来源审核和ID统一，再抽出基因集合；成分网络还需要补齐成分标识。'),
 'mapping': ('UniProt字段与映射审核不是一回事', 'processed/compound_targets.csv',
    '核对已有UniProt与基因符号，避免重复或错误映射。',
    '传统操作对照：将原始ID分批提交UniProt，保存From/To、物种、失败和一对多记录后回填。',
    '这里能看到uniprot_id与gene_symbol并列，但仅凭并列字段不能证明已经执行了完整映射质控。',
    '原始ID映射导出、查询日期、一对多处理与失败清单待补；不能将非空字段等同于审核通过。',
    '本站对应：按照本节mapping模板补全审核记录；当前平台不自动完成生物学ID映射。'),
 'disease': ('UC疾病关联证据怎样读', 'processed/disease_genes.csv',
    '收集与溃疡性结肠炎相关的基因，并保留疾病定义与来源。',
    '传统操作对照：GeneCards等来源分别检索、保留原始关联分数及链接，按预定标准筛选。',
    '本表source标记GeneCards，包含relevance_score和source_link。分数表示来源中的关联评分，不是患病概率或治疗效果。',
    '查询日期、精确疾病检索式、评分阈值与筛前数量未由此表证明；不能把目前最低分倒推成原始筛选阈值。',
    '本站对应：在来源登记表补充筛选依据，再粘贴审核后的清单求交集。'),
 'overlap': ('共同靶点从哪里来', 'processed/target_overlap.csv',
    '找出药物候选靶点与UC关联基因共有的符号。',
    '传统操作对照：统一物种与ID后，Excel匹配或R/Python集合求交；保存两侧输入及去重规则。',
    '导入脚本prepare_day1_data.py从原始“网药重要基因.csv”读取并去重生成此表，而不是当场对两侧表求交。因此此处是已保存的候选清单，不是直接交集已被复现的证明。下方重新核对现有两侧表；若不同应追查原来的筛选输入，而不是覆盖结果。',
    '原始纳入规则未完全归档；当前两侧表未必就是原分析最后使用的筛选集合。',
    '本站对应：本课双清单计算器执行相同的字符串交集；只有输入与去重规则相同才应得到相同集合。'),
 'edges': ('STRING边表：证据比图片更重要', 'processed/ppi_edges.csv',
    '用可追溯的边表构建候选靶点网络。',
    '传统操作对照：STRING核查物种、网络类型与参数，导出TSV，再导入Cytoscape。这里只展示已有归档，不声称已恢复原操作会话。',
    'source/target是端点，score是分数；表中还保留实验、数据库、文本挖掘等通道。存在一条边不意味着直接物理结合。',
    'STRING版本、查询日期、functional/physical选项、邻居数及原筛选阈值待补。保存分数的最小值不能证明检索阈值。',
    '本站对应：第7步上传同一边表，指定source、target、score并确认0–1尺度；若超出教学计算限额，不截断后声称完整复现。'),
 'topology': ('怎样解读网络中的大节点', 'processed/ppi_nodes.csv',
    '用节点拓扑描述网络位置，不把中心节点直接叫作有效治疗靶点。',
    '传统操作对照：Cytoscape Analyzer导出节点属性，再把Degree映射为节点大小。原Cytoscape版本、会话和算法设置需另行核实。',
    'degree是连接数，betweenness反映最短路径经过情况。仓库prepare_ppi_data.py记录了无向图、加入输入基因保留孤立点、无权归一化介数及closeness计算；因此当前表不能未经核实称为原Cytoscape直接导出。按degree排序只用于读表示例，不代表原核心基因筛选规则。',
    '原Cytoscape会话和设置仍待补。本站仅从边表构图时可能缺少孤立点；即使同样无权，节点集合不同也会改变归一化中心性。',
    '本站对应：网络计算采用其页面声明的算法。先统一图和定义，再比较节点指标，不比较图形布局是否相同。'),
 'enrichment': ('从富集条目读出什么，不能读出什么', 'results/go_enrichment.csv',
    '解释候选基因在功能条目中的集中程度。',
    '传统操作对照：在R或合规在线工具输入目标、背景与完整注释，保存方法和软件版本。现有结果字段不足以确认原来用了哪个软件。',
    '示例首行response to lipopolysaccharide：gene_ratio_text=52/191表示该结果口径下191个目标中52个命中；background_ratio=357/18805是背景比例。它不表示52个基因已被五积散调控，也不证明治疗UC。',
    '完整背景基因清单、注释版本、全部受检条目和原始脚本待补。不得用显著结果里的gene_list反建注释，再宣称复现原富集P值。',
    '本站对应：第6步ORA需要目标、背景、完整注释。缺少这些输入时只做结果解读，不承诺与原结果数值相同。'),
 'expression': ('疾病表达证据如何接回候选靶点', 'results/transcriptome_summary.csv',
    '检查候选靶点与疾病表达变化是否有交集，而不是证明复方干预有效。',
    '传统操作对照：按研究设计准备表达、分组和注释，使用适合设计的方法并保留全量检验结果；仅凭logFC/adj.P.Val列名不能认定具体算法。',
    '原案例汇总记录GSE38713、13例对照和15例UC、3958个显著基因、73个网络支持差异基因，阈值FDR<0.05且|logFC|>0.58。这些是已有结果记录，不是本面板重新计算。',
    '原分析脚本、探针汇总规则和完整参数待核对。近期公开数据复核使用不同注释处理与Welch方法，不能拿显著基因数量直接判定原案例对错。',
    '本站对应：第5步支持限定设计的Welch。页面顶部的GSE38713论文对照是另一项明确记录方法的再分析，不能冒充五积散的药效验证。'),
 'ml': ('高AUC也要审查：把风险当作教学内容', 'results/ml_auc.csv',
    '区分模型排序表现与临床有效性，检查数据隔离和阈值。',
    '传统操作对照：先按患者划分，训练内预处理和筛选，锁定模型后测试，保存逐样本预测和阈值。',
    '已有表中部分模型AUC为1；这是归档的性能值，不代表已确认无泄漏或可临床应用。原项目质量提示也指出完美AUC和部分阈值表现风险。',
    '患者划分、全数据是否预筛基因、调参与外部队列隔离需要原脚本和预测记录核验；不能仅凭External标签就认证独立验证。',
    '本站对应：可训练逻辑回归与随机森林，学习型处理放入训练折；并不复现所有原模型或自动提供外部验证。'),
}


def case_table(key):
    path = CASE / CASES[key][1]
    return pd.read_csv(path), hashlib.sha256(path.read_bytes()).hexdigest()


def overlap_audit():
    def genes(filename):
        return set(pd.read_csv(CASE / filename).gene_symbol.dropna().astype(str).str.strip()) - {''}
    calculated = genes('processed/compound_targets.csv') & genes('processed/disease_genes.csv')
    saved = genes('processed/target_overlap.csv')
    return {'current_table_intersection': len(calculated), 'saved_overlap': len(saved),
            'only_in_current_intersection': len(calculated-saved), 'only_in_saved_overlap': len(saved-calculated)}


def companion_markdown(key, digest, rows):
    title, path, question, traditional, interpretation, missing, platform = CASES[key]
    return '\n\n'.join(['# 五积散案例 · '+title, '固定教学案例：五积散—溃疡性结肠炎；不随当前项目选择变化。',
        '## 本步问题', question, '## 已有输入/结果', f'{path}；{rows}行；SHA256：{digest}',
        '## 传统操作对照（教学路线，非原操作日志）', traditional,
        '## 结果解读', interpretation, '## 待补证据与比较边界', missing,
        '## 本站操作', platform, '关联分析不证明治疗机制或临床疗效。'])


def render_case_step(section, step):
    import streamlit as st
    key = STEP_CASES.get((section, step))
    if key is None:
        return
    title, path, question, traditional, interpretation, missing, platform = CASES[key]
    with st.expander('五积散案例对照 · '+title):
        st.caption('固定教学案例：五积散—溃疡性结肠炎。展示已有文件，不随所选项目变化，不覆盖原始结果。')
        st.write('本步问题：'+question)
        left, right = st.columns(2)
        with left:
            st.markdown('**传统操作与文件交接**')
            st.write(traditional)
        with right:
            st.markdown('**本站对应操作**')
            st.write(platform)
        try:
            table, digest = case_table(key)
        except (OSError, ValueError) as error:
            st.warning('案例文件暂不可用；课程仍可继续。'+str(error))
            return
        st.caption(f'已有归档：{path} · {len(table):,}行；以下仅展示前8行，不代表全部数据。')
        preview = table.sort_values('degree', ascending=False) if key == 'topology' else table
        st.dataframe(preview.head(8), hide_index=True, width='stretch')
        if key == 'topology':
            st.caption('已有结果再绘图：连接数前10位，不是重新筛出的治疗靶点。')
            st.bar_chart(preview.head(10).set_index('gene_symbol')[['degree']])
        st.markdown('**怎样读结果**')
        st.write(interpretation)
        if key == 'overlap':
            audit = overlap_audit()
            st.json(audit)
            if audit['only_in_current_intersection'] or audit['only_in_saved_overlap']:
                st.warning('现有两侧表的直接交集与保存结果不同。可能存在未归档的筛选步骤，需要追溯；本面板不会自动改写任何结果。')
            else:
                st.success('现有表的字符串交集与归档结果一致；这不替代生物学ID和来源审核。')
        if key == 'ml':
            flags = pd.read_csv(CASE / 'results/ml_quality_flags.csv')
            st.dataframe(flags, hide_index=True, width='stretch')
        st.warning('待补/不可推断：'+missing)
        st.caption('传统路线是本课推荐操作，不是已确认的原研究操作日志。补齐记录后才能开展同输入、同方法的数值复核。')
        st.download_button('下载本步案例解析与文件校验值', companion_markdown(key,digest,len(table)).encode('utf-8-sig'),
                           f'wujisan_case_{key}.md', 'text/markdown', key='case_companion_'+key)
