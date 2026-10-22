"""富集分析的数据准备、传统工具路线与本站ORA交接课程。"""

ENRICHMENT_STEPS = [
    ("1. 先选ORA还是GSEA，再选输入基因", """**ORA（过度富集）**：回答“已选出的这组基因，是否在某功能条目里比随机抽取更常见？”可以使用审核后的共同靶点、预先定义的差异基因集等；每次分析写明选取规则，不能把不同目的的列表悄悄混合。

**GSEA**：通常需要所有合格检测基因的有方向排序统计量，排序方案由研究设计决定，不是把筛出的十几个基因再排一遍。本站当前实现的是ORA，不执行GSEA。

PPI与富集可以使用相同共同靶点列表分别分析，不必先用网络中心性筛一遍。若特意分析hub基因，要另起分析批次并说明选择偏倚；不能只保留能得到显著结果的列表。

**要交付**：target_genes.csv至少一列gene_symbol，每行一个审核后基因，去重复；保存原始清单、物种和选择理由。"""),
    ("2. 准备背景：它决定“随机抽取”是从哪里抽", """**先问**：在这项研究的技术和纳入规则下，哪些基因原本有机会成为目标？背景不是想让P值更小而任选的数字。

- 转录组差异基因ORA：考虑经过质控、过滤且实际参与差异检验的基因，而不是只用显著差异基因。保存过滤规则。
- 靶向测序或特定面板：考虑实际被该面板检测、可被纳入的基因。
- 数据库靶点筛选：说明可被检索、映射和筛选的候选总体。没有唯一通用的网络药理学背景；如果实际总体不可得，明确说明采用注释基因总体等替代方案的限制，并做合理敏感性检查。

不要把目标列表本身直接当背景；这会失去通常想比较的“相对更常见”的意义。单纯使用两个列表的并集也不是自动正确的背景。

**本站实际口径**：有效背景=上传背景∩注释表覆盖的基因；不上传背景时=注释表覆盖的全部基因。有效目标=目标∩有效背景，落在外面的目标会被列为忽略项。保存原始背景与最终有效数量，不能把未注释基因假装具有注释。

**要交付**：background_genes.csv一列gene_symbol，每行一个；记录抽样总体、物种、ID体系与背景选择依据。"""),
    ("3. 快速网页路线：g:Profiler怎么准备与保存", """1. 打开g:Profiler，选择研究物种，将目标ID清单粘贴至功能分析入口；确认它识别的ID体系、映射数和未识别项。
2. 选择需要的功能来源（如GO-BP/MF/CC、可用的KEGG等），不要把不同来源的多个结果当完全独立验证。
3. 按当前界面设置统计域/自定义背景。上传的是有依据的背景清单，不是目标清单的副本。核对工具实际如何处理注释缺失和背景。
4. 选择并记录实际多重校正方法。g:Profiler可提供其特有的g:SCS以及其他可用选项，不能看到“adjusted”就一律写BH；具体选项以当前版本为准。
5. 保存可下载的完整结果、查询参数、版本/日期、识别损失和命中基因，不只保存前10条气泡图。下载结果不等于获得完整注释库。

**适合**：暂时没有自备注释表、希望快速探索的初学者。数据库版本、检验条目集合与校正策略不同，不应期待它与本站完全一致。"""),
    ("4. R路线：clusterProfiler与完整注释的准备", """**传统分析**：准备目标、背景与统一ID；GO可用clusterProfiler::enrichGO，明确OrgDb、keyType、ont、universe、pAdjustMethod和条目大小筛选等；KEGG可用enrichKEGG并核对物种代码、输入ID类型、访问许可和查询日期。人类符号不应未经转换就当作KEGG的基因ID。

**本站GO注释来源之一**：使用合法安装且版本明确的org.Hs.eg.db与GO.db，提取Symbol→GOALL及GO term名称，整理成每行一个基因—GO条目的长表。下方提供人类专用R脚本，使用祖先传播GOALL；它不是实测成分靶点证据，也不包含KEGG。

**另一选择**：GO官方下载的合适物种GAF/GPA等注释资源。保留原始文件、发布版本与说明，遵循格式规范；例如GAF包含注释限定符，NOT否定关系不能当正向成员，基因产物ID需先映射，直接/祖先注释的策略要明确。GAF不是简单改个.csv后缀就能上传本站的文件。本站目前不解析原始GAF。

**KEGG注释**：在许可允许的情况下，从KEGG官方或授权资源取得物种基因—pathway关系与名称；将物种ID按同一映射方案转为本站使用的基因符号。保留映射失败项、许可、版本/日期，不使用未知来源的“万能KEGG表”。本站不自动下载KEGG，也不提供KEGG整库分发。

缺少完整注释时先走网页路线；不要把某篇论文的显著条目表或“目标基因查到的几个通路”冒充完整背景注释。"""),
    ("5. 三个文件长什么样：不是三份结果表", """**目标表target_genes.csv**：gene_symbol；一行一个目标基因。

**背景表background_genes.csv**：gene_symbol；一行一个可选总体基因。

**注释表term_annotations.csv**：gene_symbol、term_id、term_name，推荐category（GO-BP/GO-MF/GO-CC/KEGG）。一行一个基因—条目关系；同一基因属于多个条目就写多行，同一条目可对应多个基因。不要把十几个基因用斜杠塞进一格。

注释应覆盖所选背景及计划检验的功能来源，不只包含目标的命中关系。统一物种、ID体系、条目命名与版本；同一term_id/category不应因不同拼写的term_name拆成多个检验条目。

**本站限制**：当前基因符号会统一转大写，适合已审核的人类符号；其他物种不要直接套用，需要先确认大小写与ID处理。字段名不能代替身份映射。小型内置注释（含TRAIN占位）只用于学习，不是正式GO/KEGG资源。

**交付**：三个输入原件、完整注释资源说明、映射/过滤记录与enrichment_run_register.csv。"""),
    ("6. 本站计算：先核对有效数量，再读显著性", """1. 在本步骤下方直接计算：关闭内置示例，上传目标、背景、注释；也可粘贴目标基因。上传与粘贴同时存在时会合并去重，注意不要误混旧列表。
2. 设最小命中数与FDR阈值，运行后先看有效目标、有效背景、被检验条目和忽略目标。数字不符合预期时先回查ID与注释，不急着解释通路。
3. 本站采用单侧超几何检验，先对本次全部实际检验条目（含零命中）做BH，再按最小命中数过滤展示。最小命中数设0可保留所有已检验条目。
4. 本站把本次注释里的所有category一起作为BH检验族；若要按GO分支/KEGG分别校正，应预先拆分注释、分批运行并如实报告。不能结果出来后按显著性挑一部分重新校正。
5. 查看p_value、p_adjust、count、term_size、gene_ratio和fold_enrichment。GeneRatio=count/有效目标数；富集倍数=(count/有效目标数)/(条目背景基因数/有效背景数)，不是激活倍数。
6. 下载筛选后的全部结果和实验记录。FDR未达阈值时，界面可能展示非显著条目用于探索，不要把“看到了气泡”当成统计显著。保存完整结果时最小命中数设0。

**交付**：结果CSV、参数与质量记录、必要的图、目标/背景/注释资源。富集不表示通路一定激活、抑制或导致疾病，更不证明复方疗效。"""),
    ("7. 交作业与排错：让别人能按相同输入复算", """报告至少写清：研究问题；ORA或GSEA；物种/ID；目标来源与数量；背景依据与有效数量；注释来源/版本/日期及传播策略；检验条目范围；软件版本；筛选与多重校正方法；命中基因；显著和非显著结果；局限性。

- **全都不显著**：可能是真实结果，也可能是样本小或注释不足。先核对输入，不能为显著而任意换背景、只挑显著条目重算。
- **目标大量被忽略**：检查符号/蛋白ID混用、物种、旧ID与注释覆盖；保留忽略清单。
- **相似条目特别多**：GO层级与基因集重叠常见，报告共同命中基因和冗余关系，不等于获得多份独立证据。
- **工具结果不同**：对齐有效目标/背景、条目资源、传播、大小过滤、检验族和校正方法后再比较。
- **需要判断方向**：ORA不能单独判断上/下调或通路激活。需结合表达方向、适用的排序分析与独立实验。

可以继续用转录组、遗传或其他独立资料检验候选，但不要把同一基因集反复做图当成独立验证。"""),
]

