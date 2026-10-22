"""疾病资料收集课程与不改写生物学ID的集合交集练习。"""

DISEASE_STEPS = [
    ("1. 先确认疾病实体，不急着下载基因", """**准备**：疾病中文/英文名、同义名、研究物种、研究范围和上一节的药物靶点清单。

以溃疡性结肠炎为例，可以从Ulcerative colitis开始检索；Inflammatory bowel disease是更广的概念，Crohn disease不是同一疾病。数据库返回的父级疾病、亚型、症状或并发症不能未经说明混入。

**怎么做**：先建立disease_query_register.csv；每个数据库分别记录关键词、匹配到的疾病名称、带命名空间的疾病ID、纳入决定和理由。不同来源的ID不一定相同，不能只按数字匹配。

**应保存**：疾病实体记录链接/可许可保存的检索记录、查询日期和疾病定义。无法确定映射时标pending，不勉强合并。"""),
    ("2. 选择数据库：每个来源收什么、怎样留存", """**GeneCards路线**：从官网疾病相关检索/关联入口按准确英文名称检索，确认关联的是研究疾病，而不是任意全文提及。保留官方显示的基因符号、疾病名称、Relevance score等原始字段、记录链接和日期。具体检索、列表和导出能力依当前界面与许可；没有相关字段时不能自行编造。不能把相关性分数解释为患病概率。

**DISGENET路线**：先匹配疾病实体，再取得允许访问的疾病—基因关联列表。保留疾病ID、基因原始ID/符号、原始评分及其字段定义、证据来源/类型和可获得的文献。账户、版本和授权不同可能影响字段与导出；保存原始导出，不只抄筛后的基因名。

**OMIM路线**：检索表型/疾病记录并核对描述；重点提取明确的基因—表型关联与文献依据。检索命中一个记录不等于该记录中所有提及的基因都与本疾病存在已确认关联。它侧重遗传病/表型，不是所有复杂病完整基因集的替代品。

**文献路线**：PubMed检索准确疾病名与gene等关键词，先明确纳入标准；保存PMID/DOI、研究对象、实验/关联类型和基因。不要把综述里的推测自动算作实验支持。

**下载什么**：优先按许可下载完整可用关联CSV/TSV/Excel与字段说明；无导出时只按条款手工整理并标明出处。不绕过登录、验证码或付费限制。不必为凑来源数把所有库都用上。"""),
    ("3. 保留长表：一条基因—疾病—来源/证据一行", """把各来源整理进disease_gene_evidence.csv，先保存原始ID和原始评分，再映射为统一ID。

- 同一基因来自两份数据库，保留两行；同一基因来自多个文献，保留文献明细。基因清单才在最后去重。
- gene_symbol只存核对后的主符号，别名放original_gene_id或备注；Entrez/Ensembl等ID需按体系和物种映射，不直接当基因符号。
- species/taxon_id指关联证据对应的物种，动物模型不自动改写成人类基因。
- 记录source_db、source_version、query_date、raw_file与reference_url。版本不可获得时写明未报告，不自行填一个版本。

**应保存**：各库原始下载 + 未筛选证据长表 + ID映射/未映射清单。数据库在之后更新不影响你追溯本次实际使用的数据。"""),
    ("4. 按来源筛选，不把分数混成同一尺度", """分析前为每个来源分别写规则，例如明确证据类型/疾病精确匹配/物种限制，或基于来源文档选择评分门槛；记录依据、筛选前后基因数与证据行数。

没有适用于所有疾病的统一GeneCards阈值；“高于中位数”只是相对筛选方案，不是通用质量标准。GeneCards的分数不能直接与DISGENET的分数取平均、相加或共用一个阈值。

将included标为yes/no/pending，并记录decision_reason。无评分记录不是0分，缺失值不能伪造。低分或未纳入记录保留在工作表中，不从原始文件删除。

**多来源整合**：并集提高覆盖面，所有来源交集更严格但可能严重漏检；至少k来源支持可以作为另一种预先约定的方案。报告实际查询的来源集合与每个基因的来源清单。重复证据行不等于多个独立来源，不同库也可能引用同一论文。"""),
    ("5. 求交集：传统工具与本站练习都要先统一ID", """**输入**：已审核药物靶点集D、已审核疾病基因集S。两侧物种与ID体系必须一致；交集不能完成UniProt映射、别名修正或跨物种转换。

**Excel路线**：分别把审核通过的gene_symbol放入两张表A列，去空值、首尾空格并去重。药物表B2可用`=IF(COUNTIF(疾病表!$A$2:$A$10000,A2)>0,"共同","仅药物")`，向下填充，筛选“共同”。范围须覆盖实际数据；COUNTIF通常不区分大小写，大小写有意义时改用适当脚本精确匹配。不要把公式当成身份审核。

**Python路线**：在确认ID后做`common = sorted(drug_set & disease_set)`；同时保留`drug_set - disease_set`和`disease_set - drug_set`帮助发现问题。

**本站路线**：本页下方可以粘贴两份每行一个的基因清单，现场去空行/首尾空格、去重并按大小写精确匹配。不会自动按物种映射，也不猜测多列文件或按逗号拆分。

**质量检查**：共同基因数≤两侧较小集合数；并集数=药物基因数+疾病基因数−交集数。交集为空先查ID、物种和筛选规则，不为了出现交集而改名或降阈值。"""),
    ("6. 交付给STRING，并保留证据审计链", """**下游文件**：共同基因清单common_targets.txt每行一个、无标题，供STRING Multiple proteins输入；仍需在STRING明确物种并核对映射。不能把两侧并集或某一侧原始列表误当共同靶点。

**研究归档**：保留疾病查询登记、疾病证据长表、审核决定、来源集合规则、两侧最终基因清单、交集/独有集及数量记录。用gene_symbol把交集关联回药物成分关系与疾病证据长表，回查每个共同靶点由什么资料支持，不用行号拼表。

**本站项目管理**：当前基础疾病表disease_genes.csv至少需要gene_symbol、disease_name；药物候选表compound_targets.csv至少需要formula_name、herb_name、gene_symbol。只能从审核纳入数据转换，并以项目管理中的当前模板为准。详细证据表另外归档；下方纯清单练习不写入任何项目。

**解释边界**：交集表示在当前资料与规则下同时入选的候选基因，不是疗效证明、因果结论或“已验证治疗靶点”。若用差异表达作为疾病线索，应另行说明GEO数据、分组、质控、差异分析和FDR规则，不把表达变化自动等同致病作用。"""),
]

