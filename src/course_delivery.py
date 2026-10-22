"""统一能力说明、自查与可下载的教学交付记录。"""

CAPABILITIES = [
    ("药材/成分收集", "核心流程", "操作课、来源与关系空表；外部检索", "TCMSP/HERB/ETCM、原始文献", "不自动抓取，不生成未核实关系"),
    ("ID标准化", "核心流程", "UniProt输入/映射/回填教学与模板", "UniProt/UniProtKB", "不执行自动生物学ID映射"),
    ("疾病基因与交集", "核心流程", "来源审核课；粘贴清单现场求交集", "GeneCards/DISGENET/OMIM、集合脚本", "交集不是已验证治疗靶点"),
    ("PPI与关系网络", "核心流程", "STRING/Cytoscape课；上传边表真实建网与中心性", "STRING/Cytoscape/NetworkX", "不自动查询STRING；不含MCC/MCODE；边表无孤立节点恢复"),
    ("GO/KEGG", "核心流程", "准备课；自备注释上传ORA、BH与结果下载", "g:Profiler/clusterProfiler", "不自动取KEGG；非GSEA；人类符号转大写"),
    ("转录组", "可选证据", "log2表达上传、独立两组Welch/BH、火山图/热图、衔接ORA", "GEO2R/limma/DESeq2/edgeR", "不处理原始计数、配对、批次/协变量；非limma"),
    ("机器学习", "可选证据", "逻辑回归/随机森林、折内筛选、交叉验证及内部测试", "scikit-learn/tidymodels/Orange", "每位患者一个样本；无外部队列验证；特征不是因果"),
    ("免疫微环境", "可选证据", "表达与签名上传ssGSEA、覆盖审核、两组比较及BH", "GSVA/CIBERSORTx/immunedeconv", "不执行去卷积；评分非细胞比例"),
    ("孟德尔随机化", "可选证据", "外部LD筛选后上传、等位基因协调、F筛选、IVW/Q/逐一剔除", "TwoSampleMR/PLINK等", "无GWAS下载/LD/Egger；排除回文；假定有效工具及NOME"),
    ("单细胞基础", "高级可选", "下载/QC/注释与患者级设计课及空表", "Seurat/Scanpy", "无单细胞上传处理"),
    ("细胞通讯", "高级可选", "输入/工具/结果解释课及空表", "CellChat/CellPhoneDB", "无通用计算；bulk不是细胞级输入"),
    ("计算扰动", "高级可选", "方法选择课、固定虚构图删点示意", "scTenifoldKnk/CellOracle等", "不预测真实敲除后的表达或细胞状态"),
    ("报告与归档", "项目工具", "现有项目报告；课程、自查与操作单下载", "下载后本地归档", "不自动把外部分析变成已核验结果"),
]

ACCEPTANCE_CHECKS = [
    ("问题与数据", "复方版本、药材、疾病实体、物种与研究问题明确"),
    ("问题与数据", "所有原始文件有来源、日期、许可/版本说明，未被覆盖"),
    ("问题与数据", "实验、预测、数据库关联与未知证据分开标记"),
    ("问题与数据", "基因/蛋白ID统一，未映射、一对多与排除原因保留"),
    ("核心分析", "药物和疾病侧筛选规则预先说明，不为数量/显著性临时修改"),
    ("核心分析", "交集及两侧数量自洽，每个候选可回查原始证据"),
    ("核心分析", "STRING网络类型、物种、证据通道、阈值、邻居与ID损失记录"),
    ("核心分析", "网络指标、重复边、方向性和孤立节点口径清楚"),
    ("核心分析", "富集目标/背景/注释资源和实际检验族可追溯"),
    ("核心分析", "保留完整检验与非显著结果，图的统计与生物含义未夸大"),
    ("按需扩展", "所选扩展有独立问题与合格数据，未做的分支写明未做"),
    ("按需扩展", "转录组/免疫/机器学习的患者结构、混杂和信息泄漏已审核（如适用）"),
    ("按需扩展", "MR工具变量、LD、单位、等位基因与敏感性限制已审核（如适用）"),
    ("按需扩展", "单细胞/通讯/扰动所需数据满足，不将示意当作真实结果（如适用）"),
    ("解释与交付", "同源数据未当成多份独立验证，中心性/预测不当作因果或疗效"),
    ("解释与交付", "软件/数据库版本、脚本、种子、参数与输入输出保留"),
    ("解释与交付", "报告区分实际结果、教学示例、未实现功能与下一步验证"),
    ("解释与交付", "下载记录已自行保存并核对能打开，未上传密钥或敏感个人资料"),
]