ENRICHMENT_FIELDS = {
    "target_genes.csv": [("gene_symbol", "每行一个已审核目标基因")],
    "background_genes.csv": [("gene_symbol", "每行一个有机会被选择的背景基因")],
    "term_annotations.csv": [("gene_symbol", "与目标/背景同体系的基因"), ("term_id", "唯一条目ID"), ("term_name", "统一条目名称"), ("category", "GO-BP/GO-MF/GO-CC/KEGG等来源分类")],
    "enrichment_run_register.csv": [
        ("run_id", "分析唯一编号"), ("analysis_type", "ORA或GSEA，不混用"), ("species", "研究物种"), ("id_system", "统一ID体系"),
        ("target_file", "目标文件路径"), ("target_rule", "目标筛选依据"), ("background_file", "背景文件路径"), ("background_rationale", "抽样总体定义"),
        ("annotation_file", "完整注释文件路径"), ("annotation_source", "注释资源及许可"), ("annotation_version", "资源版本/日期"),
        ("annotation_propagation", "直接/GOALL等祖先传播策略"), ("category_scope", "检验GO类别/KEGG范围"),
        ("test_family", "多重校正涵盖哪些条目"), ("software_version", "实际工具及版本"), ("adjustment_method", "BH/g:SCS等实际方法"),
        ("minimum_overlap", "展示最少命中数"), ("fdr_cutoff", "FDR阈值"), ("run_date", "实际运行日期"), ("notes", "ID损失、过滤与限制"),
    ],
}