DISEASE_TABLES = {
    "disease_query_register.csv": [
        ("query_terms", "实际检索词"), ("source_db", "来源数据库/文献库"), ("source_version", "版本或未报告"),
        ("matched_disease_name", "命中的疾病实体名"), ("disease_id", "带命名空间的疾病ID"),
        ("species", "目标物种"), ("included", "yes/no/pending"), ("decision_reason", "实体纳入/排除依据"),
        ("query_date", "实际检索日期YYYY-MM-DD"), ("reference_url", "疾病实体或检索记录链接"), ("raw_file", "原始资料路径"),
    ],
    "disease_gene_evidence.csv": [
        ("disease_name", "确认的疾病名"), ("disease_id", "带命名空间的来源疾病ID"),
        ("original_gene_id", "原始基因/蛋白ID"), ("original_id_type", "原始ID体系"),
        ("gene_symbol", "审核后的主基因符号，未确认留空"), ("species", "证据物种"), ("taxon_id", "分类号"),
        ("source_db", "来源数据库/原始文献"), ("source_version", "版本或未报告"),
        ("score_name", "原始评分字段名称"), ("evidence_score", "原始评分，缺失留空"),
        ("evidence_type", "实验/遗传关联/文本/数据库关联/未知等，按原始证据记录"),
        ("reference_url", "支持关系的记录链接/PMID/DOI"), ("query_date", "实际检索日期"),
        ("raw_file", "原始下载文件路径"), ("mapping_status", "mapped/unmapped/ambiguous/wrong_species/pending"),
        ("included", "yes/no/pending"), ("decision_reason", "纳入、排除或待核理由"),
        ("screening_rule_id", "关联本来源筛选方案"),
    ],
    "disease_source_rules.csv": [
        ("screening_rule_id", "规则唯一编号"), ("source_db", "适用来源"), ("disease_scope", "精确疾病/亚型等范围"),
        ("species", "纳入物种"), ("id_system", "最终统一ID体系"),
        ("score_rule", "评分条件或无评分筛选"), ("evidence_rule", "证据纳入规则"), ("rationale", "文档/研究依据"),
        ("rows_before", "原始证据行数"), ("rows_after", "纳入证据行数"),
        ("genes_before", "标准化后筛选前唯一基因数"), ("genes_after", "最终纳入唯一基因数"),
        ("source_merge_rule", "并集/所有指定来源交集/至少k来源；注明来源集合与k"),
    ],
}


def intersect_gene_lists(drug_text, disease_text):
    """每行一个ID，保留大小写；拒绝疑似多列/分隔符，不伪装成ID映射。"""
    def parse(value):
        lines = [line.strip() for line in value.splitlines() if line.strip()]
        if not lines:
            raise ValueError("两侧都需要至少一个已审核的基因。")
        if any(any(char.isspace() or char in ",;，；" for char in line) for line in lines):
            raise ValueError("请每行只放一个基因ID，不要表头、逗号列表或多列表格。")
        if any(line.lower() in {"gene", "gene_symbol", "symbol", "基因", "基因符号"} for line in lines):
            raise ValueError("请删除表头，仅保留每行一个基因ID。")
        unique = set(lines)
        return unique, len(lines) - len(unique)
    drug, drug_duplicates = parse(drug_text)
    disease, disease_duplicates = parse(disease_text)
    return {
        "common": sorted(drug & disease), "drug_only": sorted(drug - disease),
        "disease_only": sorted(disease - drug), "drug_count": len(drug), "disease_count": len(disease),
        "union_count": len(drug | disease), "drug_duplicates": drug_duplicates,
        "disease_duplicates": disease_duplicates,
    }


