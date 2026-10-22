"""可选转录组证据课程；仅提供设计核对练习，不冒充差异分析服务。"""

TRANSCRIPTOME_STEPS = [
    ("1. 先定义验证问题：患者数据不是复方治疗实验", """网络药理学产生候选后，可用合适的转录组资料检查其在疾病相关组织中的表达变化。先说明要比较的是患者vs对照、治疗前vs后，还是其他设计。

UC患者与健康对照的差异只能支持疾病相关表达线索，不能据此说五积散逆转了变化。没有复方干预组的数据就不能宣称验证了复方治疗效果。

预先确定研究物种、组织、疾病活动状态、药物使用、年龄范围与纳入标准；组织和临床情境不匹配的资料不能只因候选基因显著就纳入。

**交付**：研究问题、对比方向、纳入排除规则，以及发现集/验证集如何独立。后续机器学习与免疫分析按需要选择，不是核心网络流程的强制步骤。"""),
    ("2. GEO检索：看研究设计，不只看标题和样本数", """1. 在GEO DataSets用疾病英文名结合物种、组织和实验类型检索，例如Ulcerative colitis、Homo sapiens与相关组织词；核对论文与Series描述。
2. 打开GSE研究页，记录GPL平台、实验类型和样本GSM。GSE是研究编号，GSM是样本编号，GPL是平台，不要互相替代。
3. 阅读Overall design、样本Characteristics、处理流程和关联论文；逐个确认哪个样本是什么组、取自什么组织、是否配对或重复取材。
4. 区分生物学重复和同一材料的技术重复；多个活检来自同一患者时不能直接当作独立患者。记录subject_id，必要时联系作者或排除分组不明样本。
5. 在geo_dataset_register.csv记录为什么纳入/排除。找不到完整分组、目标组织或适用数据时，先记录缺口，不为了凑分析随意选一项研究。

**交付**：研究列表、论文/数据链接、样本级分组证据；不在没有实际查证时填造一个GSE编号。"""),
    ("3. 下载什么：表达、样本、注释各有作用", """**处理后表达矩阵**：查看Series Matrix或Supplementary files，确认数据是探针强度、已log2标准化矩阵、TPM/FPKM，还是原始基因计数。文件叫matrix不代表它们统计含义相同。

**样本资料**：保存GSE/GSM元数据、Characteristics和作者补充样本表，整理sample_metadata.csv。样本名称必须能一一对应表达矩阵列，不能只抄每组人数。

**基因/探针注释**：芯片通常需要对应GPL平台注释，保存probe→基因对应关系；RNA-seq确认Ensembl/Entrez等体系及参考版本，记录ID转换与多对多处理。

**原始测序数据**：SRA的FASTQ通常需要质控、比对/定量等较完整流程；若已有合格处理后计数，初学者不必一开始就下载全部FASTQ。原始芯片CEL等同样需要适用预处理。

**归档**：原样放raw/，记录文件名、来源、大小/校验值（能获得时）、日期与作者处理说明。working/存清洗数据，results/存分析输出，不覆盖原始文件。GEO可能包含受控或另有条款的数据，按许可使用。"""),
    ("4. 清洗和设计核对：按sample_id连接，禁止凭行号配组", """表达矩阵整理为基因/探针为行、样本为列，首列gene_id；sample_metadata至少包含sample_id、group，按研究设计补subject_id、batch、组织与协变量。

1. 检查矩阵列名是否唯一、分组表sample_id是否唯一、两侧样本集合是否一致；按名称重排分组表，不能因为行数相等就默认顺序正确。
2. 核对缺失值、重复基因/探针、数据类型、是否已log2和标准化。多个探针对应一个基因时预先制定合理汇总规则；多基因探针不直接复制为多个独立基因。
3. 看适当的分布图、样本相关性与PCA/聚类，结合原始质控判断异常。不能因为某个样本让结果不显著就删除它。
4. 明确病例/对照方向，例如log2FC定义为disease相对control；保留所有实际检验基因、过滤规则和设计矩阵。
5. 配对/重复测量纳入患者/配对结构；批次与组别完全重合时，数据不能可靠区分疾病效应与批次，不是加一个batch项就自动解决。

**交付**：清洗矩阵、按列名对齐后的样本表、注释映射、QC说明与分析设计。"""),
    ("5. 选分析路线：GEO2R、limma与DESeq2不是随便替换", """**网页路线**：若该Series及数据类型受GEO2R支持，可在GEO2R按样本建立组，核对转换/处理说明、分组和对比，再下载完整结果与方法记录。具体支持和算法以当前官方文档为准；复杂配对/批次设计不要默认网页已正确处理。

**芯片/适当连续表达矩阵**：在明确平台预处理和log2尺度后，可采用limma并设正确设计与contrast。不是看到小数矩阵就必然适合limma。

**RNA-seq基因原始计数**：常用DESeq2或edgeR，或经适当处理的limma-voom。标准计数输入应是适用的非负计数及对应分组；TPM、FPKM和log2值不能通过四舍五入变成DESeq2原始计数。转录本定量工具的估计计数需走tximport等适用流程。

**只有TPM/FPKM**：先尝试取得原始计数或明确合适的连续表达分析方案与局限，不硬套计数模型。数据类型未知时先查原文与处理说明，不自动猜测并运行。

无论哪条路线，保存完整检验表、效应方向、P值、BH/FDR、过滤和模型参数。本步骤下方可用已标准化log2表达执行独立两组Welch t检验及BH校正；不替代limma收缩估计、DESeq2计数模型或配对/批次模型。"""),
    ("6. 如何与候选基因衔接：报告效应和不确定性", """差异输出建议保留gene_symbol、log2fc、p_value、p_adjust、dataset、contrast与可用的表达/QC信息；阈值需预先说明，不能只看P值忽略效应。

将网络候选基因与完整差异结果按统一基因ID连接，区分：可检测且有差异、可检测但无充分差异证据、未检测/未映射。无显著差异不等于该基因没有作用，未检测也不是表达为0。

使用差异基因做GO/KEGG时，背景回到实际通过过滤并被检验的基因，必要时按方向分别分析并说明检验范围。使用同一表达数据的差异、富集、免疫评分与机器学习不能当作四次独立验证。

**交付**：完整差异表、候选基因证据表、QC和方法记录。本站「五积散案例→转录组验证」用于已有案例结果解读，不代表已分析新上传数据。"""),
    ("7. 后续选哪条分支：按问题而非模块数量", """- **机器学习**：回答表达是否能帮助预测分组。表达与标签可作为起点，但训练/测试按独立患者分开，标准化和特征选择仅在训练流程内拟合，尽量保留独立队列验证。不能先在全部数据筛基因再宣称完全独立测试。
- **免疫微环境**：在适用bulk表达数据上选择ssGSEA或去卷积等方法，并核对输入尺度、基因覆盖与签名。ssGSEA是相对富集分数，不直接等于细胞比例。它是疾病环境线索，不自动证明候选基因调控免疫细胞。
- **MR**：需要独立的GWAS暴露/结局汇总数据、等位基因与工具变量审核，不从表达矩阵直接“转换”得到。
- **细胞通讯**：通常需要单细胞表达、细胞类型注释和配体受体库；bulk矩阵不直接替代。计算扰动也需匹配其模型和数据要求。

**选择原则**：只做能回答研究问题且资料满足要求的分支，写明证据来源和当前平台能力。机器学习、ssGSEA与有限输入的MR计算已在对应课程接入；细胞通讯与真实表达扰动仍使用外部方法。"""),
]

