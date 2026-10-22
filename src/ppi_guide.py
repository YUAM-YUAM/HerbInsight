"""从共同基因清单到PPI建图的文件交接教学。"""

PPI_STEPS = [
    ("1. 准备输入：共同基因清单不等于PPI边表", """**拿什么来**：上一节的common_targets.txt，每行一个已审核基因、无表头，同时带物种和ID体系说明。

先保存输入基因数，确认没有药材名、化合物名、混合物种或逗号分隔的一长串文本。此时还没有蛋白互作边，不要把两两基因组合自行当作PPI。

**交付**：common_targets.txt + 本次查询登记ppi_run_register.csv。为本次查询分配run_id，同一套参数的文件放一个目录；改变参数时新建run_id，不覆盖旧结果。"""),
    ("2. STRING提交与映射：输入了100个不等于识别了100个", """1. 打开STRING，选择多蛋白查询（Multiple proteins或当前对应入口），粘贴共同基因清单，选择研究物种，例如Homo sapiens（9606）。
2. 查看输入名称与识别条目的对应关系。核对名称、物种及重复映射；未识别或多候选项回查UniProt与原始来源，不为凑数随意挑选。
3. 保存可导出的映射/节点信息。如果页面不提供完整对应表，按许可整理可见记录并保留查询信息；不要根据图上标签臆造STRING ID。
4. 在ppi_node_mapping.csv保留input_id、string_id、preferred_name、gene_symbol、taxon_id与mapping_status。多个输入映射同一蛋白时保留输入明细，计算映射蛋白数时按唯一string_id计数。

**检查**：分别报告输入唯一ID数、成功映射输入数、映射后唯一蛋白数与未映射输入数。后面“有边节点数”是另一种口径。"""),
    ("3. 记录网络参数：每个开关都会改变后面的图", """在当前版本设置中确认并记录：

- **网络类型**：functional association包括功能关联，不代表所有边都是直接物理结合；physical interaction聚焦物理关联，但仍须解释证据来源，不能说每条边都已被自己的实验证实。
- **证据来源**：记录实际启用的通道，如experiments、databases、co-expression、text mining。不要把文本挖掘当成直接实验，或把combined score当作疗效概率。
- **置信度阈值**：例如比较0.4、0.7、0.9；高阈值更严格但可能丢失关系，不能仅凭网络变小判断研究更好。先确定主分析规则，再做敏感性分析。
- **额外邻居**：只研究共同靶点时，将可配置的新增蛋白/网络扩展数量设为0；若有第一层/第二层设置，均核对。扩展网络另存并区分输入节点与新增节点。
- **孤立节点显示**：隐藏不等于删除输入基因。记录是否隐藏，并保留映射后全部节点清单。

**交付**：记录STRING版本（能获得时）、查询日期、网络类型、物种、证据通道、分数阈值/尺度、额外邻居及是否隐藏孤立节点。界面可能变化，以官方文档为准。"""),
    ("4. 下载什么：图、边、节点与参数都要留", """从导出区域按许可保存可用的tabular/TSV边表，原样放raw/；图片只能看图，不能替代边表用于计算。

**边表**：至少要有两端蛋白标识和combined score；证据通道分数若可获得也保留。不同下载方式可能返回`#node1/node2`、`preferredName_A/preferredName_B`、`stringId_A/stringId_B`等列名，它们不是同一ID体系的保证，要看文件说明。

**节点映射**：保留输入ID、STRING ID、显示名与审核后的gene_symbol。建图两端都用STRING ID或都用统一基因名，不能一端是STRING ID、另一端是基因名。

**参数和图片**：保存查询登记、映射损失说明与原始网络图。网页给700，另一导出给0.7，可能只是0–1000与0–1两种尺度；只在确认定义后做转换，不通过“最大值看着大”自动猜。

**孤立节点**：用映射后唯一节点集合减去边端点集合确定没有入边表的节点（需确保导出范围一致）。边表中缺席不意味着该基因与疾病无关。"""),
    ("5. Cytoscape导入：网络表和属性表是两次操作", """1. 安装并启动Cytoscape；File → Import → Network from File（以安装版本为准），打开边表，核对分隔符为Tab或Comma，第一行是否表头。预览若只有一列，先修正分隔符，不继续导入。
2. 指定两端列为Source Node与Target Node，关系列可设Interaction Type，分数保留为数值型边属性。PPI通常按无向分析；箭头样式不决定分析算法方向。
3. 核对网络节点数、边数、重复关系和自环。节点表的name/shared name等键以实际导入结果为准，不假定显示标签就是匹配键。
4. 再用File → Import → Table from File导入节点属性表，选择Node Table Columns或当前对应选项。用属性表node_id匹配网络实际节点键；网络键若为STRING ID，属性表也必须用对应STRING ID。
5. 加入gene_symbol供显示、node_type、是否输入节点/新增邻居、来源或自己计算的指标。每个node_id在属性表只保留一行明确属性；多个来源写入独立证据表，避免连接时意外复制行。
6. 看几条已知节点，确认新属性不是整列空值、数值不是字符串、没有同一蛋白被画成两个ID节点。

**孤立节点提示**：仅导入边表不能恢复没有边的输入节点。若需展示全部映射节点，按当前Cytoscape版本支持的节点添加/导入流程补入，并记录方法；本站边表网络实验目前不会自动恢复孤立节点。"""),
    ("6. Cytoscape细致构图与拓扑：把样式和证据分开", """1. Tools中的Analyze Network/Analyzer运行拓扑分析，选择适用方向性；PPI常用无向。检查Degree、Betweenness、Closeness等生成字段，导出节点结果。
2. Style设置节点大小连续映射到Degree，颜色分类映射到node_type或是否输入节点，Label映射到可读gene_symbol。边宽映射combined score时注明它是置信度，不能标成作用强度。
3. Layout选择可用的力导向布局，如Prefuse Force Directed；调整标签和重叠，保持颜色/大小图例。布局中距离远近不代表蛋白在细胞中的实际距离。
4. 可选cytoHubba评估MCC等排名；可选MCODE寻找稠密模块。它们需要对应插件与版本，不是Analyzer Degree的别名。记录参数，不能把不同算法得分直接拼成一个排名。
5. 在不同置信度阈值下重复，比较节点/边数、连通分量和候选排名；同一布局看起来不同并不代表算法结果改变。
6. 保存.cys会话、完整节点/边表、软件与插件版本；通过当前导出功能保存SVG/PDF或高分辨率PNG，标明布局、阈值和网络类型。

**交付**：会话、带图例的图、节点指标、清洗边表与方法记录；不要只保存一张无法复算的截图。"""),
    ("7. 本站替代路线：快速计算，再回到Cytoscape精修", """1. 在本步骤下方直接计算：关闭内置示例，上传STRING导出TSV/CSV或整理后的Excel边表。
2. 根据预览选择source、target和权重列。若明确是0–1000的STRING分数，选择转换成0–1；已经是0–1则保持原始权重。转换后再填阈值，例如0.7。
3. PPI通常关闭有向网络，运行后核对输入文件、列名、尺度、节点/边数、重复边、自环和连通分量。在线教学限500节点/5000条去重边；大网络用本地工具。
4. 下载节点指标CSV、清洗边表CSV和实验记录。本站node_id与上传端点相同，不会自动变成gene_symbol。
5. 将节点指标CSV作为Cytoscape节点属性导入，用node_id与网络节点键匹配，再做精细样式与论文图。

**指标差异**：本站使用简单图，重复节点对只保留最高权重；权重用于筛选与布局，中心性用无权最短路径。有向Closeness按到达节点的距离计算；不同软件的归一化/断连处理可能不同，不能只按列名认定数值应完全一致。

本站不查询STRING、不执行cytoHubba MCC或MCODE，也不将中心性高解释为已验证治疗靶点。"""),
]