def capability_markdown():
    rows = ["# 平台能力与教学交付边界", "更新：2026-10-23。下表是软件功能说明，不是科学有效性认证。", "| 模块 | 定位 | 本站实际能力 | 外部路线 | 边界 |", "| --- | --- | --- | --- | --- |"]
    rows.extend("| " + " | ".join(row) + " |" for row in CAPABILITIES)
    rows.extend(["## 归档建议", "raw/原始资料；working/清洗映射与审核；scripts/实际分析代码；results/完整数值输出；figures/图例完整的图；reports/报告；metadata/版本、参数、许可和数据字典。", "每个分析分配run_id关联输入、来源、筛选、软件和输出。只下载课程不等于已完成研究；没有使用某个分支时明确不适用，不为勾选而补造结果。"])
    return "\n\n".join(rows)


def study_record(title, question, branches, results, limitations, checked):
    if any(i < 0 or i >= len(ACCEPTANCE_CHECKS) for i in checked):
        raise ValueError("自查项编号无效。")
    sections = ["# 教学项目交付记录", "项目：" + (title.strip() or "未填写"), "本记录由使用者填写/自查，不表示平台核验了外部数据或模型结论。", "## 研究问题", question.strip() or "未填写", "## 选择的分析分支及理由", branches.strip() or "未填写", "## 实际结果与文件路径", results.strip() or "未填写；不要粘贴示例作为研究结果", "## 限制与下一步验证", limitations.strip() or "未填写", "## 自查（未勾选=未确认，不自动判为失败）"]
    sections.extend(f"- [{'x' if i in checked else ' '}] [{category}] {label}" for i, (category, label) in enumerate(ACCEPTANCE_CHECKS))
    sections.extend(["## 报告正文建议", "研究问题 → 来源与数据字典 → 纳入/筛选与ID → 实际方法及参数 → 完整结果与图 → 独立证据/未验证项 → 限制 → 下一步；按能力表如实区分平台、外部工具与示意结果。", capability_markdown()])
    return "\n\n".join(sections)


def render_delivery():
    import pandas as pd
    import streamlit as st
    st.subheader("分析方法与适用范围")
    st.dataframe(pd.DataFrame(CAPABILITIES, columns=["模块", "定位", "本站实际能力", "外部路线", "边界"]), hide_index=True, width="stretch")
    st.caption("在线计算涵盖网络分析、ORA、限定设计的差异表达、分类模型、ssGSEA与IVW。各模块输入和适用设计见表；外部工具课程与模拟练习单独标识。")
    st.download_button("下载能力与归档清单", capability_markdown().encode("utf-8-sig"), "platform_capabilities.md", "text/markdown", key="course_capabilities_download")
    st.subheader("整理你的研究记录")
    st.write("先用一句话写清研究问题，再记录用到的方法、结果文件和下一步计划。只填写与你研究相关的分支，其余标为不适用。")
    st.caption("记录由你核对并填写，不构成平台认证。完成后请下载保存，会话重置可能丢失未保存内容。")
    title = st.text_input("教学项目名称", key="delivery_title")
    question = st.text_area("你的研究问题", key="delivery_question")
    branches = st.text_area("选哪些分支、为什么；哪些不适用", key="delivery_branches")
    results = st.text_area("实际结果与输入/输出文件路径（不要填写密钥或敏感信息）", key="delivery_results")
    limitations = st.text_area("限制与后续验证", key="delivery_limitations")
    checked = set()
    for category in dict.fromkeys(category for category, _ in ACCEPTANCE_CHECKS):
        with st.expander(category):
            for i, (item_category, label) in enumerate(ACCEPTANCE_CHECKS):
                if item_category == category and st.checkbox(label, key=f"delivery_check_{i}"):
                    checked.add(i)
    st.caption(f"自行确认 {len(checked)}/{len(ACCEPTANCE_CHECKS)} 项；这不是算法完成比例或研究质量分数。")
    st.download_button("下载我的教学交付记录（Markdown）", study_record(title, question, branches, results, limitations, checked).encode("utf-8-sig"), "teaching_project_record.md", "text/markdown", key="delivery_record_download")
