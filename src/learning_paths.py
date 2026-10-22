"""网络药理学双路线课程：数据库操作、传统工具与本站实训。"""

from src.collection_guide import TABLE_SCHEMAS, collection_markdown, render_collection_guide
from src.disease_guide import disease_markdown, render_disease_guide, render_disease_download
from src.ppi_guide import ppi_markdown, render_ppi_guide
from src.enrichment_guide import enrichment_markdown, render_enrichment_guide
from src.transcriptome_guide import transcriptome_markdown, render_transcriptome_guide
from src.ml_guide import ml_markdown, render_ml_guide
from src.advanced_guides import advanced_markdown, render_advanced_course
from src.course_delivery import capability_markdown, render_delivery
from src.learning_exercises import render_exercise, render_learning_record
from src.first_experiment import render_first_experiment
from src.published_validation import render_published_validation

RESOURCES = [
    ("TCMSP", "https://tcmsp-e.com/", "药材、成分、ADME与靶点线索", "历史常用资源；可用性、下载与授权以站点为准"),
    ("HERB", "https://herb.ac.cn/", "药材、成分、靶点与文献证据", "本次访问未成功；可选其他资源或原始文献"),
    ("ETCM", "http://www.tcmip.cn/ETCM/", "中药、成分与候选靶点的补充来源", "补充入口，访问和版本需自行核实"),
    ("PubChem", "https://pubchem.ncbi.nlm.nih.gov/", "成分CID、结构、SMILES和同义名", "官方入口可访问；结构信息不等于靶点实验证据"),
    ("UniProt", "https://www.uniprot.org/id-mapping", "蛋白ID映射与物种核对", "保留原始ID、映射状态和一对多结果"),
    ("GeneCards", "https://www.genecards.org/", "人类疾病相关基因与关联评分", "本次出现访问验证；检索、下载和使用受条款约束"),
    ("DISGENET", "https://disgenet.com/", "疾病—基因关联与证据来源", "官方入口可访问；部分功能需账户或授权"),
    ("OMIM", "https://omim.org/", "遗传表型和基因的文献线索", "补充证据，不能代替疾病全体相关基因集"),
    ("STRING", "https://string-db.org/", "蛋白功能关联或物理互作网络", "先选择网络类型、物种、证据来源与阈值"),
    ("Cytoscape", "https://cytoscape.org/", "网络导入、属性映射、拓扑与图形导出", "桌面软件；Analyzer与可选插件用途不同"),
    ("g:Profiler", "https://biit.cs.ut.ee/gprofiler/", "在线功能富集与ID转换的备选工具", "核对物种、背景与多重校正方法"),
    ("clusterProfiler", "https://bioconductor.org/packages/release/bioc/html/clusterProfiler.html", "R/Bioconductor富集与可复现绘图", "适合保存代码、数据库版本与分析参数"),
]