PPI_FIELDS = {
    "ppi_run_register.csv": [
        ("run_id", "查询唯一编号，变参数另存"), ("input_file", "输入清单路径"), ("id_system", "输入ID体系"),
        ("species", "研究物种"), ("taxon_id", "物种分类号"), ("string_version", "可获得的版本，未知留空"),
        ("query_date", "查询日期"), ("network_type", "functional或physical"), ("evidence_channels", "实际启用通道"),
        ("confidence_cutoff", "本次阈值"), ("score_scale", "0–1或0–1000，注明导出含义"),
        ("added_neighbors", "新增邻居设置，必要时注明各层"), ("hide_isolates", "是否隐藏孤立节点"),
        ("input_count", "输入唯一ID数"), ("mapped_input_count", "成功映射输入数"),
        ("mapped_protein_count", "映射后唯一蛋白数"), ("edge_node_count", "边表端点唯一数"),
        ("edge_count", "边数及去重口径"), ("raw_edge_file", "原始边表路径"), ("mapping_file", "节点映射路径"),
        ("query_reference", "任务/查询记录，不能保证链接永久有效"),
    ],
    "ppi_node_mapping.csv": [
        ("run_id", "对应本次查询"), ("input_id", "原始输入ID，原样保留"), ("string_id", "映射得到的蛋白ID"),
        ("preferred_name", "来源显示名，不保证是标准基因名"), ("gene_symbol", "审核后的主基因符号"),
        ("taxon_id", "映射物种"), ("mapping_status", "mapped/unmapped/ambiguous等"),
        ("is_input_node", "yes/no，区分新增邻居"), ("has_edge", "本次边表中是否出现yes/no"), ("notes", "人工审核备注"),
    ],
    "ppi_edges_template.csv": [
        ("source", "统一ID体系的起点"), ("target", "同体系的终点"), ("weight", "明确尺度的数值置信度"),
        ("relation", "functional_association或physical_association等准确类型"),
        ("source_type", "如protein"), ("target_type", "如protein"), ("source_db", "STRING等实际来源"), ("run_id", "关联查询登记"),
    ],
    "ppi_node_attributes.csv": [
        ("node_id", "与建图端点相同体系的唯一键"), ("gene_symbol", "显示用审核符号"),
        ("node_type", "节点类别"), ("is_input_node", "是否原始输入节点"), ("source_db", "来源"), ("notes", "说明"),
    ],
}