GO_EXPORT_R = r'''# 人类GO注释导出示例。需先合法安装AnnotationDbi、org.Hs.eg.db、GO.db。
# 在RStudio中设置独立工作目录后运行；已有同名输出时停止，避免覆盖。
# 此脚本不执行富集、不下载KEGG。实际物种不是人类时不要直接运行。
library(AnnotationDbi)
library(org.Hs.eg.db)
library(GO.db)
outputs <- c("term_annotations_human_go.csv", "go_annotation_versions.txt")
if (any(file.exists(outputs))) stop("输出已存在，请更换工作目录或另存文件名")
genes <- keys(org.Hs.eg.db, keytype = "SYMBOL")
mapping <- select(org.Hs.eg.db, keys = genes, keytype = "SYMBOL",
                  columns = c("GOALL", "ONTOLOGYALL"))
mapping <- unique(mapping[complete.cases(mapping[, c("SYMBOL", "GOALL", "ONTOLOGYALL")]), ])
terms <- select(GO.db, keys = unique(mapping$GOALL), keytype = "GOID", columns = "TERM")
joined <- merge(mapping, terms, by.x = "GOALL", by.y = "GOID", all.x = TRUE)
annotations <- data.frame(gene_symbol = joined$SYMBOL, term_id = joined$GOALL,
                          term_name = joined$TERM, category = paste0("GO-", joined$ONTOLOGYALL))
annotations <- unique(annotations[complete.cases(annotations), ])
write.csv(annotations, outputs[1], row.names = FALSE, fileEncoding = "UTF-8")
capture.output(sessionInfo(), metadata(org.Hs.eg.db), metadata(GO.db), file = outputs[2])
message("导出完成：请核查ID/物种/注释覆盖。GOALL含祖先传播，未按证据代码筛选；请记录该策略。")
'''