LESSONS = [
    {
        "title": "01 明确研究问题与资料登记",
        "question": "要研究哪一个复方、哪一种疾病、哪个物种？",
        "input": "处方出处、药材规范名、疾病定义与研究物种。",
        "output": "研究方案、药材清单、数据来源登记表。",
        "traditional": """1. 从处方文献、药典或已发表研究确认处方组成，记录名称、炮制与剂量；同名异物要核对。
2. 疾病同时记录中文、英文名和可用的标准疾病ID，例如 Ulcerative colitis；预先约定纳入与排除标准。
3. 在 Excel 或 LibreOffice 建立工作簿：药材、成分、药物靶点、疾病基因、来源登记各一张表。
4. 每条关系记录数据库名称、版本、查询日期、原始ID、证据类型和文献链接。原始下载文件单独保存。""",
        "choices": "Excel适合初学者手工核对；R/Python适合批量清洗与保留脚本。文献与数据库可组合使用，但应分别标记来源。",
        "platform": "下载本课程的资料登记模板；完成外部检索后按模板整理。本站当前不代替药材数据库检索，也不会自动生成未核实的药材—成分关系。",
        "checks": ["能说清楚研究问题与物种", "处方组成可追溯到出处", "每个文件有来源、日期和版本"],
        "links": [("PubMed 文献检索", "https://pubmed.ncbi.nlm.nih.gov/")],
    },
    {
        "title": "02 收集药材、成分与候选靶点",
        "question": "复方包含哪些成分？哪些候选靶点有证据支持？",
        "input": "已确认的药材清单和预先确定的筛选标准。",
        "output": "药材—成分表、成分—靶点表及证据来源。",
        "traditional": """1. 在 TCMSP、HERB 或 ETCM 中逐味检索规范药名，同时核对拉丁名和别名；数据库没有该药材时记录缺失，不随意替换。
2. 收集成分名称、数据库成分ID、可获得的 PubChem CID、SMILES、药材来源，以及 OB、DL 等确实存在的属性。
3. 收集靶点原始ID、蛋白名、物种、来源、实验或预测证据及文献。预测靶点与实验支持靶点分别标记。
4. 若研究设计采用 OB≥30%、DL≥0.18，注明这只是部分研究常用的筛选约定，并解释依据；不要将阈值当成通用标准，也不要给缺失数据补造数值。
5. 使用 PubChem 核对同义名与结构，避免把同一化合物的不同名称当作不同成分。
6. 可以用 SwissTargetPrediction 等工具对具有可靠结构的成分预测靶点，保留输入SMILES、物种和预测分数，并明确其预测性质。""",
        "choices": "数据库整合路线适合快速形成候选集；文献证据路线更适合核对关键关系；结构预测路线用于补充假设。三类证据不能不加区分地合并。",
        "platform": "按下载的成分—靶点登记模板整理资料。本课程提供字段与来源规范；网络实验接受整理后的边表，尚不自动抓取上述数据库或执行结构靶点预测。",
        "checks": ["药材、成分和靶点ID可追溯", "实验与预测证据分开", "筛选阈值有依据，缺失值未伪造"],
        "links": [("PubChem", "https://pubchem.ncbi.nlm.nih.gov/"), ("SwissTargetPrediction", "http://www.swisstargetprediction.ch/")],
    },
    {
        "title": "03 标准化蛋白ID与基因符号",
        "question": "不同来源的靶点是否真的是同一个基因？",
        "input": "靶点原始ID、命名体系与物种。",
        "output": "保留原始ID的映射表、未映射清单和去重后的靶点集。",
        "traditional": """1. 在 UniProt 的 ID Mapping 中选择准确的输入ID体系，例如 UniProtKB accession；批量粘贴或上传ID。
2. 选择合适的输出体系，下载带From/To对应关系的映射结果及可获得的主基因名、物种、Entry、审核状态；核对 organism/taxonomy，人类为 Homo sapiens（9606）。只有蛋白名或基因符号时先按物种检索UniProtKB并人工核查，不把它们冒充accession提交。
3. 保留 original_id、uniprot_id、gene_symbol、species 和 mapping_status。一对多映射保留明细并核查，不直接取第一条。
4. 区分基因符号、蛋白名和 STRING protein ID。基因符号不是所有物种都适合统一转大写。
5. 先完成命名和物种统一，再对同一基因去重；保留它来自哪些成分和数据库的关系明细。""",
        "choices": "少量ID可在 UniProt 网页映射；大量ID可采用其官方API或R/Python脚本。人工复核仍用于未映射和一对多项。",
        "platform": "本站网络实验会去除节点名称首尾空格，但这不等于生物学ID映射。请在外部完成正式映射后上传，不能把蛋白名和基因符号混在同一列。",
        "checks": ["映射前后物种一致", "未映射和一对多记录保留", "所有后续集合采用同一种ID体系"],
        "links": [("UniProt ID Mapping", "https://www.uniprot.org/id-mapping"), ("ID Mapping 帮助", "https://www.uniprot.org/help/id_mapping")],
    },
    {
        "title": "04 收集疾病基因并求交集",
        "question": "哪些药物候选靶点也与疾病有关？",
        "input": "疾病关键词/ID、标准化药物靶点和疾病关联证据。",
        "output": "疾病基因明细表、共同靶点表和来源统计。",
        "traditional": """1. 分别在 GeneCards、DISGENET、OMIM 等资源检索准确疾病名称和同义词，记录匹配到的疾病ID。
2. 下载或按许可整理 gene_symbol、疾病ID、来源、评分、证据类型、查询日期和文献。不同数据库的评分尺度不能直接混算。
3. 对每个来源单独制定筛选规则，例如某评分阈值或实验/文献证据要求，并报告筛选前后数量；不能事后为了得到期望数量而改阈值。
4. 统一ID和物种后去重。多来源并集提高覆盖面，来源交集更严格；两种选择都需要说明目的。
5. 在 Excel 用去重与匹配函数，或在 R/Python 做集合交集：药物靶点∩疾病基因。维恩图只表示集合关系。""",
        "choices": "在线集合工具适合少量基因；Excel适合人工审核；R/Python适合复现。若以差异表达基因作为疾病证据，应交代数据集、对照与差异分析方法。",
        "platform": "本课程的「疾病基因与交集（详细操作）」提供数据库取舍、来源审核工作表与双清单交集现场练习。项目工具中的项目管理可上传标准化基础数据并生成交集；五积散案例提供现有共同靶点示范。上传前仍需完成数据库检索与来源筛选。",
        "checks": ["疾病实体匹配准确", "各来源评分分别处理", "共同靶点未被解释为已验证治疗靶点"],
        "links": [("GeneCards", "https://www.genecards.org/"), ("DISGENET", "https://disgenet.com/"), ("OMIM", "https://omim.org/")],
    },
    {
        "title": "05 用 STRING 获取 PPI 数据",
        "question": "共同靶点之间有哪些蛋白关联？哪些边可以纳入分析？",
        "input": "共同靶点基因列表及物种。",
        "output": "节点映射表、互作边表、STRING参数与原始网络图。",
        "traditional": """1. 打开 STRING，选择 Multiple proteins，逐行输入共同靶点并选择研究物种；提交后逐项检查映射、重名和未识别项。
2. 在网络设置中选择 functional association 或 physical interaction。前者包含功能关联，不代表所有边都是直接物理结合。
3. 记录证据通道，例如 experiments、databases、co-expression、text mining 等；不同通道不具有相同证据性质。
4. 选择置信度阈值。0.4、0.7、0.9是常见比较值，可分别观察敏感性；它们不是研究质量的单一标准。
5. 首次分析将新增邻接蛋白数量设为0，避免不知不觉把输入列表以外的蛋白纳入。若要扩展邻居，另存一份扩展网络并说明理由。
6. 在导出区域下载 tabular/TSV 边表，并保存节点标识映射；文件格式和界面会随版本变化。优先保留两个端点、combined_score 和证据分数。
7. 核对分数是0–1还是0–1000；例如0.7与700可能代表同一尺度转换后的阈值。不要把 confidence 当成最短路径距离。
8. 分别记录输入数、映射数、有边节点数和孤立节点。只看边表可能丢失孤立节点。""",
        "choices": "STRING网页适合可视化检索；Cytoscape的stringApp适合在桌面内查询并继续美化；STRING官方API适合脚本复现。BioGRID或IntAct可用于有出处的物理互作补充，需核对物种与证据。",
        "platform": "完成 STRING 检索后，在「03 PPI构图」第7步上传TSV/CSV，选择source、target和分数列；若原分数为0–1000，明确选择该尺度。本站负责已获取关系的建网与拓扑计算，目前不自动查询STRING，也不从边表恢复孤立节点。",
        "checks": ["网络类型和证据通道已记录", "新增邻居设置明确", "分数尺度与阈值一致", "孤立节点和映射损失有记录"],
        "links": [("STRING", "https://string-db.org/"), ("STRING 官方 FAQ", "https://string-db.org/help/faq/"), ("BioGRID", "https://thebiogrid.org/"), ("IntAct", "https://www.ebi.ac.uk/intact/")],
    },
    {
        "title": "06 用 Cytoscape 细致构图与分析",
        "question": "如何把边表变成可解释、可复现的 PPI 图？",
        "input": "PPI边表、节点属性表和来源参数。",
        "output": "Cytoscape会话、网络图、节点拓扑表及可选模块结果。",
        "traditional": """1. 安装 Cytoscape，使用 File → Import → Network from File 导入边表；指定 Source Node、Target Node，可把关系类型设为 Interaction Type。
2. 用 File → Import → Table from File 导入节点属性；选择网络节点表与匹配键。先检查基因符号能否匹配，避免属性全为空。
3. 在 Style 将节点颜色映射到node_type、节点大小连续映射到Degree、边宽映射到置信度。设置合理的标签和图例，避免把颜色变化误认为显著性。
4. 选择布局，例如 Prefuse Force Directed 或其他可用力导向布局。记录布局名称；图上距离主要由布局算法决定，不能解释为生物距离。
5. 在 Tools 的 Analyze Network/Analyzer 中运行分析，PPI通常选无向。导出 Degree、Betweenness、Closeness 等节点属性。菜单名称以安装版本为准。
6. 可选cytoHubba比较MCC等枢纽排名，可选MCODE发现稠密子网络；插件指标与Degree不同，记录算法与参数，并回查模块的生物学含义。
7. 对多个阈值重跑并比较候选稳定性；不同软件对断连网络、有向图和归一化可能有不同约定。
8. 保存.cys会话，导出节点/边表，并按需要导出SVG/PDF或高分辨率PNG；记录软件和插件版本。""",
        "choices": "Cytoscape适合精细样式、插件和论文制图；本站适合快速计算、教学练习和表格导出；NetworkX/igraph脚本适合批量复现。可把本站节点指标下载后作为Cytoscape节点属性表导入。",
        "platform": "在「03 PPI构图」第7步运行同一边表，查看Degree、Betweenness、Closeness、连通分量和密度，并下载节点指标与清洗边表。本站中心性使用无权最短路径，weight用于筛选与布局；当前未实现cytoHubba MCC、MCODE或精细排版。",
        "checks": ["节点属性匹配正确", "图例解释节点和边的含义", "拓扑算法与方向性明确", "会话、版本和原始边表已保存"],
        "links": [("Cytoscape 下载", "https://cytoscape.org/"), ("官方网络导入手册", "https://manual.cytoscape.org/en/stable/Creating_Networks.html"), ("官方 Analyzer 手册", "https://manual.cytoscape.org/en/stable/Network_Analyzer.html"), ("Cytoscape App Store", "https://apps.cytoscape.org/")],
    },
    {
        "title": "07 GO/KEGG富集的多种路线",
        "question": "候选基因在哪些功能或通路中出现得更频繁？",
        "input": "基因列表、实际可选的背景基因、物种和注释版本。",
        "output": "包含完整检验条目、FDR、命中基因与背景定义的富集结果。",
        "traditional": """1. 网页路线可选g:Profiler或其他具有明确文档的富集工具，设置物种、ID类型与背景，并记录其实际校正方法。
2. R路线可选clusterProfiler：GO可使用enrichGO；KEGG可使用enrichKEGG并核对物种代码、ID转换、背景与数据库访问许可。
3. 明确区分ORA与GSEA。ORA需要一个筛选基因集；GSEA通常需要全基因排序列表，不能把二者结果和参数混用。
4. 校正范围包括实际检验的条目，不能只挑显著结果再重算FDR。保存非显著结果便于复核。
5. 绘图时同时查看命中数、GeneRatio、富集倍数和FDR；不要只展示最小P值。""",
        "choices": "网页工具便于快速探索；clusterProfiler适合脚本复现；本站适合讲解超几何ORA并使用自备注释集。各工具数据库版本、背景和校正策略不同，结果不一定完全一致。",
        "platform": "在「04 GO/KEGG富集」第6步上传目标基因、背景与基因—条目注释表，直接运行ORA。正式分析须准备合法的完整注释资源；内置小型示例用于教学演示，不能替代真实GO/KEGG数据库。",
        "checks": ["ORA或GSEA选择有依据", "背景与研究抽样范围一致", "物种、注释版本与校正范围可追溯"],
        "links": [("g:Profiler", "https://biit.cs.ut.ee/gprofiler/"), ("clusterProfiler", "https://bioconductor.org/packages/release/bioc/html/clusterProfiler.html"), ("GO 注释资源", "https://geneontology.org/docs/download-go-annotations/"), ("KEGG", "https://www.kegg.jp/")],
    },
    {
        "title": "08 证据扩展与完整实验报告",
        "question": "网络候选能被哪些独立数据支持？怎样形成可复核结论？",
        "input": "核心网络结果及可用的表达、遗传或单细胞数据。",
        "output": "有来源、方法、参数、结果和局限性的实验报告。",
        "traditional": """1. 转录组可从GEO等资源获取表达与分组，先核对研究设计、批次和平台，再选择limma或DESeq2等适用方法。
2. 机器学习用表达和分组建立预测模型，训练/测试分开；特征筛选和标准化放入训练流程。它评估预测能力，不自动给出治疗机制。
3. 免疫分析可按数据与目的选择ssGSEA、去卷积工具等；前者是相对富集，不能直接当细胞比例。
4. MR需要暴露/结局GWAS汇总统计、独立工具变量和等位基因协调，可采用TwoSampleMR等成熟工具，并检查工具强度、异质性及多效性。
5. 细胞通讯通常使用带细胞注释的单细胞数据，可选择CellChat或CellPhoneDB；计算扰动选择与数据、模型假设匹配的方法。它们是按问题选用的分支。
6. 报告写清研究问题、资料来源、筛选流程、各步参数、实际结果及解释边界。相同表达矩阵产生的多个分析不能算完全独立验证。""",
        "choices": "先完成核心网络药理学流程，再根据研究问题选择证据扩展。无需为了模块数量而运行所有方法。",
        "platform": "转录组、机器学习、免疫评分和MR课程已提供限定设计下的上传计算，输入条件与方法边界见各课计算区。单细胞通讯仍以外部工具教学为主；计算扰动演示不等于细胞生物学敲除。五积散案例为结果解读，不能替代独立验证。",
        "checks": ["每个扩展方法都回答明确问题", "同源数据未被重复计为独立证据", "报告含原始文件、参数及局限性"],
        "links": [("GEO", "https://www.ncbi.nlm.nih.gov/geo/"), ("TwoSampleMR 文档", "https://mrcieu.github.io/TwoSampleMR/")],
    },
]


