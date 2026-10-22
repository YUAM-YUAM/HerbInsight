"""其余证据分支的完整教学交接；不把课程包装为已开放算法。"""

ADVANCED_COURSES = {
    "immune": {
        "title": "免疫微环境教学", "boundary": "本课程可上传表达与自备签名计算ssGSEA及独立两组比较；不提供去卷积或细胞比例估计。",
        "links": [("GSVA/Bioconductor", "https://bioconductor.org/packages/GSVA/"), ("MSigDB", "https://www.gsea-msigdb.org/gsea/msigdb/"), ("CIBERSORTx", "https://cibersortx.stanford.edu/"), ("immunedeconv", "https://omnideconv.org/immunedeconv/")],
        "steps": [
            ("1. 先选择问题：富集分数还是细胞比例？", """bulk组织表达是多种细胞信号的混合。先确定想比较免疫相关签名的相对富集，还是在特定参考下推断细胞组成。

ssGSEA等签名评分不是细胞计数；某些去卷积方法可输出相对组成或其他分数，但其含义取决于模式、参考和算法，不能统一写成“浸润比例”。不把免疫分数和基因表达相关直接解释为该基因调控细胞。"""),
            ("2. 准备表达、样本表与签名/参考", """沿用上一节经审核的表达矩阵与分组，核对组织、物种、尺度、基因ID和患者结构。根据目标方法的文档决定需要counts、归一化或非log数据，不能任意反log或把已log数据再log。

签名可从有出处的论文补充材料、许可允许的MSigDB集合或方法配套资源取得。保存完整基因集/参考原件、物种、版本、细胞类型定义与出处。MSigDB并非所有集合都是免疫细胞签名，也不保证任意组织适用。

统计每个签名的总基因数、表达中命中数和覆盖比例；匹配不足时记录并设合理纳入规则，不自动补0。混合物种签名需明确映射，不能只改大写。"""),
            ("3. 多条工具路线：输入和输出要按所选方法解释", """**R/GSVA路线**：根据安装版本文档构建ssGSEA适用参数对象和运行GSVA，记录版本、签名、归一化选项和输入处理。新旧版本函数接口可能不同，不直接复制旧教程。

**CIBERSORTx路线**：按其授权、参考签名、混合表达矩阵格式与运行模式提交；记录是否输出相对组成/absolute score等。对不可公开数据，先确认是否允许外传，不直接上传敏感个体资料。

**immunedeconv等R整合路线**：逐个核对被调用方法的数据和许可要求；统一入口并不代表不同方法输出在同一尺度。

本课程实际操作区使用GSEApy运行ssGSEA；上述R和网页工具是可选的外部路线。请记录实际采用的实现与参数。"""),
            ("4. 比较组别与候选基因：避免伪重复", """保存每个样本×每个签名/细胞类型的原始结果，字段区分score_type与method。按患者、配对、批次和协变量选择适当比较模型，记录多重检验范围与校正方法。

候选基因与免疫签名做相关时明确Pearson/Spearman等、样本范围与校正；若该基因本身在签名中，存在直接数学耦合，应评估移除该基因等敏感性分析，而非当独立证据。

相对组成存在总和约束，评分也有相依性。没有适用理由，不把不同签名的数值大小解释为“哪种细胞最多”。"""),
            ("5. 交付文件与质量检查", """保存签名登记、覆盖表、样本长表结果、组间完整检验表、相关分析表、参数和软件版本。检查样本ID、缺失值与异常分布，不能把未输出的细胞类型当作真实0。

结果图注明方法与单位（相对评分/估计比例等）。报告同一表达矩阵产生的结果不是独立于转录组的新队列验证。"""),
            ("6. 接回平台与下一步", """「案例解读→免疫微环境结果」用于读已有数据。本课程实际操作区可上传表达与签名进行ssGSEA，下载评分、覆盖审核和组间比较；同一分析数据中的归一化分数不应直接与另一独立运行的分数混算。

若需要解释细胞来源或通讯，选择具有细胞注释的单细胞数据，而不是把bulk免疫评分自动转成细胞通讯网络。"""),
        ],
        "tables": {
            "immune_signature_register.csv": [("signature_id", "签名唯一编号"), ("cell_type", "原定义细胞类型/状态"), ("species", "物种"), ("source", "论文/资源及许可"), ("version", "版本"), ("gene_set_file", "原始GMT/基因集合路径"), ("gene_count", "签名基因数"), ("matched_gene_count", "表达覆盖数"), ("coverage_rule", "覆盖纳入规则")],
            "immune_scores_long.csv": [("sample_id", "与样本表一致"), ("signature_id", "关联签名"), ("cell_type", "细胞/签名名称"), ("method", "实际方法和模式"), ("score_type", "relative_score/estimated_fraction等"), ("score", "原始输出，不混尺度"), ("dataset", "数据来源")],
            "immune_run_register.csv": [("run_id", "运行编号"), ("expression_file", "输入矩阵"), ("sample_file", "样本表"), ("input_scale", "归一化与log状态"), ("signature_version", "签名/参考版本"), ("software_version", "方法/版本"), ("parameters", "实际设置"), ("comparison_design", "组别/配对/协变量"), ("correction_family", "实际多重校正范围"), ("limitations", "适用性与不确定性")],
        },
    },
    "mr": {
        "title": "孟德尔随机化教学", "boundary": "可上传外部已做LD筛选的汇总表，进行单碱基等位基因协调、F筛选、IVW及逐一剔除分析；不自动下载GWAS或做LD筛选。",
        "links": [("GWAS Catalog", "https://www.ebi.ac.uk/gwas/"), ("OpenGWAS", "https://opengwas.io/"), ("TwoSampleMR", "https://mrcieu.github.io/TwoSampleMR/"), ("ieugwasr", "https://mrcieu.github.io/ieugwasr/")],
        "steps": [
            ("1. 先定义暴露、结局与可解释单位", """MR通常使用遗传工具评估某暴露对结局的潜在因果影响；不是把机器学习重要基因直接传入就能得到因果结论。

明确暴露是表达(eQTL)、蛋白(pQTL)还是其他表型，组织、祖源、测量单位及方向；结局定义、病例/对照或连续单位也要明确。基因表达与蛋白丰度不等价，MR遗传代理也不等同于复方直接干预。

写明相关性、独立性、排除限制三类核心假设及可能违背途径；任何统计显著性都不自动确认这些假设。"""),
            ("2. 去哪里拿什么：完整GWAS/QTL汇总统计", """在GWAS Catalog、OpenGWAS或经许可的原始GWAS/QTL研究资源中查找匹配表型。保存研究/数据集ID、原文、样本量、祖源、组织、基因组版本、暴露/结局单位和可能样本重叠。

每个SNP至少核对rsID或位置、effect_allele、other_allele、beta、se、P值，尽量保留effect allele frequency(EAF)、样本量、染色体/位置。OR形式须按定义转log(OR)，SE也必须是相同效应尺度。

账号、令牌、API配额和使用许可按资源要求；不要把令牌写进下载表或代码截图。不是所有网页都提供全部字段，没有SE或等位基因不能当成可直接MR的合格数据。"""),
            ("3. 选择工具变量：强度、LD、祖源与方向", """根据研究目的预先设显著性、cis/trans范围、LD阈值/窗口与参考祖源。常见门槛只是研究方案，不是所有暴露通用的唯一标准。

用TwoSampleMR等适用工具或PLINK及祖源匹配参考做LD去相关；保存筛除原因。不能只按rsID不同就认为独立。F≈(beta_exposure/se_exposure)^2可作单SNP强度近似诊断，不能单靠一个F阈值保证所有MR假设。

记录弱工具、样本重叠、群体分层和相关多效性风险。分子性状cis工具可能需要结合共定位等分析排查LD中不同因果变异，不把“cis”当作自动有效。"""),
            ("4. 协调等位基因：不能直接按SNP行合并", """按SNP与基因组版本连接暴露/结局，核对效应等位基因方向、正负链和EAF。需要翻转时改变对应beta方向并保持SE含义，记录协调决定。

A/T、C/G回文SNP的方向有歧义，需按频率、数据质量和方法规则判断；无法可靠判断时排除并保留记录。多等位、插入缺失、版本差异与代理SNP需额外核查，不静默替换。

TwoSampleMR的harmonise_data等可辅助，但要保留结果和剔除列表。缺失EAF不能伪造，单靠某个字符串看起来一致也不能确认已协调。"""),
            ("5. 主分析与敏感性分析各自回答什么", """单工具可做Wald ratio；多个合格、近似独立工具可按适用假设使用IVW。选择固定/随机效应及误差处理，保存原始效应、SE、CI与P值，说明暴露增加单位。

异质性Q、leave-one-out、加权中位数、MR-Egger等各有额外假设与样本要求。加权中位数依赖有效工具权重条件，Egger依赖InSIDE等且可能低功效；不显著的多效性检验不等于不存在多效性。

按设计考虑反向MR、方向性诊断和共定位等；不要把同一组工具的多种算法当作多个独立实验。结局为log-odds时才按定义指数化为OR，连续结局不能都标OR。"""),
            ("6. 整理表格、完整结果与证据边界", """保存原始汇总统计、工具筛选、LD参数、协调明细、主分析、敏感性分析和剔除理由。多个暴露/结局检验要声明多重校正范围，不只保留P<0.05的一对。

结论限定于人群、遗传代理与假设。表达/蛋白遗传倾向不等于短期药物作用，更不能由MR直接证明某复方有效。本站现有MR页面仅解读案例结果。"""),
        ],
        "tables": {
            "gwas_dataset_register.csv": [("role", "exposure/outcome"), ("dataset_id", "实际数据集ID"), ("trait", "准确表型"), ("unit", "beta效应单位"), ("ancestry", "祖源"), ("tissue", "QTL组织，适用时"), ("sample_size", "样本量"), ("genome_build", "基因组版本"), ("sample_overlap", "与另一数据集重叠情况/未知"), ("reference", "论文/资源/许可")],
            "gwas_summary_template.csv": [("SNP", "变异ID"), ("effect_allele", "效应等位基因"), ("other_allele", "另一等位基因"), ("beta", "效应，OR需明确处理"), ("se", "同尺度标准误"), ("pval", "原始P值"), ("eaf", "效应等位基因频率，缺失留空"), ("samplesize", "适用样本量"), ("chr", "染色体"), ("pos", "坐标"), ("genome_build", "坐标版本")],
            "mr_harmonisation_register.csv": [("SNP", "变异ID"), ("exposure_dataset", "暴露ID"), ("outcome_dataset", "结局ID"), ("action", "保留/翻转/回文剔除等"), ("included", "yes/no/pending"), ("reason", "决定依据"), ("beta_exposure", "协调后暴露效应"), ("se_exposure", "暴露SE"), ("beta_outcome", "同方向结局效应"), ("se_outcome", "结局SE"), ("ld_reference", "祖源/参考/筛选参数")],
        },
    },
    "single_cell": {
        "title": "单细胞与细胞通讯教学", "boundary": "本站未开放单细胞处理或CellChat/CellPhoneDB计算；本课程提供准备、传统工具路线与交付规范。",
        "links": [("GEO", "https://www.ncbi.nlm.nih.gov/geo/"), ("CELLxGENE", "https://cellxgene.cziscience.com/"), ("Seurat", "https://satijalab.org/seurat/"), ("Scanpy", "https://scanpy.readthedocs.io/"), ("CellChat", "https://github.com/jinworks/CellChat"), ("CellPhoneDB", "https://cellphonedb.readthedocs.io/")],
        "steps": [
            ("1. 先问细胞来源，不能把bulk当作单细胞", """要研究哪些细胞表达候选基因、哪些细胞可能通过配体受体交流，需要带细胞粒度的信息。bulk矩阵的每列是混合样本，单细胞矩阵的每列/行依工具格式对应barcode，不能靠矩阵转置互相转换。

患者数与细胞数不同，数万细胞来自一个患者不等于数万生物学重复；先规划组别、组织、患者级比较和独立验证。"""),
            ("2. 检索与下载：表达、细胞元数据、患者元数据", """GEO或CELLxGENE等资源中核对组织、物种、疾病状态、平台和作者处理过程。取得适用的10x matrix.mtx/features/barcodes、h5ad、Seurat对象或作者提供矩阵，格式由实际资源决定。

保存barcode→sample_id→subject_id→group对应关系及细胞注释/marker依据；明确矩阵是原始counts还是已归一化。已有整合对象不能默认为保留了适合差异/通讯的表达层。

原始FASTQ需完整定量流程和参考基因组，已有合格矩阵时不必盲目全量下载。按数据许可和隐私要求使用，不补造缺失患者编号。"""),
            ("3. Seurat/Scanpy基础：QC、聚类与注释", """按实际平台评估低质量细胞、基因覆盖、线粒体比例、doublets与环境RNA；阈值根据样本分布和方案确定，不照抄万能数值。

按工具流程进行适当归一化、特征选择、降维和聚类；记录批次/整合方法。以多个marker、参考映射和生物背景共同注释细胞，不按单一marker盲命名。

用UMAP检查结构，但图上距离不是物理空间距离；整合后的表示适合可视化不必然适合所有差异统计。患者级差异可考虑适用的pseudobulk或重复测量模型，避免把每个细胞当独立患者。"""),
            ("4. CellChat/CellPhoneDB路线：表达支持的候选通讯", """准备所选方法要求的表达尺度、barcode和cell_type，核对物种、基因命名、配体受体数据库版本、多亚基复合物及最低细胞覆盖规则。

按官方教程建立对象、计算并筛选候选配体—受体关系；保存归一化/表达阈值、置换/随机种子、细胞数筛选和校正策略。小群体与掉落可能导致不稳定，不把未检出当确定不存在。

不同疾病组比较时确认细胞注释和可比较患者组成；不能把不同患者数量/细胞比例造成的差异直接解释为通讯变化。不同方法的score定义不同，不混成同一尺度。"""),
            ("5. 交付与证据解释", """保存QC统计、细胞/患者元数据、注释依据、对象与表达层说明、完整候选通讯表、数据库/版本、参数和脚本。

通讯表至少能回查sender、receiver、ligand、receptor、样本/组别、方法分数及可获得的P值/校正。候选通讯是基于表达与数据库的推断，不证明蛋白结合或信号实际发生；需要空间、蛋白或干预等适当验证。

本站目前只有教学入口，不在既有bulk案例上伪造细胞通讯结果。"""),
        ],
        "tables": {
            "single_cell_metadata.csv": [("barcode", "细胞唯一键，跨样本需唯一"), ("sample_id", "样本ID"), ("subject_id", "患者/个体ID"), ("group", "组别"), ("batch", "批次"), ("cell_type", "审核细胞注释"), ("annotation_evidence", "marker/参考及版本"), ("qc_included", "是否纳入和规则")],
            "communication_results_template.csv": [("dataset", "实际数据集"), ("sample_or_group", "结果粒度"), ("sender", "发送细胞类型"), ("receiver", "接收细胞类型"), ("ligand", "配体/复合物"), ("receptor", "受体/复合物"), ("method", "实际方法"), ("score", "本方法定义分数"), ("p_value", "适用时原始P值"), ("p_adjust", "适用时校正值"), ("database_version", "配体受体库版本")],
        },
    },
    "perturbation": {
        "title": "计算扰动与虚拟敲除教学", "boundary": "仅提供方法选择、网络删点示意与归档规范；未开放通用单细胞虚拟敲除或干预预测。",
        "links": [("scTenifoldKnk", "https://github.com/cailab-tamu/scTenifoldKnk"), ("CellOracle", "https://morris-lab.github.io/CellOracle.documentation/")],
        "steps": [
            ("1. 先分清三种完全不同的操作", """PPI网络删点是在固定图中删除节点再看连通性；调控网络扰动依赖推断出的调控关系；表达状态预测依赖训练数据和模型。它们不是同一个算法，不能用一张删点图声称完成基因敲除后的转录组预测。

真实基因敲除还受细胞类型、反馈、时序和补偿影响，计算结果属于模型条件下的假设，不是实验证据。"""),
            ("2. 选择方法及资料前提", """scTenifoldKnk等方法面向适用的单细胞表达/调控网络问题；CellOracle有其GRN、参考信息和状态模拟要求。先读目标版本文档，核对物种、细胞状态、数据层、候选基因表达与参考资源，不能只上传一个基因名。

若用真实扰动数据训练预测模型，保存干预类型、细胞类型、对照、批次和剂量/时间，并设计未见基因/状态等适当留出评估。普通观测表达不自动提供可识别的干预效应。"""),
            ("3. 外部执行和敏感性检查", """按所选官方流程做QC、网络/模型拟合、候选扰动与输出，记录随机种子、网络/正则化参数、对照状态与重复运行稳定性。

比较适当负对照、基因覆盖和网络构建选择；没有合适假设或输入时停止，不把缺失数据自动补为0模拟。结果解释应限制于该细胞类型和模型条件。"""),
            ("4. 本站示意能做什么、不能做什么", """下方仅在虚构无向图删除节点，比较节点、边和连通分量；它没有表达矩阵，不预测基因上/下调，不提供真实细胞敲除、通路激活或药物疗效。

正式单细胞扰动仍需外部工具。本课程将其标为可选高级教学，不计入本站已开放通用算法。"""),
            ("5. 交付与实验验证", """归档输入对象/参考网络、方法/版本、目标基因、细胞状态、参数、所有输出与不确定性。明确输出是拓扑变化、预测表达变化还是状态转移，单位和方向不能混用。

后续独立干预实验或适当外部扰动数据才可检验假设；不可把模型生成结果再喂回同一模型当作独立验证。"""),
        ],
        "tables": {
            "perturbation_run_register.csv": [("run_id", "运行编号"), ("method_version", "实际模型及版本"), ("input_file", "表达/网络/训练对象"), ("reference_source", "参考资源及版本"), ("species", "物种"), ("cell_state", "细胞类型/状态"), ("target_gene", "实际干预基因"), ("perturbation_type", "删点/GRN扰动/真实数据训练预测等"), ("parameters", "参数及种子"), ("control", "对照定义"), ("output_definition", "输出意义及单位"), ("validation", "独立检验方案或尚无"), ("limitations", "假设与适用边界")],
        },
    },
}


