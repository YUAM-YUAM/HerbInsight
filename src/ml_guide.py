"""机器学习教学、真实限定建模、固定预测评估与患者划分核对。"""

ML_ALGORITHMS = [
    {"模型": "Logistic Regression", "适合回答": "建立可解释的二分类基线", "优势": "系数方向清楚、速度快、便于复现", "主要局限": "难表达复杂非线性", "平台状态": "可直接运行"},
    {"模型": "Elastic Net Logistic", "适合回答": "高维特征下做收缩与稀疏建模", "优势": "兼顾L1筛选与L2稳定性", "主要局限": "相关特征的保留结果可能波动", "平台状态": "可直接运行"},
    {"模型": "Random Forest", "适合回答": "探索非线性及变量交互", "优势": "对尺度不敏感、能描述复杂关系", "主要局限": "小样本易过拟合，重要性可能偏倚", "平台状态": "可直接运行"},
    {"模型": "RBF-SVM", "适合回答": "比较复杂分类边界是否改善预测", "优势": "高维空间中有较强表达能力", "主要局限": "参数敏感、全局解释较弱", "平台状态": "可直接运行"},
    {"模型": "XGBoost/LightGBM", "适合回答": "较充分样本下的提升树比较", "优势": "性能与调参空间丰富", "主要局限": "小样本调参很容易产生乐观偏差", "平台状态": "方法拓展，不在本站计算"},
]

LANGUAGE_ROUTES = [
    {"路线": "Python", "推荐工具": "pandas + scikit-learn Pipeline", "优势": "网页部署、模型管线和工程复现方便", "局限": "部分经典组学流程不如Bioconductor集中", "适用场景": "平台计算、多模型比较、自动化交付"},
    {"路线": "R", "推荐工具": "Bioconductor + tidymodels/glmnet", "优势": "统计建模、差异表达和科研绘图生态成熟", "局限": "跨环境部署与依赖管理相对复杂", "适用场景": "组学预处理、统计分析、论文级图表"},
]

