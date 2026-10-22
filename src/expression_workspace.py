"""Course-embedded upload, calculation and result hand-off."""
import json
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.expression_analysis import (read_analysis_table, differential_expression, train_classifier,
    analysis_fingerprint, method_record, result_zip, expression_example)
from src.enrichment_engine import run_over_representation


def inputs(prefix):
    source = st.radio("选择数据", ["使用虚构数据练习", "上传我的数据"], key=prefix+"_source", horizontal=True)
    example, meta, annotation = expression_example()
    with st.expander("输入格式与示例文件"):
        st.write("表达矩阵：首列gene_symbol，后续列名为sample_id；每行一个已整理好的基因。样本表：sample_id、group，建议附subject_id。两张表的样本必须完全对应。")
        st.download_button("下载表达矩阵示例", example.to_csv(index=False).encode("utf-8-sig"), "demo_expression_log2.csv", key=prefix+"_expr_download")
        st.download_button("下载分组表示例", meta.to_csv(index=False).encode("utf-8-sig"), "demo_sample_metadata.csv", key=prefix+"_meta_download")
    if source == "上传我的数据":
        expression_file = st.file_uploader("表达矩阵（CSV/TSV，最多30 MB）", type=["csv", "tsv", "txt"], key=prefix+"_expression")
        metadata_file = st.file_uploader("样本分组（CSV/TSV）", type=["csv", "tsv", "txt"], key=prefix+"_metadata")
        if not expression_file or not metadata_file:
            return None
        try:
            example, meta = read_analysis_table(expression_file), read_analysis_table(metadata_file)
        except (ValueError, UnicodeError, pd.errors.ParserError) as error:
            st.error(str(error))
            return None
        scale = st.selectbox("表达数据类型", ["请选择", "已标准化的log2连续表达", "原始RNA-seq计数", "TPM/FPKM或类型不确定"], key=prefix+"_scale")
        if scale != "已标准化的log2连续表达":
            st.info("当前计算入口接收已标准化的log2连续表达。原始计数请按本节DESeq2/edgeR路线处理；不要通过改名、取整或直接取log冒充适用输入。")
            return None
        if not st.checkbox("已核对：每位患者只有一个样本，两组独立，无需配对或批次/协变量调整", key=prefix+"_design"):
            return None
    else:
        st.caption("这是固定种子生成的虚构数据，基因和功能集合均为占位名称，仅供练习。")
    if "group" not in meta or meta["group"].isna().any():
        st.error("分组表需要非空group列。")
        return None
    groups = list(meta.group.astype(str).unique())
    if len(groups) != 2:
        st.error("本流程需要恰好两个组。")
        return None
    col1, col2 = st.columns(2)
    control = col1.selectbox("对照组", groups, index=groups.index("control") if "control" in groups else 0, key=prefix+"_control")
    case = col2.selectbox("病例/实验组（效应方向：此组减对照）", groups, index=groups.index("case") if "case" in groups else 1, key=prefix+"_case")
    st.caption(f"读取到 {len(example)} 个基因、{max(0, example.shape[1]-1)} 个样本。")
    return example, meta, annotation, control, case, source