def advanced_markdown():
    parts = ["# 可选证据与高级教学", "更新：2026-10-23。资源链接是官方/方法入口，不表示本次已逐项验证在线下载和软件运行。"]
    for course in ADVANCED_COURSES.values():
        parts.extend(["## " + course["title"], "本站能力：" + course["boundary"]])
        for title, body in course["steps"]:
            parts.extend(["### " + title, body])
        for name, fields in course["tables"].items():
            parts.extend(["### " + name, "| 字段 | 含义 |\n| --- | --- |\n" + "\n".join(f"| {key} | {meaning} |" for key, meaning in fields)])
        parts.append("\n".join(f"- [{name}]({url})" for name, url in course["links"]))
    return "\n\n".join(parts)


def ivw_formula_demo(beta_exposure, beta_outcome, se_outcome):
    """仅演示已协调独立工具、忽略暴露误差的固定效应IVW；不执行MR前处理。"""
    import numpy as np
    from scipy.stats import norm, chi2
    x, y, se = [np.asarray(values, dtype=float) for values in (beta_exposure, beta_outcome, se_outcome)]
    if any(v.ndim != 1 for v in (x, y, se)) or len(x) < 2 or len(x) != len(y) or len(x) != len(se):
        raise ValueError("示意IVW至少需要两个长度一致的一维工具列表。")
    if not all(np.isfinite(v).all() for v in (x, y, se)) or (se <= 0).any() or (x == 0).any():
        raise ValueError("效应必须有限，暴露效应非零，结局SE须大于0。")
    weights = 1 / se ** 2
    estimate = float(np.sum(weights * x * y) / np.sum(weights * x ** 2))
    error = float(np.sqrt(1 / np.sum(weights * x ** 2)))
    q = float(np.sum(weights * (y - estimate * x) ** 2))
    return {"beta": estimate, "se": error, "ci_low": estimate - norm.ppf(0.975) * error,
            "ci_high": estimate + norm.ppf(0.975) * error, "p_value": float(2 * norm.sf(abs(estimate / error))),
            "q": q, "q_df": len(x) - 1, "q_p_value": float(chi2.sf(q, len(x) - 1))}