def course_markdown():
    parts = ["# 网络药理学：传统工具与本站实训双路线\n", "课程更新日期：2026-10-23。网站界面和访问权限以官方最新说明为准；各资源核对日期见课程说明。\n"]
    for lesson in LESSONS:
        parts.extend([
            f"## {lesson['title']}", f"研究问题：{lesson['question']}",
            f"输入：{lesson['input']}", f"产物：{lesson['output']}",
            "### 传统工具路线", lesson["traditional"],
            "### 多种选择", lesson["choices"],
            "### 本站路线与当前能力", lesson["platform"],
            "### 完成检查", "\n".join(f"- {check}" for check in lesson["checks"]),
            "### 官方参考", "\n".join(f"- [{name}]({url})" for name, url in lesson["links"]),
        ])
    parts.append(collection_markdown())
    from src.symmap_guide import symmap_markdown
    parts.append(symmap_markdown())
    parts.append(disease_markdown())
    parts.append(ppi_markdown())
    parts.append(enrichment_markdown())
    parts.append(transcriptome_markdown())
    parts.append(ml_markdown())
    parts.append(advanced_markdown())
    parts.append(capability_markdown())
    return "\n\n".join(parts)


def _open_course_route(route_id):
    import streamlit as st
    st.query_params["view"] = route_id