def enrichment_markdown():
    parts = ["# GO/KEGG富集：输入准备与多路线操作", "具体网页选项以官方版本与许可为准；本课程未声称逐项验证实时网站操作。"]
    for title, body in ENRICHMENT_STEPS:
        parts.extend(["## " + title, body])
    for filename, fields in ENRICHMENT_FIELDS.items():
        parts.extend(["## " + filename, "| 字段 | 含义 |\n| --- | --- |\n" + "\n".join(f"| {key} | {meaning} |" for key, meaning in fields)])
    parts.extend(["## 人类GO注释导出R示例（需本地R与相应包）", "```r\n" + GO_EXPORT_R + "\n```"])
    return "\n\n".join(parts)


def render_enrichment_guide(practice=None):
    import pandas as pd
    import streamlit as st
    from scipy.stats import hypergeom

    st.subheader("GO/KEGG：三个输入文件从哪里来？")
    st.write("富集分析先准备三份材料：目标基因、背景基因、完整注释。可以走网页、R或本平台ORA路线；先看清输入是什么，再选择工具。显著结果表是分析产物，不是注释输入。")
    for name, url in [("g:Profiler", "https://biit.cs.ut.ee/gprofiler/"), ("clusterProfiler", "https://bioconductor.org/packages/release/bioc/html/clusterProfiler.html"), ("GO注释下载说明", "https://geneontology.org/docs/download-go-annotations/"), ("KEGG官方入口", "https://www.kegg.jp/"), ("org.Hs.eg.db", "https://bioconductor.org/packages/org.Hs.eg.db/")]:
        st.link_button(name, url)
    for i, (title, body) in enumerate(ENRICHMENT_STEPS):
        with st.expander(title, expanded=i == 0):
            st.markdown(body)
            from src.case_companion import render_case_step
            render_case_step("enrichment", i)
            if i == 5 and practice is not None:
                practice()
    st.subheader("输入表字段与空白模板")
    for filename, fields in ENRICHMENT_FIELDS.items():
        with st.expander(filename):
            st.dataframe(pd.DataFrame(fields, columns=["字段", "填写说明"]), hide_index=True, width="stretch")
            st.download_button("下载空表 · " + filename, pd.DataFrame(columns=[key for key, _ in fields]).to_csv(index=False).encode("utf-8-sig"), filename, "text/csv", key="ora_guide_" + filename)
    with st.expander("有R基础：导出人类GO注释的脚本与使用条件"):
        st.warning("需本地R及匹配包版本；此处未执行该R脚本。仅人类GO，使用GOALL祖先传播且不筛证据代码，不是KEGG下载器。正式分析须核查资源版本及适用性。")
        st.code(GO_EXPORT_R, language="r")
        st.download_button("下载人类GO注释导出R示例", GO_EXPORT_R.encode("utf-8"), "export_human_go_annotations.R", "text/plain", key="ora_guide_r")
    st.subheader("背景为什么会影响P值？")
    st.caption("虚构总体的单条目超几何演示：目标10个、命中4个，背景中条目成员10个。没有GO/KEGG真实注释，也没有进行多重检验。")
    population = st.slider("演示背景总基因数", min_value=20, max_value=200, value=100, step=20, key="ora_guide_population")
    p_value = float(hypergeom.sf(4 - 1, population, 10, 10))
    expected = 10 * 10 / population
    columns = st.columns(3)
    columns[0].metric("随机期望命中数", f"{expected:.2f}")
    columns[1].metric("演示富集倍数", f"{4 / expected:.2f}")
    columns[2].metric("原始P值（未校正）", f"{p_value:.4g}")
    st.warning("演示只为理解抽样模型，改变背景时固定了条目成员数。真实背景应按研究设计决定，不能根据哪个P值更小来挑背景。正式多条目分析必须进行合适的多重校正。")
    st.download_button("下载富集分析完整操作单（Markdown）", enrichment_markdown().encode("utf-8-sig"), "enrichment_input_guide.md", "text/markdown", key="ora_guide_full")