def node_removal_demo(node):
    """固定虚构图的删点，不等于生物学敲除。"""
    import networkx as nx
    graph = nx.Graph([("NODE_A", "NODE_B"), ("NODE_B", "NODE_C"), ("NODE_B", "NODE_D"), ("NODE_D", "NODE_E")])
    if node not in graph:
        raise ValueError("请选择示意图中存在的节点。")
    baseline = {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "components": nx.number_connected_components(graph)}
    graph.remove_node(node)
    changed = {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "components": nx.number_connected_components(graph)}
    return baseline, changed


def render_advanced_course(key):
    import pandas as pd
    import streamlit as st
    course = ADVANCED_COURSES[key]
    st.subheader(course["title"])
    introductions = {
        "immune": "表达差异告诉我们哪些基因变了。这一节换个角度：看看免疫相关基因集合在样本中的整体表现。先选与问题匹配的签名，再看覆盖率，最后比较评分；ssGSEA给出的是相对富集，不是细胞比例。",
        "mr": "如果想进一步讨论因果方向，就要先审查遗传工具，而不是直接看一张OR图。我们从暴露与结局的定义开始，逐步核对独立性、效应单位和等位基因，再进入IVW计算。",
        "single_cell": "bulk数据看到的是组织平均信号。想知道哪些细胞参与、细胞之间可能如何交流，需要先准备单细胞表达和可靠注释，再选择通讯工具；这一节带你完成外部分析的准备与解读。",
        "perturbation": "删掉一个网络节点，与让细胞中的基因失活，是两件不同的事。先明确你想研究拓扑变化还是表达响应，再选择相应数据和方法；本页网络删点用于理解前者。",
    }
    st.write(introductions[key])
    with st.expander("方法范围与数据要求"):
        st.write(course["boundary"])
    for name, url in course["links"]:
        st.link_button(name, url)
    st.caption("按当前官方文档确认版本、输入和使用许可，再开始准备数据。")
    for i, (title, body) in enumerate(course["steps"]):
        with st.expander(title, expanded=i == 0):
            st.markdown(body)
    if key in ("immune", "mr"):
        with st.expander("实际操作：上传数据并计算"):
            from src.advanced_workspace import render_immune_analysis, render_mr_analysis
            if key == "immune":
                render_immune_analysis()
            else:
                render_mr_analysis()
    for name, fields in course["tables"].items():
        with st.expander("空表与字段 · " + name):
            st.dataframe(pd.DataFrame(fields, columns=["字段", "填写说明"]), hide_index=True, width="stretch")
            st.download_button("下载 · " + name, pd.DataFrame(columns=[key for key, _ in fields]).to_csv(index=False).encode("utf-8-sig"), name, "text/csv", key="advanced_" + name)
    if key == "mr":
        st.subheader("公式演示：协调方向错误会发生什么？")
        st.caption("模拟公式练习 · 3个虚构工具变量，假定独立、单位匹配；固定效应IVW忽略暴露估计误差。本练习不包含GWAS获取、LD处理、协调或工具有效性审核。")
        wrong = st.toggle("演示错误：将第二个结局beta方向反过来", key="mr_demo_wrong_direction")
        outcome = [0.05, -0.09 if wrong else 0.09, 0.07]
        result = ivw_formula_demo([0.1, 0.2, 0.15], outcome, [0.03, 0.04, 0.03])
        st.dataframe(pd.DataFrame({"instrument": ["DEMO_1", "DEMO_2", "DEMO_3"], "beta_exposure": [0.1, 0.2, 0.15], "beta_outcome": outcome, "se_outcome": [0.03, 0.04, 0.03]}), hide_index=True, width="stretch")
        cols = st.columns(3)
        cols[0].metric("示意IVW beta", f"{result['beta']:.3f}")
        cols[1].metric("示意固定效应SE", f"{result['se']:.3f}")
        cols[2].metric("示意异质性Q", f"{result['q']:.3f}")
        st.caption("这是固定数据的公式计算，不是实际协调算法；没有输出真实因果结论，也不能用Q是否显著来证明等位基因协调正确。")
    if key == "perturbation":
        st.subheader("虚构网络删点示意，不是细胞敲除预测")
        st.code("NODE_A — NODE_B — NODE_C\n             |\n           NODE_D — NODE_E", language="text")
        node = st.selectbox("删除哪个示意节点", ["NODE_A", "NODE_B", "NODE_C", "NODE_D", "NODE_E"], key="perturbation_demo_node")
        before, after = node_removal_demo(node)
        st.dataframe(pd.DataFrame([{"状态": "删点前", **before}, {"状态": "删点后", **after}]), hide_index=True, width="stretch")
        st.caption("结果解读：连通分量增加表示网络更分散。这是拓扑变化，不涉及真实表达、细胞死亡或药物疗效预测。")
    st.download_button("下载本分支教学操作单", _single_course_markdown(course).encode("utf-8-sig"), key + "_guide.md", "text/markdown", key="advanced_download_" + key)


def _single_course_markdown(course):
    parts = ["# " + course["title"], course["boundary"]]
    for title, body in course["steps"]:
        parts.extend(["## " + title, body])
    for name, fields in course["tables"].items():
        parts.extend(["## " + name, "\n".join(f"- {key}：{meaning}" for key, meaning in fields)])
    parts.append("\n".join(f"- [{name}]({url})" for name, url in course["links"]))
    return "\n\n".join(parts)