def render_course_overview():
    import pandas as pd
    import streamlit as st
    st.subheader("HerbInsight · 从会看结果，到会完成分析")
    st.write("面向中医药与生命科学初学者的网络药理学教学实训平台。沿着资料收集、数据整理、分析计算、结果解释完成一次可追溯的学习任务。")
    st.info("第一次来：从01开始。已有规范数据：直接进入对应课程的计算区。五积散—溃疡性结肠炎用于案例解读，不是已证实的治疗机制或临床建议。")
    render_first_experiment()
    with st.expander("这次学习要交付什么？", expanded=False):
        st.markdown("**任务**：为一个明确的复方—疾病问题建立候选关联分析。\n\n**准备**：处方出处与物种、来源登记、药材/成分/靶点关系、疾病基因证据。\n\n**交付**：映射审核表、共同靶点、PPI边表与参数、富集结果及背景说明、包含局限性的分析记录。\n\n**完成标准**：每张结果图能追溯到输入、来源、参数和方法；能解释关联为何不等于机制。")
    st.write("先完成下面4个核心阶段，再按研究问题选择进阶证据。左侧可直接进入任一章节，无需切换模式或横向翻找。")
    cards = [
        ("01 资料检索与ID整理", "去哪查药材、成分与靶点；怎样保留证据并完成UniProt核对。", "learn_collection"),
        ("02 疾病基因与交集", "收集疾病证据、分别筛选来源，并现场练习求共同靶点。", "learn_disease"),
        ("03 PPI构图", "STRING下载与Cytoscape操作；把边表交给本站做网络分析。", "learn_ppi"),
        ("04 GO/KEGG富集", "准备目标、背景和完整注释，选择网页、R或本站ORA。", "learn_enrichment"),
    ]
    for start in (0, 2):
        for col, (title, description, route) in zip(st.columns(2), cards[start:start + 2]):
            with col.container(border=True):
                st.subheader(title)
                st.write(description)
                st.button("进入学习", key="start_" + route, on_click=_open_course_route, args=(route,), width="stretch")
    st.caption("跟着课程准备资料，在PPI第7步、GO/KEGG第6步即可上传数据并计算，无需另找入口。进阶证据按研究需要选学。")
    st.caption("在资料整理、富集、转录组和机器学习课程中，展开「纠错挑战」练习常见错误；课程内可计算，不要求先完成测验。")
    render_learning_record()
    with st.expander("查看8步输入与产物对照"):
        st.dataframe(pd.DataFrame([
            {"阶段": lesson["title"], "准备材料": lesson["input"], "应得到的产物": lesson["output"]}
            for lesson in LESSONS
        ]), hide_index=True, width="stretch")
    st.download_button("下载完整操作课程（Markdown）", course_markdown().encode("utf-8-sig"), "network_pharmacology_course.md", "text/markdown")