TRANSCRIPTOME_FIELDS = {
    "geo_dataset_register.csv": [
        ("dataset", "真实GSE编号"), ("platform", "GPL与平台类型"), ("species", "研究物种"), ("tissue", "组织/细胞来源"),
        ("study_question", "疾病/治疗等实际对比"), ("data_type", "芯片/原始计数/TPM/FPKM等"), ("processing", "原文归一化与转换"),
        ("subject_count", "独立受试者数"), ("sample_count", "样本数，不能替代患者数"), ("group_definition", "组别定义及方向"),
        ("included", "yes/no/pending"), ("decision_reason", "取舍依据"), ("reference_url", "论文和记录链接"),
        ("download_date", "下载日期"), ("raw_file", "原始文件路径"),
    ],
    "sample_metadata.csv": [
        ("sample_id", "与表达矩阵列名完全对应"), ("group", "如control/disease，按实际研究定义"),
        ("subject_id", "患者/生物学个体ID"), ("batch", "已知批次，不猜测"), ("tissue", "样本组织"),
        ("pair_id", "配对标识，非配对留空"), ("included", "yes/no/pending"), ("decision_reason", "QC/分组纳入依据"),
        ("reference_url", "GSM/样本表等分组出处"),
    ],
    "gene_annotation_register.csv": [
        ("original_gene_id", "原探针或基因ID"), ("original_id_type", "Probe/Ensembl/Entrez等"),
        ("gene_symbol", "审核后的主基因符号"), ("species", "物种"), ("annotation_version", "GPL/参考基因组/资源版本"),
        ("mapping_status", "mapped/unmapped/ambiguous等"), ("aggregation_rule", "多探针/多ID的处理规则"),
        ("included", "yes/no/pending"), ("reference_url", "注释出处"),
    ],
    "transcriptome_run_register.csv": [
        ("run_id", "分析编号"), ("dataset", "研究编号"), ("expression_file", "实际输入矩阵路径"), ("metadata_file", "样本表路径"),
        ("data_type", "原始计数/已log2芯片等"), ("preprocessing", "过滤、归一化与转换"),
        ("software_version", "方法、软件和版本"), ("design", "组别/配对/批次/协变量设计"),
        ("contrast", "比较方向"), ("effect_threshold", "效应阈值及理由"), ("fdr_method", "实际校正方法"),
        ("fdr_cutoff", "校正阈值"), ("tested_gene_count", "实际检验基因数"), ("run_date", "运行日期"),
        ("limitations", "混杂、样本量、注释损失等"),
    ],
    "expression_matrix_template.csv": [
        ("gene_id", "每行一个审核后特征；不是把所有基因写同一格"),
        ("SAMPLE_A", "示意样本列，替换为实际样本ID，数值尺度需明确"),
        ("SAMPLE_B", "示意样本列，实际多少样本就多少列"),
    ],
}


