import pandas as pd
import streamlit as st
import plotly.express as px
from src.expression_analysis import read_analysis_table, analysis_fingerprint, method_record, result_zip
from src.expression_workspace import inputs
from src.advanced_analysis import run_mr, mr_example, immune_ssgsea


def render_mr_analysis():
    st.subheader("孟德尔随机化 · IVW分析")
    st.write("支持已按同一基因组版本合并、已在外部做LD筛选的两样本汇总数据。进行单碱基等位基因协调、F阈值筛选、IVW、异质性与逐一剔除分析；回文位点保守排除。")
    example = mr_example()
    st.download_button("下载MR输入示例（虚构）", example.to_csv(index=False).encode("utf-8-sig"), "mr_input_example.csv", key="mr_input_example")
    source = st.radio("MR数据来源", ["虚构示例", "上传我的工具变量"], key="mr_source")
    table = example
    if source != "虚构示例":
        file = st.file_uploader("上传暴露与结局合并表", type=["csv","tsv","txt"], key="mr_input")
        if not file:
            st.session_state.pop("mr_computed", None); return
        try:
            table = read_analysis_table(file)
        except (ValueError, UnicodeError) as error:
            st.error(str(error)); st.session_state.pop("mr_computed", None); return
        if not st.checkbox("已核对：同一暴露/结局、基因组版本一致，工具已按LD独立筛选，效应单位和样本重叠已审核", key="mr_prerequisites"):
            st.session_state.pop("mr_computed", None); return
    st.caption("本站不自动下载GWAS或做LD clumping；IVW依赖有效工具假设，结果不能独自确认因果。不执行MR-Egger或水平多效性全面审核。beta按原效应单位输出，二分类结局应输入log(OR)。")
    minimum_f = st.number_input("最小单工具F统计量", 0.0, 1000.0, 10.0, key="mr_minimum_f")
    fp = analysis_fingerprint(table, minimum_f, source)
    previous = st.session_state.get("mr_computed")
    if previous and previous["fingerprint"] != fp:
        st.session_state.pop("mr_computed", None)
    if st.button("协调并计算MR", key="run_mr", type="primary"):
        st.session_state.pop("mr_computed", None)
        try:
            result, audit, loo = run_mr(table, minimum_f)
            record = method_record("two_sample_IVW", {"minimum_f":minimum_f,
                "harmonization":"same/swapped/complement; all palindromic SNPs excluded",
                "ld":"user pre-clumped externally", "se":"multiplicative random effects, no underdispersion",
                "limitations":"NOME assumed; no Egger/LD/overlap correction"}, fp, source)
            st.session_state["mr_computed"] = dict(fingerprint=fp, result=result, audit=audit, loo=loo, record=record)
        except (ValueError, TypeError) as error:
            st.error(str(error))
    run = st.session_state.get("mr_computed")
    if run:
        st.dataframe(run["result"], hide_index=True, width="stretch")
        st.dataframe(run["audit"], hide_index=True, width="stretch")
        st.plotly_chart(px.scatter(run["loo"], x="beta", y="excluded_snp", title="逐一剔除后的IVW估计"), width="stretch")
        st.download_button("下载MR结果、协调审计与方法", result_zip({"ivw.csv":run["result"], "harmonization.csv":run["audit"], "leave_one_out.csv":run["loo"]}, run["record"]), "mr_results.zip", key="mr_results_zip")


def render_immune_analysis():
    st.subheader("免疫相关签名 · ssGSEA评分")
    st.caption("输出免疫相关签名相对富集分数，不是细胞比例。使用已标准化log2表达进行样本内秩评分，分组比较限独立两组。")
    data = inputs("immune_run")
    if data is None:
        st.session_state.pop("immune_computed", None); return
    expression, meta, annotation, control, case, source = data
    signatures = annotation.rename(columns={"term_id":"signature_id"})[["signature_id", "gene_symbol"]]
    st.download_button("下载签名格式示例（虚构）", signatures.to_csv(index=False).encode("utf-8-sig"), "demo_signatures.csv", key="signature_example")
    if source == "上传我的数据":
        file = st.file_uploader("免疫签名表（signature_id、gene_symbol）", type=["csv","tsv","txt"], key="immune_signatures")
        if not file:
            st.session_state.pop("immune_computed", None); return
        try:
            signatures = read_analysis_table(file)
        except (ValueError, UnicodeError) as error:
            st.error(str(error)); st.session_state.pop("immune_computed", None); return
    minimum = st.number_input("每个签名最少覆盖基因数", 2, 500, 5, key="immune_minimum")
    fp = analysis_fingerprint(expression, meta, signatures, control, case, minimum, source)
    old = st.session_state.get("immune_computed")
    if old and old["fingerprint"] != fp:
        st.session_state.pop("immune_computed", None)
    if st.button("计算ssGSEA与组间比较", key="run_immune", type="primary"):
        st.session_state.pop("immune_computed", None)
        try:
            with st.spinner("计算每个样本的签名富集…"):
                scores, comparisons, coverage = immune_ssgsea(expression, meta, signatures, control, case, minimum)
            import importlib.metadata
            record = method_record("GSEApy_ssGSEA", {"minimum_genes":minimum, "control":control, "case":case,
                "sample_norm_method":"rank", "correl_norm_type":"rank", "weight":0.25,
                "permutations":0, "seed":42, "comparison":"two-sided asymptotic Mann-Whitney U, BH across included signatures",
                "score_unit":"relative enrichment, not cell proportion"}, fp, source)
            record["versions"]["gseapy"] = importlib.metadata.version("gseapy")
            st.session_state["immune_computed"] = dict(fingerprint=fp, scores=scores, comparisons=comparisons, coverage=coverage, record=record)
        except (ValueError, TypeError, ImportError, LookupError) as error:
            st.error(str(error))
    run = st.session_state.get("immune_computed")
    if run:
        st.dataframe(run["coverage"], hide_index=True, width="stretch")
        st.dataframe(run["comparisons"], hide_index=True, width="stretch")
        st.plotly_chart(px.box(run["scores"], x="signature_id", y="NES", color="group", points="all", title="签名相对富集分数"), width="stretch")
        st.download_button("下载ssGSEA评分、比较与方法", result_zip({"scores.csv":run["scores"], "comparisons.csv":run["comparisons"], "coverage.csv":run["coverage"]}, run["record"]), "immune_ssgsea.zip", key="immune_results_zip")