TROUBLESHOOTING = [
    ("导入只有一列", "TSV被当成CSV；核对文件真实分隔符，不是只改后缀。"),
    ("节点属性全空", "核对两表连接键、空格与ID体系；STRING ID不能直接匹配基因名。"),
    ("同一蛋白出现两次", "混用了别名/STRING ID/基因符号；先查映射，不仅仅改显示标签。"),
    ("网络节点比输入多", "检查是否新增邻居、同一输入多候选或混入额外表；不直接宣称发现新靶点。"),
    ("网络节点比输入少", "逐项核对未映射、合并映射、筛选和孤立节点是否未入边表。"),
    ("阈值0.7几乎不筛边", "若原始为0–1000，0.7不是700；先确认单位再转换。"),
    ("本站与Cytoscape排名不同", "统一实际节点/边集合、自环/重复、方向性、权重用法、算法和归一化再比较。"),
]


def ppi_markdown():
    parts = ["# 共同靶点到PPI：STRING、Cytoscape与本站交接", "菜单与可导出字段以当前官方版本为准；本课程不代表已完成所有网站实时操作验证。"]
    for title, body in PPI_STEPS:
        parts.extend(["## " + title, body])
    for filename, fields in PPI_FIELDS.items():
        parts.extend(["## " + filename, "| 字段 | 含义 |\n| --- | --- |\n" + "\n".join(f"| {key} | {meaning} |" for key, meaning in fields)])
    parts.extend(["## 排错", "\n".join(f"- {symptom}：{solution}" for symptom, solution in TROUBLESHOOTING)])
    return "\n\n".join(parts)


def render_ppi_guide(practice=None):
    import pandas as pd
    import streamlit as st
    from src.network_engine import map_edge_columns

    st.subheader("共同靶点 → STRING → Cytoscape / 本站")
    st.info("拿着上一节共同基因清单开始。本节讲清每次文件交接；获取真实PPI仍需在外部数据库按许可操作。")
    for name, url in [("STRING官方帮助", "https://string-db.org/help/faq/"), ("Cytoscape网络导入手册", "https://manual.cytoscape.org/en/stable/Creating_Networks.html"), ("Cytoscape Analyzer手册", "https://manual.cytoscape.org/en/stable/Network_Analyzer.html")]:
        st.link_button(name, url)
    for i, (title, body) in enumerate(PPI_STEPS):
        with st.expander(title, expanded=i == 0):
            st.markdown(body)
            if i == 6 and practice is not None:
                practice()
    st.subheader("文件交接与空白模板")
    for filename, fields in PPI_FIELDS.items():
        with st.expander(filename):
            st.dataframe(pd.DataFrame(fields, columns=["字段", "填写说明"]), hide_index=True, width="stretch")
            st.download_button("下载空表 · " + filename, pd.DataFrame(columns=[key for key, _ in fields]).to_csv(index=False).encode("utf-8-sig"), filename, "text/csv", key="ppi_guide_" + filename)
    st.subheader("评分单位与列名对应演示")
    st.caption("完全虚构的NODE_A/B/C边与分数，仅演示导入；不是STRING检索结果或真实蛋白互作。")
    raw = pd.DataFrame({"#node1": ["NODE_A", "NODE_B", "NODE_A"], "node2": ["NODE_B", "NODE_C", "NODE_C"], "combined_score": [900, 700, 400]})
    st.dataframe(raw, hide_index=True, width="stretch")
    st.markdown("`#node1 → source`，`node2 → target`，`combined_score ÷ 1000 → weight`。两端ID本身不变，转换的只有分数。")
    cutoff = st.slider("演示阈值（0–1）", 0.0, 1.0, 0.7, 0.1, key="ppi_guide_cutoff")
    mapped = map_edge_columns(raw, "#node1", "node2", "combined_score", "string_1000")
    kept = mapped[mapped["weight"] >= cutoff]
    st.metric("演示保留边数", len(kept))
    st.dataframe(kept, hide_index=True, width="stretch")
    st.caption("此处演示评分换算与筛选，不冒充完整建图结果。真实数据的清洗、中心性、网络图与结果导出，请进入左侧「网络药理学教学实验」。")
    st.subheader("遇到问题先检查这里")
    st.dataframe(pd.DataFrame(TROUBLESHOOTING, columns=["现象", "核查方式"]), hide_index=True, width="stretch")
    st.download_button("下载PPI建图完整操作单（Markdown）", ppi_markdown().encode("utf-8-sig"), "ppi_building_guide.md", "text/markdown", key="ppi_guide_download")