def align_sample_metadata(expression_sample_ids, metadata):
    """严格核对样本集合并按矩阵列名排序；不执行统计模型或ID映射。"""
    import pandas as pd
    samples = list(expression_sample_ids)
    if not samples or any(pd.isna(value) or not isinstance(value, str) or not value.strip() for value in samples):
        raise ValueError("表达矩阵样本名不能为空，且必须为文本。")
    if len(samples) != len(set(samples)):
        raise ValueError("表达矩阵样本列名重复，需先核查样本身份。")
    if not {"sample_id", "group"} <= set(metadata.columns):
        raise ValueError("样本表至少需要sample_id、group。")
    if metadata[["sample_id", "group"]].isna().any().any():
        raise ValueError("样本ID或分组为空，不能默认为某一组。")
    if any(not isinstance(value, str) or not value.strip() for value in metadata["sample_id"]):
        raise ValueError("样本ID必须为非空文本。")
    if metadata["group"].astype(str).str.strip().eq("").any():
        raise ValueError("样本分组不能为空。")
    if metadata["sample_id"].duplicated().any():
        raise ValueError("样本表sample_id重复，不能自动取第一条。")
    missing = sorted(set(samples) - set(metadata["sample_id"]))
    extra = sorted(set(metadata["sample_id"]) - set(samples))
    if missing or extra:
        raise ValueError(f"样本集合不一致：表达侧缺分组{missing}；分组侧多出{extra}。请回查，不自动丢弃。")
    return metadata.set_index("sample_id").loc[samples].reset_index()


