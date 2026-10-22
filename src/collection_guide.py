"""资料检索到UniProt的可下载教学操作单，不调用或抓取外部数据库。"""

COLLECTION_STEPS = [
    {
        "title": "A. 确认处方与药材：先知道自己要查什么",
        "need": "处方出处、每味药材的规范名/别名、基原、药用部位、炮制与剂量。不是先随便搜一组化合物。",
        "where": "优先核对药典、处方原始文献或有出处的论文；PubMed可补充检索。TCMSP/HERB/ETCM用于后续成分查询，不替代处方出处。",
        "actions": """1. 先记下研究复方、疾病和研究物种，确认使用的是哪一个处方版本。
2. 按处方逐味抄录原始名称，再填写规范药名、别名、基原及炮制。暂时确认不了的项目写入备注。
3. 保存可合法获取的文献原文/补充表或引文记录；记录页码、DOI/PMID或出处。不要把无来源的网页配方当成已核实处方。""",
        "save": "原始处方文献/引文记录；整理得到 herb_register.csv。每行一味处方药材，用本项目herb_id串联后续表。",
        "table": "herb_register.csv",
        "check": "药材同名不等于同一基原；生品和炮制品不要自动合并。原文未报告剂量或基原时留空并注明，不补造。",
        "links": [("PubMed", "https://pubmed.ncbi.nlm.nih.gov/")],
    },
    {
        "title": "B. 查药材成分：下载成分资料，而不是只有药名",
        "need": "每味药材有哪些候选成分，以及成分ID、名称、来源和可用筛选属性。",
        "where": "TCMSP、HERB、ETCM可选一种作起点，再用其他资源或原始文献补充。各库覆盖面和证据不同，不要求每个库都查，也不能假定都有OB/DL。",
        "actions": """1. 用规范药名检索，再用别名或拉丁名补充；打开匹配记录，核对物种/基原与药用部位。
2. 找成分列表及其关联信息。若该库提供合规导出，保存原始CSV/TSV/Excel或补充表；无导出时按许可手工整理并保存记录URL，不绕过登录、验证码或付费限制。
3. 保留该库的成分ID和名称，建立项目内部compound_key。不同库的ID不直接视为同一成分，要核对结构/可靠标识。
4. 把OB、DL等源数据原样保留；缺失值留空。另设included与exclusion_reason记录是否纳入及理由，先保存全量原始结果再筛选。
5. OB≥30%、DL≥0.18只是部分研究的约定；若采用，写清依据。缺少这两个字段的其他数据库不能强套这套筛选。""",
        "save": "每味药材的原始成分导出文件 + herb_compounds.csv；每行一个药材—成分—来源记录。同一成分来自两味药时保留两条关系。",
        "table": "herb_compounds.csv",
        "check": "必须能从compound_key回查到数据库成分ID、药材和原始文件。数据库关联不等于实测含量或体内暴露。",
        "links": [("TCMSP", "https://tcmsp-e.com/"), ("HERB", "https://herb.ac.cn/"), ("ETCM", "http://www.tcmip.cn/ETCM/")],
    },
    {
        "title": "C. 核对化合物结构：PubChem不是靶点预测结果",
        "need": "成分的可靠身份：PubChem CID、结构、同义名；只有需要结构预测时才准备SMILES/SDF。",
        "where": "PubChem的Compound检索；找不到准确结构时回到原库或原始文献，不按相似名字随便选。",
        "actions": """1. 用成分名称或已有CID检索PubChem，核对同义名、分子式及结构；特别检查立体异构、盐型和苷/苷元是否混淆。
2. 保存CID和记录URL。若后续工具使用SMILES，保留实际提交的完整字符串及其结构类型；需要SDF时按工具要求下载结构文件。
3. 记录映射为exact、ambiguous或not_found；不确定的候选先不进入结构预测。查不到CID不代表成分不存在。
4. 不需要结构预测时无需下载整库或所有3D构象。PubChem身份记录本身不证明该成分作用于某靶点。""",
        "save": "compound_identity.csv；必要时保存每个实际提交结构的SMILES/SDF原件。每行一条原库成分到候选结构的映射。",
        "table": "compound_identity.csv",
        "check": "映射不唯一时保留多个候选并标记待复核，不静默取第一条。来源中的结构与实际提交结构都要可追溯。",
        "links": [("PubChem", "https://pubchem.ncbi.nlm.nih.gov/")],
    },
    {
        "title": "D. 找成分靶点：实验、数据库关联与预测要分开",
        "need": "成分—候选蛋白靶点关系，尤其是靶点原始标识、标识类型、物种和证据。不要只保存一列蛋白名。",
        "where": "路线1：TCMSP/HERB/ETCM已有成分关联；路线2：文献中的实验支持关系；路线3：有可靠结构时选择SwissTargetPrediction等工具生成预测假设。",
        "actions": """1. 在已确认的成分记录中查看靶点/证据，按许可保存关系表及关联文献；不要把药材层面的靶点直接分配给它的全部成分。
2. 保存数据库原样返回的target_id与target_name，并判断ID属于UniProt accession、Entrez Gene、Ensembl、STRING还是只有名称。未知类型填unknown。
3. 记录靶点物种。天然产物来源物种不等于预测靶点物种；人类疾病研究通常核对Homo sapiens（9606），其他物种证据不可悄悄改成人类。
4. 若做结构预测：逐个提交经核对的SMILES，选择目标物种，保存输入结构、完整可下载预测结果、预测分数、筛选规则和运行日期。概率不是疗效或实验验证。
5. evidence_type分别标记experimental、predicted、database_association或unknown，并记录supporting_reference。每条关系/来源单独一行，分数只在相同来源尺度内解释。""",
        "save": "原始靶点关系/预测结果 + compound_targets_raw.csv。此时gene_symbol可以还没确定；不要覆盖原始ID。",
        "table": "compound_targets_raw.csv",
        "check": "实验支持须核对原文和实验对象；若原库不说明证据类型，标unknown而非experimental。映射到UniProt只解决身份，不提升证据等级。",
        "links": [("SwissTargetPrediction", "http://www.swisstargetprediction.ch/"), ("PubMed", "https://pubmed.ncbi.nlm.nih.gov/")],
    },
    {
        "title": "E. 整理UniProt输入：按ID类型分批，不混着粘贴",
        "need": "从原始关系表抽出的靶点ID列表、输入ID体系和目标物种。UniProt不需要药材名、CID或SMILES来完成蛋白ID映射。",
        "where": "UniProt ID Mapping用于支持的ID体系；只有蛋白名称时使用UniProtKB检索并人工确认身份。",
        "actions": """1. 先按original_id_type和species分组；在各组内去掉ID首尾空格和空值、对待查询ID去重。原始关系表不删，查询列表去重不代表丢弃成分关系。
2. 每批保存一个纯文本清单：每行一个ID、无标题、无逗号、无药名。文件名说明ID类型和物种，例如uniprot_accession_9606.txt。
3. 只有TNF这类基因符号时，先按符号加物种检索UniProtKB并核对Gene Names，再确认蛋白条目；不要把符号谎称为UniProt accession。
4. 只有蛋白名称时用名称+物种检索，结合原文/原库描述核对，候选多时留待复核；数据库内部ID若不被ID Mapping支持，先查原库交叉引用。
5. 有明确的UniProt accession也要核对条目当前状态、物种和主基因名；“已是UniProt ID”不等于无需审核。""",
        "save": "各ID类型/物种的输入.txt清单 + 查询批次登记；compound_targets_raw.csv保留全部成分—靶点来源关系。",
        "table": "id_mapping_register.csv",
        "check": "不把蛋白名、基因符号、成分CID与蛋白accession混在同一批。物种不明的项目先核查，不能当人类处理。",
        "links": [("UniProt ID Mapping", "https://www.uniprot.org/id-mapping"), ("UniProtKB", "https://www.uniprot.org/uniprotkb")],
    },
    {
        "title": "F. 下载映射并回填：最终交付关系表和基因清单",
        "need": "原始ID→UniProt条目→标准基因符号的映射，以及未映射、一对多和排除项。",
        "where": "UniProt ID Mapping结果与UniProtKB条目。字段/菜单随版本变化，以官方说明为准。",
        "actions": """1. 在ID Mapping选择正确的From体系，输出到可用的UniProtKB体系；粘贴/上传对应批次，保留任务信息与运行日期。
2. 如界面提供物种约束可先设置；仍需在结果中按Organism/Organism ID核对，不假定每种映射都提供相同筛选项。
3. 下载带From/To对应关系的TSV等表格；按可用列保留Entry（accession）、Entry Name、Protein names、Gene Names (primary)、Organism/Organism ID及Reviewed状态。同时保存未映射清单；若任务页未提供，按本批输入减去成功映射的From补出。
4. 不要把Gene Names整串别名塞进gene_symbol。核对主基因符号；缺少主基因名时留空并注明。Reviewed是审核状态，不是该成分—靶点关系已经实验证实。
5. 把每个候选映射单独存一行：mapped、unmapped、ambiguous、wrong_species等状态需明确；一对多先保留所有候选，人工确定是否纳入及理由，不自动取第一条。
6. 用original_id + original_id_type + species把审核后的映射关联回原始成分—靶点表，允许一对多展开并检查行数变化。不能靠行号或仅凭名称复制粘贴。
7. 输出compound_targets_standardized.csv保留全部审核明细；从included=yes且映射通过的行抽出gene_symbol去重，形成drug_target_genes.txt（每行一个、无标题），供后续疾病交集。""",
        "save": "UniProt原始映射TSV、未映射.txt、id_mapping_register.csv、compound_targets_standardized.csv与drug_target_genes.txt。记录输入ID数、映射成功ID数、未映射/歧义数及最终基因数；口径不同不能混报。",
        "table": "compound_targets_standardized.csv",
        "check": "去重后的靶点基因数通常不等于关系行数。最终每个基因必须能追溯到成分、药材、数据库/文献及人工审核决定。",
        "links": [("ID Mapping官方帮助", "https://www.uniprot.org/help/id_mapping"), ("UniProt下载帮助", "https://www.uniprot.org/help/downloads")],
    },
]