def render_compact_lessons():
    import streamlit as st
    selected = st.selectbox("选择当前学习步骤", range(len(LESSONS)), format_func=lambda index: LESSONS[index]["title"])
    lesson = LESSONS[selected]
    st.subheader(lesson["question"])
    st.write(f"输入：{lesson['input']}")
    st.write(f"本步产物：{lesson['output']}")
    st.caption("需要详细清单与字段模板？从左侧核心学习或进阶证据直接进入相应章节。")
    traditional, platform = st.tabs(["传统网站与软件操作", "本站实训与替代选择"])
    with traditional:
        st.markdown(lesson["traditional"])
        for name, url in lesson["links"]:
            st.link_button(name, url)
    with platform:
        st.markdown(lesson["platform"])
        st.markdown(lesson["choices"])
    for index, check in enumerate(lesson["checks"]):
        st.checkbox(check, key=f"course_check_{selected}_{index}")
    st.caption("勾选用于当前浏览会话自查；下载实验记录后自行保存。")


def render_course_resources():
    import pandas as pd
    import streamlit as st
    from pathlib import Path
    with st.expander("作品验证与演示材料（不增加学习步骤）"):
        st.write("自动化检查验证软件行为，不证明教学效果或临床有效性。已完成GSE38713探索性再分析与论文摘要对照，见转录组课程；独立队列验证、全文严格复现及真人试用尚未完成。")
        docs = Path(__file__).resolve().parents[1] / "docs"
        for filename, label in [("reviewer_walkthrough.md", "评审演示与能力边界"), ("pilot_protocol.md", "初学者试用任务与空白记录"), ("validation_protocol.md", "真实数据复核方案"), ("contribution_disclosure.md", "原创贡献与AI使用披露模板")]:
            st.download_button("下载" + label, (docs / filename).read_bytes(), filename, "text/markdown", key="artifact_" + filename)
    render_learning_record()
    with st.expander("数据库入口与常用登记模板"):
        st.dataframe(pd.DataFrame(RESOURCES, columns=["资源", "官方入口", "收集资料/用途", "访问与使用说明"]), hide_index=True, width="stretch", column_config={"官方入口": st.column_config.LinkColumn("官方入口")})
        st.caption("2026-10-22核对部分官方入口与文档，入口可达不表示已验证所有下载功能。详细模板见左侧对应课程。")
        templates = {
            "source_register.csv": ["source_db", "database_version", "query_date", "query_terms", "species", "filters", "download_file", "reference_url", "license_notes"],
            "compound_target_register.csv": ["herb_name", "compound_id", "compound_name", "pubchem_cid", "smiles", "original_target_id", "gene_symbol", "species", "evidence_type", "source_db", "reference_url"],
            "id_mapping_register.csv": next([key for key, _, _ in fields] for filename, _, fields in TABLE_SCHEMAS if filename == "id_mapping_register.csv"),
            "disease_gene_register.csv": ["disease_name", "disease_id", "gene_symbol", "species", "source_db", "evidence_score", "evidence_type", "screening_criteria", "query_date", "reference_url"],
            "cytoscape_node_attributes.csv": ["node_id", "gene_symbol", "node_type", "source_db", "evidence_type"],
        }
        st.caption("这些是资料登记空表，不是可直接运行的示例。Cytoscape导入节点属性时，用node_id与网络节点标识匹配；若边使用STRING ID，需先用映射表统一，不能直接按基因符号硬匹配。网络实验的可运行边表示例在实验页下载。")
        st.caption("成分靶点register为简版来源登记；新手建议使用详细操作页的raw→mapping→standardized分层工作表，避免把未审核ID直接当基因。")
        for filename, columns in templates.items():
            st.download_button(f"下载 {filename}", pd.DataFrame(columns=columns).to_csv(index=False).encode("utf-8-sig"), filename, "text/csv")
    st.download_button("下载完整操作课程（Markdown）", course_markdown().encode("utf-8-sig"), "network_pharmacology_course.md", "text/markdown")
    render_delivery()