def transcriptome_markdown():
    parts = ["# 可选转录组证据：GEO资料到分析设计", "本课程第5步支持独立两组、已标准化log2表达的Welch差异检验与BH校正；原始计数、配对和批次模型仍按外部路线执行。"]
    for title, body in TRANSCRIPTOME_STEPS:
        parts.extend(["## " + title, body])
    for filename, fields in TRANSCRIPTOME_FIELDS.items():
        parts.extend(["## " + filename, "| 字段 | 含义 |\n| --- | --- |\n" + "\n".join(f"| {key} | {meaning} |" for key, meaning in fields)])
    return "\n\n".join(parts)


def render_transcriptome_guide():
    import pandas as pd
    import streamlit as st

    st.subheader("可选扩展：转录组资料与设计核对")
    st.info("第5步可以上传已标准化log2表达，完成独立两组差异分析并接着做富集。GEO疾病数据提供疾病表达证据，复方治疗效应需要对应干预数据。")
    for name, url in [("GEO DataSets", "https://www.ncbi.nlm.nih.gov/gds/"), ("GEO2R官方说明", "https://www.ncbi.nlm.nih.gov/geo/info/geo2r.html"), ("limma", "https://bioconductor.org/packages/limma/"), ("DESeq2", "https://bioconductor.org/packages/DESeq2/"), ("edgeR", "https://bioconductor.org/packages/edgeR/")]:
        st.link_button(name, url)
    st.caption("链接为官方学习入口；本页不宣称已验证每项当前检索/下载界面。按许可获取数据，不能补造缺失分组。")
    for i, (title, body) in enumerate(TRANSCRIPTOME_STEPS):
        with st.expander(title, expanded=i == 0):
            st.markdown(body)
            if i == 4:
                from src.expression_workspace import render_expression_analysis
                render_expression_analysis()
    st.subheader("转录组资料空表与字段")
    for filename, fields in TRANSCRIPTOME_FIELDS.items():
        with st.expander(filename):
            st.dataframe(pd.DataFrame(fields, columns=["字段", "填写说明"]), hide_index=True, width="stretch")
            st.download_button("下载空表 · " + filename, pd.DataFrame(columns=[key for key, _ in fields]).to_csv(index=False).encode("utf-8-sig"), filename, "text/csv", key="tx_guide_" + filename)
    st.subheader("练习：同样是4个样本，分组就一定配得上吗？")
    st.caption("以下S1–S4及表达值完全虚构，仅演示按名称对齐，不是真实GEO数据或差异表达结果。")
    expression = pd.DataFrame({"gene_id": ["DEMO_GENE_A", "DEMO_GENE_B"], "S1": [10, 12], "S2": [15, 13], "S3": [25, 18], "S4": [30, 22]})
    st.dataframe(expression, hide_index=True, width="stretch")
    mode = st.radio("选择样本表情形", ["顺序打乱但ID完整", "样本数相同但ID不一致", "同一ID重复"], key="tx_guide_mode")
    ids = ["S3", "S1", "S4", "S2"]
    if mode == "样本数相同但ID不一致":
        ids[-1] = "S5"
    elif mode == "同一ID重复":
        ids[-1] = "S1"
    metadata = pd.DataFrame({"sample_id": ids, "group": ["disease", "control", "disease", "control"]})
    st.dataframe(metadata, hide_index=True, width="stretch")
    try:
        aligned = align_sample_metadata(list(expression.columns[1:]), metadata)
        st.success("样本集合一致，已按表达矩阵列名重新排序。注意：这不代表临床分组、配对或统计设计已被核实。")
        st.dataframe(aligned, hide_index=True, width="stretch")
    except ValueError as error:
        st.error(str(error))
    st.download_button("下载转录组资料与设计完整操作单（Markdown）", transcriptome_markdown().encode("utf-8-sig"), "transcriptome_design_guide.md", "text/markdown", key="tx_guide_full")