# 每项：(文件名, 行粒度, [(字段, 中文解释, 示例值)])。示例不构成药材—成分—靶点证据。
TABLE_SCHEMAS = [
    ("herb_register.csv", "一行一味处方药材", [
        ("herb_id", "项目内唯一药材编号", "H001"), ("formula_name", "复方名称与版本", "示例复方A"),
        ("original_herb_name", "处方原始药名", "示例药材甲"), ("herb_name", "核对后的规范药名", "示例药材甲"),
        ("latin_name", "核实的基原拉丁名，未知留空", ""), ("medicinal_part", "药用部位", ""),
        ("processing", "炮制情况", "待核对"), ("dose", "原文剂量与单位，未知留空", ""),
        ("reference_url", "文献DOI/PMID/URL或出处页码", "教学占位，待填真实出处"), ("notes", "别名、疑问与版本说明", "仅示例，不用于分析"),
    ]),
    ("herb_compounds.csv", "一行一条药材—成分—来源记录", [
        ("herb_id", "关联药材表", "H001"), ("compound_key", "项目内成分唯一键，核对身份后分配", "C001"),
        ("source_compound_id", "来源数据库的成分ID", "DEMO-C01"), ("compound_name", "原始成分名称", "示例成分甲"),
        ("ob", "源库报告的OB，缺失留空", ""), ("dl", "源库报告的DL，缺失留空", ""),
        ("included", "yes/no/pending", "pending"), ("exclusion_reason", "排除理由或待核事项", "待核对结构"),
        ("source_db", "数据库/文献来源", "教学占位库"), ("source_record_url", "具体记录链接，不只是首页", ""),
        ("query_date", "实际检索日期YYYY-MM-DD", ""), ("raw_file", "原始导出文件相对路径", "raw/herb_compounds_original.tsv"),
    ]),
    ("compound_identity.csv", "一行一个原始成分到候选结构的映射", [
        ("compound_key", "关联项目成分", "C001"), ("source_db", "原成分来源", "教学占位库"),
        ("source_compound_id", "原库成分ID", "DEMO-C01"), ("pubchem_cid", "核对后的CID，未知留空", ""),
        ("smiles", "实际使用的结构字符串", ""), ("structure_type", "结构类型/盐型/立体信息", ""),
        ("identity_status", "exact/ambiguous/not_found/pending", "pending"), ("reference_url", "结构记录链接", ""),
        ("query_date", "核对日期", ""), ("notes", "人工核查依据", "未核对，不可提交预测"),
    ]),
    ("compound_targets_raw.csv", "一行一个成分—原始靶点—来源/证据记录", [
        ("compound_key", "关联已确认成分", "C001"), ("original_id", "靶点原始ID，原样保存", "DEMO-T01"),
        ("original_id_type", "UniProtKB accession/Entrez/Ensembl/unknown等", "unknown"),
        ("target_name", "原始蛋白/靶点名", "示例蛋白"), ("species", "目标蛋白物种，不是药材基原", "待确认"),
        ("taxon_id", "目标物种分类号，未知留空", ""), ("evidence_type", "experimental/predicted/database_association/unknown", "unknown"),
        ("score", "原始关系/预测评分，不同源不混算", ""), ("score_name", "分数字段原名/定义", ""),
        ("input_structure", "预测时实际提交的SMILES；非预测可空", ""),
        ("source_db", "来源数据库、软件及版本", "教学占位库"), ("supporting_reference", "支持该关系的文献或记录链接", ""),
        ("query_date", "检索/运行日期", ""), ("raw_file", "原始文件路径", "raw/targets_original.tsv"),
        ("screening_criteria", "采用的筛选条件", "待制定"),
    ]),
    ("id_mapping_register.csv", "一行一个原始ID到候选条目的映射；失败也保留一行", [
        ("original_id", "与原始靶点表完全对应", "DEMO-T01"), ("original_id_type", "输入ID体系", "unknown"),
        ("species", "输入记录的目标物种", "待确认"), ("uniprot_id", "UniProtKB Entry/accession", ""),
        ("entry_name", "UniProt Entry Name，非基因符号", ""), ("protein_name", "映射后蛋白名称", ""),
        ("gene_symbol", "经核对的主基因符号", ""), ("mapped_taxon_id", "结果物种分类号", ""),
        ("reviewed", "条目审核状态，未知留空", ""), ("mapping_status", "mapped/unmapped/ambiguous/wrong_species/pending", "pending"),
        ("included", "yes/no/pending", "pending"), ("decision_reason", "纳入/排除或待核理由", "输入ID体系待确认"),
        ("source_db", "映射资源/版本", "UniProt"), ("query_date", "映射日期", ""), ("mapping_batch", "查询批次/任务号", "batch_001"),
    ]),
    ("compound_targets_standardized.csv", "一行一个成分—靶点—证据—映射审核明细", [
        ("herb_id", "关联药材表；共享成分可按药材展开", "H001"), ("compound_key", "关联成分", "C001"),
        ("original_id", "原靶点ID", "DEMO-T01"), ("original_id_type", "原ID体系", "unknown"),
        ("species", "原始靶点物种", "待确认"), ("uniprot_id", "审核后的accession", ""),
        ("gene_symbol", "审核后的标准主基因名", ""), ("taxon_id", "审核后的物种分类号", ""),
        ("mapping_status", "映射状态", "pending"), ("included", "最终是否纳入yes/no/pending", "pending"),
        ("decision_reason", "审核决定依据", "仅示例，禁止用于分析"), ("evidence_type", "原关系证据等级，映射不升级证据", "unknown"),
        ("source_db", "原关系来源", "教学占位库"), ("supporting_reference", "关系出处", ""),
        ("query_date", "原关系检索日期", ""), ("raw_file", "原始关系文件路径", "raw/targets_original.tsv"),
        ("mapping_batch", "关联映射批次", "batch_001"),
    ]),
]