def render_expression_analysis():
    st.subheader("在这里完成差异分析与富集")
    st.write("当前方法：独立两组的逐基因Welch t检验，随后在全部可检验基因上做BH校正。log2FC为两组平均log2表达之差；本方法不进行limma的经验贝叶斯收缩。")
    data = inputs("de")
    if data is None:
        st.session_state.pop("de_run", None)
        return
    expression, meta, annotation, control, case, source = data
    fp = analysis_fingerprint(expression, meta, control, case, source)
    stored = st.session_state.get("de_run")
    if stored and stored["fingerprint"] != fp:
        st.session_state.pop("de_run", None)
    if st.button("运行差异分析", key="run_differential", type="primary"):
        st.session_state.pop("de_run", None)
        try:
            with st.spinner("核对输入并计算差异…"):
                result, matrix, aligned = differential_expression(expression, meta, control, case)
            record = method_record("Welch_two_sided_BH", {"control": control, "case": case,
                "scale": "normalized_log2", "design": "independent_two_groups_no_covariates",
                "log2fc_definition": "mean_log2_case - mean_log2_control",
                "multiple_testing": "BH over all finite test p-values; zero variance excluded"}, fp, source)
            st.session_state["de_run"] = dict(fingerprint=fp, result=result, matrix=matrix, aligned=aligned, record=record)
        except (ValueError, TypeError) as error:
            st.error(str(error))
    run = st.session_state.get("de_run")
    if not run:
        return
    result, matrix = run["result"], run["matrix"]
    st.success("差异分析完成。筛选阈值只改变展示与下游目标，不会重新定义BH检验范围。")
    c1, c2 = st.columns(2)
    fdr = c1.number_input("差异FDR阈值", min_value=0.001, max_value=1.0, value=0.05, key="de_fdr")
    effect = c2.number_input("最小绝对log2FC", min_value=0.0, value=1.0, key="de_effect")
    significant = result[(result.p_adjust <= fdr) & (result.log2fc.abs() >= effect)].copy()
    tested = result.loc[result.status == "tested", "gene_symbol"]
    c1, c2, c3 = st.columns(3)
    c1.metric("实际检验基因", len(tested)); c2.metric("上调", int((significant.log2fc > 0).sum())); c3.metric("下调", int((significant.log2fc < 0).sum()))
    if (result.status != "tested").any():
        st.info(f"{int((result.status != 'tested').sum())}个基因两组内方差均为零，未作检验；完整表保留原因。")
    with st.expander("完整差异结果", expanded=True):
        st.dataframe(result, hide_index=True, width="stretch")
    plot = result[result.p_adjust.notna()].copy()
    plot["minus_log10_fdr"] = -np.log10(plot.p_adjust.clip(lower=1e-300))
    plot["方向"] = np.where((plot.p_adjust <= fdr) & (plot.log2fc.abs() >= effect), np.where(plot.log2fc > 0, "上调", "下调"), "未达阈值")
    volcano = px.scatter(plot, x="log2fc", y="minus_log10_fdr", color="方向", hover_name="gene_symbol", title=f"{case} 相对 {control}：火山图")
    st.plotly_chart(volcano, width="stretch")
    st.download_button("下载可交互火山图（HTML）", volcano.to_html(include_plotlyjs=True).encode("utf-8"), "volcano.html", key="de_volcano")
    top = plot.head(30).gene_symbol
    if len(top):
        heat = matrix.loc[top]
        sd = heat.std(axis=1).replace(0, 1)
        heat = heat.sub(heat.mean(axis=1), axis=0).div(sd, axis=0)
        figure = px.imshow(heat, aspect="auto", color_continuous_scale="RdBu_r", title="FDR排序前30基因（逐行Z分数，展示用途）")
        st.plotly_chart(figure, width="stretch")
        st.download_button("下载可交互热图（HTML）", figure.to_html(include_plotlyjs=True).encode("utf-8"), "heatmap.html", key="de_heatmap")
    record = dict(run["record"], display_thresholds={"fdr": fdr, "abs_log2fc": effect})
    tables = {"all_differential_results.csv": result, "selected_genes.csv": significant,
              "tested_background.csv": pd.DataFrame({"gene_symbol": tested}), "aligned_samples.csv": run["aligned"]}
    st.download_button("下载差异分析结果与方法记录（ZIP）", result_zip(tables, record), "differential_analysis.zip", key="de_zip")
    st.divider()
    st.subheader("接着做GO/KEGG富集")
    st.caption("自动使用上面实际检验的基因作背景；注释覆盖范围还会进一步限制有效背景。正式分析请提供同物种、同ID的完整注释表。")
    direction = st.selectbox("用哪组差异基因做富集", ["全部达阈值基因", "仅上调", "仅下调"], key="de_ora_direction")
    target = significant if direction.startswith("全部") else significant[significant.log2fc > 0] if direction == "仅上调" else significant[significant.log2fc < 0]
    if source == "上传我的数据":
        ann_file = st.file_uploader("注释表：gene_symbol、term_id、term_name，可选category", type=["csv", "tsv", "txt"], key="de_annotations")
        if not ann_file:
            st.info("准备方式见GO/KEGG课程；差异结果可先下载保存。")
            return
        try:
            annotation = read_analysis_table(ann_file)
        except (ValueError, UnicodeError) as error:
            st.error(str(error)); return
    else:
        st.caption("练习使用虚构功能集合；下列结果不是实际GO/KEGG发现。")
    ora_fp = analysis_fingerprint(fp, annotation, direction, fdr, effect)
    old = st.session_state.get("de_ora_run")
    if old and old["fingerprint"] != ora_fp:
        st.session_state.pop("de_ora_run", None)
    if st.button("用这些差异基因计算富集", key="run_de_ora"):
        st.session_state.pop("de_ora_run", None)
        try:
            ora, diagnostics = run_over_representation(set(target.gene_symbol), annotation, set(tested), minimum_overlap=0)
            st.session_state["de_ora_run"] = dict(fingerprint=ora_fp, result=ora, diagnostics=diagnostics)
        except ValueError as error:
            st.error(str(error))
    ora_run = st.session_state.get("de_ora_run")
    if ora_run:
        st.dataframe(ora_run["result"], hide_index=True, width="stretch")
        with st.expander("有效背景与目标核对"):
            st.json(ora_run["diagnostics"])
        ora_record = method_record("hypergeometric_ORA_BH", {"differential_run": record, "direction": direction,
            "background": "all testable genes intersect annotation coverage", "diagnostics": ora_run["diagnostics"]}, ora_fp, source)
        st.download_button("下载差异＋富集完整结果包", result_zip(dict(tables, **{"enrichment.csv": ora_run["result"]}), ora_record), "expression_to_enrichment.zip", key="de_ora_zip")