ML_STEPS = [
    ("1. 定义预测任务：预测分组不是证明治疗机制", """先确定预测对象、阳性标签与使用场景。例如用结肠组织表达区分患者/对照，仅能评估这一数据情境下的分组预测，不能说模型预测了复方疗效或适合临床筛查。

标签必须来自可靠样本资料。保留样本、患者、队列和批次信息；同一患者的多个活检不算多个独立受试者。病例定义、组织、治疗状态和对照来源应可比较。

**交付**：任务说明、阳性/阴性定义、样本纳入规则。分类、回归、生存预测不是同一种任务，本课程的评估练习仅针对二分类。"""),
    ("2. 准备X与y：表达矩阵要变成样本行、基因列", """从上一节已审核的表达矩阵出发，核对样本和基因ID、数据尺度与缺失值。X通常一行一个样本、一列一个基因/特征，y是一行对应的标签，不把GSE/GSM编号当预测特征。

- features.csv：sample_id + 各特征数值。sample_id只用于连接，不能当数值输入模型。
- ml_sample_labels.csv：sample_id、subject_id、cohort、batch、label；标签0/1含义在研究方案里记录，不按行号拼表。
- 预先确定的外部知识候选基因可作为特征范围，但若基因由本次整批表达数据的标签差异筛出，则这一步已使用测试信息，不能宣称独立验证。

训练集与外部数据需同一特征定义和适用处理尺度。不同平台不能直接拼起来训练，更不能用待测试标签决定如何处理。**交付**：原始/处理后数据、标签来源及映射损失记录。"""),
    ("3. 先划分，再学习：患者级隔离与数据泄漏", """在训练前设计划分。训练集用于拟合；验证集/内层交叉验证用于调参和阈值选择；最终测试集只用于锁定模型后的评估。具体比例需考虑独立患者数、类别和研究目的，没有固定万能7:3。

同一subject_id的全部样本必须在同一数据划分；存在重复患者时交叉验证也要按患者分组。适当检查类别分布，并保留随机种子和每个样本的split。若仅有很小样本，可采用合适的分组/嵌套交叉验证，但不能把重复折数说成独立患者数。

**泄漏高风险**：在全部样本上用标签筛差异基因、填补/标准化、筛特征、选模型，然后才随机分训练和测试。正确做法是把需拟合的数据处理、特征选择与模型放进每个训练折内；测试集只应用已学到的变换。

不要用全部发现+验证数据一起做批次校正后再声称验证集完全独立。疾病与批次/队列完全重合时，模型可能学的是来源差别，不是疾病。"""),
    ("4. 选模型：每种算法都要有明确角色", """**Python**：scikit-learn的Pipeline串联适用的缺失处理、StandardScaler、特征选择和LogisticRegression/SVM等；分层或分组交叉验证要与患者结构一致。GroupKFold/StratifiedGroupKFold等的适用性以实际样本和版本为准。

**R**：tidymodels或caret组织预处理、重采样与调参；glmnet可做惩罚回归。LASSO在分类时需使用适当的分类模型，不是所有LASSO分数都直接当概率。

**可视化软件**：Orange等适合学习数据导入与训练/评估流程，但数据类型、分组重采样及嵌套特征选择能力必须核对，拖拽流程不自动避免泄漏。

先用逻辑回归建立基线，再按研究需要比较Elastic Net、随机森林与SVM。所有模型必须使用相同训练样本、相同交叉验证折和相同指标；调参及特征筛选只发生在训练流程中。样本很少、特征很多时，复杂模型并不自动更可靠。

**本站当前**：实际操作区可运行逻辑回归、Elastic Net、随机森林和RBF-SVM。公平比较模式先在训练集交叉验证中选择候选，再用内部保留测试集评估；不提供自动调参、外部验证或临床可用性判断。"""),
    ("5. 报告指标：AUC、阈值和准确率不是一回事", """先定义阳性为1，保存每个测试样本的真实标签和模型阳性分数；概率应说明校准情况，decision score则注明不是概率。

ROC-AUC衡量排序，不依赖某一个分类阈值，但受数据构成和验证设计影响。Accuracy、Sensitivity/Recall、Specificity、Precision、F1及混淆矩阵依赖阈值；阈值应在训练/验证流程中按目的确定，不在最终测试集上挑最优后当作预先指定。

类别不平衡时补充PR-AUC/平均精确率等适当指标，并明确具体定义；它们不能和ROC-AUC混称。若输出风险概率，还要考虑校准。报告患者级不确定性/置信区间与样本量，不能只挑一张高AUC图。

下方固定预测分数练习只演示二分类ROC-AUC和阈值指标，不验证分数是否来自真正未见过的样本。实际训练区另有平均精确率等指标；当前不提供性能置信区间或概率校准。某个分母为0时显示未定义，不能冒充0或100%。"""),
    ("6. 外部验证与特征解释：先锁定再测试", """有条件时在独立队列验证，先检查患者是否重复、组织/临床定义、特征覆盖、测量尺度和训练策略能否迁移。只用训练阶段锁定的特征、变换、模型和阈值。

如果为了适应新队列重新调参或筛基因，这个队列已参与开发，不能继续称作纯外部测试；应另设评估或明确限制。

LASSO系数、随机森林重要性、SHAP等反映模型中贡献，不证明基因是治疗靶点或因果驱动。相关基因可相互替代，比较跨重采样稳定性时也要把筛选放在合法训练流程中。

**交付**：完整划分、训练参数、每例预测、性能和限制；不把同一表达数据的差异分析、免疫评分和模型当成多份独立验证。"""),
    ("7. 接回平台：学习、评估与真实建模分开", """先用本页虚构病例练习患者隔离检查，再理解固定预测在不同阈值下的表现。这里的指标由现场计算生成，但没有训练模型，也没有真实疗效证据。

「案例解读→机器学习结果」用于已有文件解读；本课程实际操作区支持四类模型的训练内公平比较、特征筛选、交叉验证与内部保留测试。外部验证与复杂患者/批次模型需另行开展。

后续可结合独立的表达、免疫环境或遗传证据，但每一分支有自己的数据前提。完整性不是每个算法都跑一遍，而是任务、数据、模型、评估与解释边界能接得上。"""),
]

ML_FIELDS = {
    "features_template.csv": [("sample_id", "唯一样本键，不作为模型特征"), ("GENE_A", "示意特征列，替换为实际审核基因"), ("GENE_B", "示意特征列，按实际特征数扩展")],
    "ml_sample_labels.csv": [("sample_id", "与X行名一致"), ("subject_id", "独立患者/生物个体ID"), ("label", "实际0/1标签，定义另记"), ("cohort", "发现/外部队列来源"), ("batch", "已知测量批次"), ("label_reference", "分组出处")],
    "ml_split_register.csv": [("sample_id", "唯一样本ID"), ("subject_id", "同患者全部样本同一划分"), ("split", "train/validation/test"), ("fold", "适用时交叉验证折号"), ("random_seed", "实际种子"), ("split_rationale", "患者隔离、分层/队列设计依据")],
    "ml_predictions.csv": [("sample_id", "评估样本ID"), ("subject_id", "独立患者ID"), ("dataset", "队列"), ("y_true", "0或1，阳性定义另记"), ("positive_score", "模型阳性分数/概率"), ("score_type", "probability/decision_score"), ("model_id", "锁定模型编号"), ("evaluation_set", "测试/验证/训练需标清")],
    "ml_run_register.csv": [("run_id", "分析编号"), ("task", "任务和标签定义"), ("feature_source", "候选来源，是否使用本数据标签"), ("split_file", "划分路径"), ("preprocessing", "训练折内拟合处理"), ("model", "算法和参数"), ("resampling", "重采样/嵌套/患者分组方案"), ("threshold_rule", "阈值及确定数据集"), ("software_version", "环境及版本"), ("random_seed", "种子"), ("limitations", "泄漏、样本量、混杂和迁移限制")],
}