def disease_markdown():
    parts = ["# 疾病基因收集与交集：操作单", "数据库界面、字段与许可可能变化；本指南不代表已逐个验证当前下载流程。"]
    for title, body in DISEASE_STEPS:
        parts.extend(["## " + title, body])
    for filename, fields in DISEASE_TABLES.items():
        parts.extend(["## " + filename, "| 字段 | 含义 |\n| --- | --- |\n" + "\n".join(f"| {key} | {meaning} |" for key, meaning in fields)])
    return "\n\n".join(parts)


def render_disease_guide():
    import pandas as pd
    import streamlit as st

    st.subheader("疾病基因收集 → 交集 → STRING")
    st.write("药物侧清单已经准备好，接下来补齐疾病侧。先确认数据库里的疾病是不是你要研究的那一个，再记录来源和筛选条件。两侧物种、ID统一后，就能在本页求交集。外部检索和筛选依据由你完成。")
    for name, url in [("GeneCards", "https://www.genecards.org/"), ("DISGENET", "https://disgenet.com/"), ("OMIM", "https://omim.org/"), ("PubMed", "https://pubmed.ncbi.nlm.nih.gov/")]:
        st.link_button(name + " 官方入口", url)
    st.caption("以下按数据任务说明操作，具体菜单、字段和下载权限以当前官方文档为准；无法访问时记录替代来源，不绕过访问限制。")
    for i, (title, body) in enumerate(DISEASE_STEPS):
        with st.expander(title, expanded=i == 0):
            st.markdown(body)
            from src.case_companion import render_case_step
            render_case_step("disease", i)
    st.subheader("疾病资料工作表与字段")
    for filename, fields in DISEASE_TABLES.items():
        with st.expander(filename):
            st.dataframe(pd.DataFrame(fields, columns=["字段", "填写说明"]), hide_index=True, width="stretch")
            st.download_button("下载空表 · " + filename, pd.DataFrame(columns=[key for key, _ in fields]).to_csv(index=False).encode("utf-8-sig"), filename, "text/csv", key="disease_" + filename)
    st.caption("证据表一行一条来源/文献支持，不把多库评分挤到同一个数值。空模板不是数据库结果，缺失字段留空并备注。")
    st.subheader("现场练习：两个已审核基因集求交集")
    st.caption("示意清单只演示集合运算，不是五积散或任何疾病的真实证据。请用自己的已审核清单替换；不会修改项目文件。")
    left, right = st.columns(2)
    drug = left.text_area("药物靶点（每行一个、无表头）", "TNF\nIL6\nAKT1\nTNF", key="disease_practice_drug")
    disease = right.text_area("疾病基因（每行一个、无表头）", "IL6\nAKT1\nSTAT3", key="disease_practice_genes")
    confirmed = st.checkbox("我已确认两侧使用同一物种、同一ID体系；本练习不执行ID映射", key="disease_practice_confirm")
    if not confirmed:
        st.info("核对物种与ID后勾选确认，即可计算。")
        return
    # 每次输入变化立即重算，避免旧结果被误认为来自新清单。
    try:
        if len(drug) + len(disease) > 2_000_000:
            raise ValueError("教学粘贴练习限两侧合计200万字符；更大清单请用本地脚本。")
        result = intersect_gene_lists(drug, disease)
    except ValueError as error:
        st.error(str(error))
        return
    cols = st.columns(4)
    for column, label, key in zip(cols, ["药物基因", "疾病基因", "共同基因", "并集基因"], ["drug_count", "disease_count", "common", "union_count"]):
        column.metric(label, len(result[key]) if key == "common" else result[key])
    st.caption(f"已去除重复ID：药物侧{result['drug_duplicates']}条，疾病侧{result['disease_duplicates']}条。精确区分大小写，不自动修正别名。")
    if not result["common"]:
        st.warning("没有共同基因；请先核对ID体系、物种和筛选规则。空交集不表示必须放宽规则。")
    for key, label, filename in [("common", "共同基因", "common_targets.txt"), ("drug_only", "仅药物侧", "drug_only_genes.txt"), ("disease_only", "仅疾病侧", "disease_only_genes.txt")]:
        with st.expander(label):
            st.dataframe(pd.DataFrame({"gene_symbol": result[key]}), hide_index=True, width="stretch")
            st.download_button("下载 · " + filename, ("\n".join(result[key]) + ("\n" if result[key] else "")).encode("utf-8"), filename, "text/plain", key="disease_result_" + key)
    st.download_button("下载本次集合计算记录", ("# 集合交集练习\n\n两侧物种与ID一致性由使用者确认；未执行数据库或证据核验。\n\n" + "\n".join(f"- {key}: {len(value) if isinstance(value, list) else value}" for key, value in result.items()) + "\n\n共同基因是候选集合，不是已验证治疗靶点。\n").encode("utf-8-sig"), "intersection_record.md", "text/markdown", key="disease_result_record")


def render_disease_download():
    import streamlit as st
    st.download_button("下载疾病基因收集与交集操作单（Markdown）", disease_markdown().encode("utf-8-sig"), "disease_to_intersection_guide.md", "text/markdown", key="disease_full_guide")