def render_machine_learning():
    st.subheader("用自己的表达数据训练分类模型")
    st.write("先保留25%样本作内部测试集；其余样本在训练集内交叉验证。去除常量、标准化和特征筛选都在训练折内完成。请使用未按全体分组预筛选的表达矩阵。")
    data = inputs("ml_run")
    if data is None:
        st.session_state.pop("ml_computed", None); return
    expression, meta, _, control, case, source = data
    model = st.selectbox("分类方法", ["logistic", "random_forest"], format_func=lambda x: {"logistic":"逻辑回归", "random_forest":"随机森林"}[x], key="ml_algorithm")
    features = st.number_input("训练折内最多选择基因数", 2, 500, 50, key="ml_feature_count")
    seed = st.number_input("随机种子", 0, 100000, 42, key="ml_seed")
    st.caption("每组至少8名独立患者；小样本评估波动很大。反复根据测试集挑模型会使评估偏乐观，最终仍需独立队列。这里不自动复用差异筛选后的基因，以避免数据泄漏。")
    fp = analysis_fingerprint(expression, meta, control, case, model, features, seed, source)
    old = st.session_state.get("ml_computed")
    if old and old["fingerprint"] != fp:
        st.session_state.pop("ml_computed", None)
    if st.button("训练模型并评估", key="train_model", type="primary"):
        st.session_state.pop("ml_computed", None)
        try:
            with st.spinner("在训练集内筛选特征并验证…"):
                outputs = train_classifier(expression, meta, control, case, model, features, seed)
            record = method_record("classification", {"model": model, "feature_limit": features, "seed": seed,
                "negative_group": control, "positive_group": case, "test_fraction": 0.25,
                "preprocessing": "variance filter, standard scaling, ANOVA selection within training folds",
                "validation": "internal held-out test; no external validation"}, fp, source)
            st.session_state["ml_computed"] = dict(fingerprint=fp, outputs=outputs, record=record)
        except (ValueError, TypeError, ImportError) as error:
            st.error(str(error))
    run = st.session_state.get("ml_computed")
    if not run:
        return
    metrics, predictions, importance, splits, cv = run["outputs"]
    a,b,c = st.columns(3)
    a.metric("训练内交叉验证平均AUC", f"{metrics['cv_auc_mean']:.3f}")
    b.metric("内部测试集AUC", f"{metrics['test_auc']:.3f}")
    c.metric("测试集平衡准确率", f"{metrics['test_balanced_accuracy']:.3f}")
    from sklearn.metrics import roc_curve
    fpr, tpr, _ = roc_curve(predictions.true_label, predictions.probability)
    figure = px.line(x=fpr, y=tpr, labels={"x":"假阳性率", "y":"真阳性率"}, title="内部保留测试集ROC")
    st.plotly_chart(figure, width="stretch")
    st.dataframe(pd.DataFrame(metrics["confusion_matrix"], index=["真实对照", "真实病例"], columns=["预测对照", "预测病例"]), width="stretch")
    st.dataframe(importance, hide_index=True, width="stretch")
    st.caption("逻辑回归权重对应标准化后的特征；随机森林权重为不纯度重要性。特征权重是预测线索，不能解释为因果效应。")
    st.download_button("下载训练评估结果与方法记录", result_zip({"test_predictions.csv": predictions,
        "feature_weights.csv": importance, "sample_split.csv": splits, "training_cv.csv": cv,
        "metrics.csv": pd.DataFrame([{k:v for k,v in metrics.items() if k != "confusion_matrix"}])}, run["record"]), "classification_results.zip", key="ml_results_zip")