def audit_patient_split(records):
    """检查样本唯一性和跨划分患者重叠，不保证不存在其他泄漏。"""
    required = {"sample_id", "subject_id", "split"}
    if not required <= set(records.columns):
        raise ValueError("划分表需要sample_id、subject_id、split。")
    if records.empty or records[list(required)].isna().any().any():
        raise ValueError("划分表为空或患者/样本/划分信息缺失。")
    if any(not isinstance(v, str) or not v.strip() for c in required for v in records[c]):
        raise ValueError("样本、患者和划分必须是非空文本。")
    if any(v != v.strip() for c in required for v in records[c]):
        raise ValueError("标识含首尾空格，请先核对清理，避免漏检重复患者。")
    if records.sample_id.duplicated().any():
        raise ValueError("样本ID重复，不能静默去重。")
    if not set(records.split) <= {"train", "validation", "test"}:
        raise ValueError("split仅允许train、validation、test。")
    counts = records.groupby("subject_id")["split"].nunique()
    return sorted(counts[counts > 1].index.tolist())


def evaluate_binary_predictions(labels, scores, threshold=0.5):
    """固定0–1阳性分数的二分类评估，AUC按平均秩处理并列。"""
    import numpy as np
    import pandas as pd
    y = np.asarray(labels, dtype=float)
    p = np.asarray(scores, dtype=float)
    if y.ndim != 1 or p.ndim != 1 or not len(y) or len(y) != len(p):
        raise ValueError("标签与分数须是长度一致的非空一维列表。")
    if not np.isfinite(y).all() or not np.isin(y, [0, 1]).all():
        raise ValueError("真实标签必须为0或1。")
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("本练习仅接受0–1有限阳性分数。")
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("阈值必须在0–1内。")
    positives = int(y.sum())
    negatives = len(y) - positives
    if not positives or not negatives:
        raise ValueError("ROC-AUC评估需要同时有阳性和阴性样本。")
    pred = p >= threshold
    tp, fp = int(((y == 1) & pred).sum()), int(((y == 0) & pred).sum())
    fn, tn = positives - tp, negatives - fp
    ranks = pd.Series(p).rank(method="average").to_numpy()
    auc = (ranks[y == 1].sum() - positives * (positives + 1) / 2) / (positives * negatives)
    return {"auc": float(auc), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "accuracy": (tp + tn) / len(y), "sensitivity": tp / positives, "specificity": tn / negatives,
            "precision": tp / (tp + fp) if tp + fp else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}


def ml_markdown():
    def table(rows):
        columns = list(rows[0])
        return "| " + " | ".join(columns) + " |\n| " + " | ".join(["---"] * len(columns)) + " |\n" + "\n".join(
            "| " + " | ".join(str(row[column]) for column in columns) + " |" for row in rows)
    parts = ["# 机器学习：数据、划分与评估", "课程包含规范教学与限定条件下的真实模型训练；内部测试不等于外部或临床验证。"]
    parts.extend(["## 算法选择表", table(ML_ALGORITHMS),
                  "## Python与R路线", table(LANGUAGE_ROUTES)])
    for title, body in ML_STEPS:
        parts.extend(["## " + title, body])
    for name, fields in ML_FIELDS.items():
        parts.extend(["## " + name, "| 字段 | 含义 |\n| --- | --- |\n" + "\n".join(f"| {key} | {meaning} |" for key, meaning in fields)])
    return "\n\n".join(parts)