SECTION_TITLES = {
    "overview": "学习路线", "collection": "01 资料检索与ID整理", "disease": "02 疾病基因与交集",
    "ppi": "03 PPI构图", "enrichment": "04 GO/KEGG富集", "transcriptome": "转录组数据与设计",
    "ml": "机器学习与评估", "immune": "免疫微环境", "mr": "孟德尔随机化",
    "single_cell": "单细胞与细胞通讯", "perturbation": "计算扰动与虚拟敲除",
    "lessons": "8步简明课程", "resources": "资料模板与交付自查",
}


def page_learning_paths(cfg, project_id, section="overview", practice=None):
    import streamlit as st
    section = section if section in SECTION_TITLES else "overview"
    st.header(SECTION_TITLES[section])
    from src.data_handoff import render_data_handoff
    render_data_handoff(section)
    if section == "transcriptome":
        render_published_validation()
    render_exercise(section)
    renderers = {
        "overview": render_course_overview, "collection": render_collection_guide,
        "ppi": render_ppi_guide, "enrichment": render_enrichment_guide,
        "transcriptome": render_transcriptome_guide, "ml": render_ml_guide,
        "lessons": render_compact_lessons, "resources": render_course_resources,
    }
    if section == "ppi":
        render_ppi_guide(practice=practice)
    elif section == "enrichment":
        render_enrichment_guide(practice=practice)
    elif section == "disease":
        render_disease_download()
        render_disease_guide()
    elif section in ("immune", "mr", "single_cell", "perturbation"):
        render_advanced_course(section)
    else:
        renderers[section]()