def collection_markdown():
    parts = ["# 从资料检索到UniProt：操作与交付清单", "原始文件只读保存；界面、字段和下载权限以官方为准。教学示例不是研究数据。"]
    for step in COLLECTION_STEPS:
        parts.extend([f"## {step['title']}", f"要什么：{step['need']}", f"去哪里：{step['where']}", step["actions"], f"保存什么：{step['save']}", f"核查：{step['check']}", "\n".join(f"- [{name}]({url})" for name, url in step["links"])])
    for filename, grain, fields in TABLE_SCHEMAS:
        parts.extend([f"## {filename}", grain, "| 字段 | 含义 |", "| --- | --- |", "\n".join(f"| {key} | {meaning} |" for key, meaning, _ in fields)])
    parts.append("最终drug_target_genes.txt：仅从included=yes且mapping_status=mapped、gene_symbol非空、物种正确的行提取并去重，每行一个基因、无标题。它用于疾病交集，不是成分靶点关系表，也不是本站项目上传CSV的替代品。")
    return "\n\n".join(parts)


def render_collection_guide():
    import pandas as pd
    import streamlit as st

    st.subheader("资料检索 → UniProt：手把手资料准备")
    route = st.radio("本次用哪条资料整理路线？", ["SymMap药材—靶点（五积散案例）", "其他来源的成分—靶点路线"], key="collection_route")
    if route.startswith("SymMap"):
        from src.symmap_guide import render_symmap_workflow
        from src.case_companion import render_case_step
        render_symmap_workflow()
        with st.expander("五积散归档对照（不是需要再填的一套表）"):
            for step in (0, 3, 5):
                render_case_step("collection", step)
        return
    st.write("这一节先把资料整理清楚：从药材出发，找到成分与靶点，再把不同ID统一到同一套基因标识。走完A至F，就可以带着审核后的清单进入疾病交集。数据库检索和身份核对需要在来源端完成。")
    st.markdown("**交接顺序**：处方/药材表 → 药材成分表 → 成分结构核对 → 原始靶点表 → 分类型ID清单 → UniProt映射表 → 标准关系表与去重基因清单。")
    st.caption("建议分raw/（原始下载）、working/（清洗和审核）、exports/（下游输入）。原始文件不覆盖；每次检索记录数据库版本、日期、关键词、筛选条件与使用许可。")
    for index, step in enumerate(COLLECTION_STEPS):
        with st.expander(step["title"], expanded=index == 0):
            st.markdown(f"**需要什么**：{step['need']}\n\n**去哪里找**：{step['where']}")
            for name, url in step["links"]:
                st.link_button(name, url)
            st.markdown(step["actions"])
            st.markdown("**这一步保存什么**：" + step["save"])
            st.caption("核对要点：" + step["check"])
            st.caption("下方表格规范对应文件：" + step["table"])
            from src.case_companion import render_case_step
            render_case_step("collection", index)
    st.subheader("资料审核工作表（不是分析程序的直接输入）")
    st.caption("仅适用于当前成分—靶点路线；若使用SymMap药材靶点表，切换上方路线，不必再填这一套。")
    st.caption("格式示例 · 虚构编号与占位关系，仅用于学习填写。CSV使用UTF-8，日期YYYY-MM-DD，ID按文本保存；未知值留空，一格一个值。")
    for filename, grain, fields in TABLE_SCHEMAS:
        with st.expander(filename + " · " + grain):
            st.dataframe(pd.DataFrame(fields, columns=["字段名", "填写说明", "格式示例"]), hide_index=True, width="stretch")
            st.caption("横向预览：一行记录的实际形状（仅示意）")
            st.dataframe(pd.DataFrame([{key: example for key, _, example in fields}]), hide_index=True, width="stretch")
            st.download_button("下载空白模板 · " + filename, pd.DataFrame(columns=[key for key, _, _ in fields]).to_csv(index=False).encode("utf-8-sig"), filename, "text/csv", key="collection_" + filename)
    st.markdown("""### 完成后交给下一步什么？

- **研究归档**：保存原始文件、来源登记、所有审核明细，包括未映射和排除项。
- **疾病交集**：从最终关系表中筛选`included=yes`、`mapping_status=mapped`、物种正确且`gene_symbol`非空的行，抽出基因符号去重，保存为`drug_target_genes.txt`；每行一个、无标题。
- **网络构图**：保留完整成分—靶点关系，不要只剩去重基因。建边表时以成分键为source、基因为target，另带证据和来源；用于关系整理，不自动变成PPI。
- **本站项目上传**：本页是检索审核工作表，不保证可直接作为项目基础CSV上传；请按「项目管理」的实际字段模板转换。在线网络实验需整理成source/target边表。

### 常见卡点

数据库打不开或没有导出：换可用来源或按许可整理文献，记录替代来源，不假定数据相同。只有蛋白名字：走UniProtKB检索+人工确认，不使用错误的ID体系强行映射。映射失败：保留失败清单、回查拼写/旧ID/物种，不能为了让数量好看而删除失败记录。""")
    st.download_button("下载资料检索到UniProt完整操作单（Markdown）", collection_markdown().encode("utf-8-sig"), "collection_to_uniprot_guide.md", "text/markdown", key="collection_full_guide")