def render_ml_guide():
    import pandas as pd
    import streamlit as st

    st.subheader("机器学习：先防泄漏，再谈模型性能")
    st.write("先别急着追求最高AUC。我们先把训练与测试样本分开，再用同一划分公平比较四类模型。课程下方可以上传自己的表达数据真实计算；案例结果、虚构练习和用户数据始终分开标注。")
    for name, url in [("scikit-learn防泄漏指南", "https://scikit-learn.org/stable/common_pitfalls.html"), ("scikit-learn模型评估", "https://scikit-learn.org/stable/modules/model_evaluation.html"), ("tidymodels", "https://www.tidymodels.org/"), ("Orange", "https://orangedatamining.com/")]:
        st.link_button(name, url)
    st.subheader("算法不是越多越好：先明确每个模型的角色")
    st.dataframe(pd.DataFrame(ML_ALGORITHMS), hide_index=True, width="stretch")
    st.caption("平台真正运行前四类模型；提升树列为拓展方向，不冒充已完成功能。竞赛展示重点是公平比较、证据留痕和边界说明，而不是算法数量。")
    st.subheader("Python和R都能完成，选择取决于任务")
    st.dataframe(pd.DataFrame(LANGUAGE_ROUTES), hide_index=True, width="stretch")
    st.info("同一项目可以用R完成组学预处理，再把规范表达矩阵交给Python平台建模。若要比较两条路线，必须保持样本纳入、标签、数据划分、预处理定义和评价指标一致。")
    for i, (title, body) in enumerate(ML_STEPS):
        with st.expander(title, expanded=i == 0):
            st.markdown(body)
            from src.case_companion import render_case_step
            render_case_step("ml", i)
    with st.expander("实际操作：上传表达矩阵，训练并评估"):
        from src.expression_workspace import render_machine_learning
        render_machine_learning()
    st.subheader("建模资料空表")
    for name, fields in ML_FIELDS.items():
        with st.expander(name):
            st.dataframe(pd.DataFrame(fields, columns=["字段", "填写说明"]), hide_index=True, width="stretch")
            st.download_button("下载空表 · " + name, pd.DataFrame(columns=[key for key, _ in fields]).to_csv(index=False).encode("utf-8-sig"), name, "text/csv", key="ml_guide_" + name)
    st.subheader("练习一：同一患者能同时在训练集和测试集吗？")
    mode = st.radio("患者划分情形", ["患者隔离", "同患者跨训练和测试"], key="ml_guide_split")
    records = pd.DataFrame({"sample_id": ["DEMO_S1", "DEMO_S2", "DEMO_S3", "DEMO_S4"], "subject_id": ["DEMO_P1", "DEMO_P2", "DEMO_P3", "DEMO_P4"], "split": ["train", "train", "test", "test"]})
    if mode == "同患者跨训练和测试":
        records.loc[2, "subject_id"] = "DEMO_P1"
    st.dataframe(records, hide_index=True, width="stretch")
    overlap = audit_patient_split(records)
    if overlap:
        st.error("检测到跨划分患者：" + "、".join(overlap) + "。请按患者重新设计划分。")
    else:
        st.success("本示意表未发现跨划分患者；不代表分组、预处理、特征选择或队列设计已通过完整审核。")
    st.subheader("练习二：移动阈值，为什么AUC不变？")
    st.caption("虚构的4例固定预测，不来自训练模型或真实患者；小样本只为演示计算，不能说明模型可用性。阳性定义为1，score≥阈值判阳性。")
    labels, scores = [0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]
    st.dataframe(pd.DataFrame({"y_true": labels, "positive_score": scores}), hide_index=True, width="stretch")
    threshold = st.slider("演示分类阈值", 0.0, 1.0, 0.5, 0.05, key="ml_guide_threshold")
    metrics = evaluate_binary_predictions(labels, scores, threshold)
    columns = st.columns(4)
    for col, key, label in zip(columns, ["auc", "accuracy", "sensitivity", "specificity"], ["演示ROC-AUC", "演示准确率", "演示敏感度", "演示特异度"]):
        col.metric(label, f"{metrics[key]:.2f}")
    st.dataframe(pd.DataFrame({"实际类别": ["阳性1", "阴性0"], "预测阳性": [metrics["tp"], metrics["fp"]], "预测阴性": [metrics["fn"], metrics["tn"]]}), hide_index=True, width="stretch")
    st.caption("Precision：" + ("未定义（没有预测阳性）" if metrics["precision"] is None else f"{metrics['precision']:.2f}") + f"；F1：{metrics['f1']:.2f}。AUC由全部固定分数的排序计算，移动分类阈值不会重训练模型或改变排序。")
    st.warning("只能在训练/验证流程中选择最终阈值；不要在正式测试集上反复挑阈值，再把最好的结果当作无偏性能。")
    st.download_button("下载机器学习教学完整操作单（Markdown）", ml_markdown().encode("utf-8-sig"), "machine_learning_guide.md", "text/markdown", key="ml_guide_full")
