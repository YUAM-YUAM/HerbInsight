"""A short, reproducible first experiment using the production ORA engine."""
from math import comb

import pandas as pd

from src.enrichment_engine import run_over_representation
from src.expression_analysis import analysis_fingerprint, method_record, result_zip


def experiment_inputs(hit_count=5):
    if not isinstance(hit_count, int) or not 1 <= hit_count <= 10:
        raise ValueError("命中数须为1到10的整数。")
    genes = [f"DEMO_{i:03}" for i in range(1, 101)]
    targets = genes[:hit_count] + genes[10:30-hit_count]
    # A partition covers the entire background, with no invented GO/KEGG IDs.
    annotations = pd.DataFrame([
        {"gene_symbol": gene, "term_id": f"DEMO_SET_{index // 10 + 1:02}",
         "term_name": f"模拟集合{index // 10 + 1}", "category": "模拟注释"}
        for index, gene in enumerate(genes)
    ])
    return pd.DataFrame({"gene_symbol": targets}), pd.DataFrame({"gene_symbol": genes}), annotations


def exact_tail(n_population, n_term, n_target, n_hit):
    """Independent finite combinatorial reference, only for this small fixture."""
    lower = max(n_hit, 0, n_target - (n_population - n_term))
    upper = min(n_term, n_target)
    return sum(comb(n_term, k) * comb(n_population - n_term, n_target - k)
               for k in range(lower, upper + 1)) / comb(n_population, n_target)


def run_first_experiment(hit_count):
    targets, background, annotations = experiment_inputs(hit_count)
    result, diagnostics = run_over_representation(set(targets.gene_symbol), annotations,
                                                  set(background.gene_symbol), minimum_overlap=0)
    fingerprint = analysis_fingerprint(targets, background, annotations)
    params = {"hit_count_for_set_1": hit_count, "background_size": 100, "target_size": 20,
              "tested_terms": 10, "correction": "BH over all 10 terms", "minimum_overlap": 0}
    record = method_record("ORA / hypergeometric upper tail", params, fingerprint, "人工构造的教学模拟数据；非GO/KEGG数据库注释")
    reference = exact_tail(100, 10, 20, hit_count)
    calculated = float(result.loc[result.term_id == "DEMO_SET_01", "p_value"].iloc[0])
    record["reference_check"] = {"method": "finite sum of binomial coefficients, independent of scipy.stats",
                                 "reference_p": reference, "engine_p": calculated,
                                 "absolute_error": abs(reference-calculated), "tolerance": 1e-12,
                                 "passed": abs(reference-calculated) <= 1e-12,
                                 "scope": "仅模拟集合1原始P值的软件数值核对；非真实数据或教学效果验证"}
    tables = {"target_genes.csv": targets, "background_genes.csv": background,
              "term_annotations.csv": annotations, "all_results.csv": result}
    return result, diagnostics, record, tables


def render_first_experiment():
    import streamlit as st
    with st.expander("三分钟实训：亲手算一次，再解释为什么", expanded=False):
        st.write("不需要账号或自备文件。这里调用与正式课程相同的ORA引擎，不是预存结果图片。")
        st.warning("模拟教学数据：100个虚构基因分成10个集合。没有药材关系、真实GO/KEGG注释或治疗结论。")
        st.markdown("**1 · 改输入**：背景100个基因、目标20个；集合1含10个基因。改变目标与集合1的重叠数，观察结果。目标总数保持20，其他集合的命中也随之改变。")
        hits = st.slider("目标与模拟集合1的重叠基因数", 1, 10, 5, key="first_hits")
        targets, background, annotations = experiment_inputs(hits)
        with st.expander("核对本次输入：目标、背景、注释"):
            st.write("目标基因")
            st.dataframe(targets, hide_index=True, width="stretch")
            st.caption("背景为DEMO_001至DEMO_100；每连续10个基因组成一个集合，完整输入将随结果包导出。")
        if st.button("2 · 运行真实计算", type="primary", key="first_run"):
            result, diagnostics, record, tables = run_first_experiment(hits)
            st.session_state["first_experiment"] = {"hits": hits, "result": result, "record": record, "tables": tables}
        run = st.session_state.get("first_experiment")
        if not run:
            st.caption("点击运行后才会产生结果。先猜一猜：重叠数增加时，集合1的富集证据会怎样变化？")
            return
        if run["hits"] != hits:
            st.info("输入已改变，旧结果和下载已隐藏。请重新运行，避免把旧结果当成新结果。")
            return
        result, record = run["result"], run["record"]
        first = result.loc[result.term_id == "DEMO_SET_01"].iloc[0]
        st.markdown("**3 · 读结果**：集合1随机期望命中2个（20×10/100），本次实际命中" + str(hits) + "个。")
        cols = st.columns(3)
        cols[0].metric("集合1富集倍数", f"{first.fold_enrichment:.2f}")
        cols[1].metric("集合1原始P值", f"{first.p_value:.3g}")
        cols[2].metric("集合1 BH校正P值", f"{first.p_adjust:.3g}")
        st.caption("倍数表示相对背景的集中程度；P值不是治疗有效概率。BH在全部10个集合上计算，零命中集合也包含在内。")
        st.dataframe(result[["term_id", "count", "term_size", "p_value", "p_adjust", "fold_enrichment"]], hide_index=True, width="stretch")
        check = record["reference_check"]
        st.caption(f"数值复核：用独立组合公式核对集合1原始P值，绝对差 {check['absolute_error']:.2e}（容差1e-12）。仅验证此模拟输入的数值实现。")
        answer = st.radio("这份结果能支持哪种表述？", ["该复方已被证明能治疗疾病", "在给定模拟背景与注释下，描述目标基因的集合富集；不能推断疗效"], index=None, key=f"first_interpret_{hits}")
        if answer:
            if answer.startswith("在给定"):
                st.success("解释正确。下一步用课程规范准备真实来源、背景和注释，再开展分析。")
            else:
                st.error("这里没有真实药材、疾病或疗效数据；统计富集不能支持治疗结论。请重新解释。")
        export_record = dict(record, interpretation_answer=answer,
                             interpretation_correct=bool(answer and answer.startswith("在给定")))
        st.download_button("4 · 下载输入、全部结果与复算记录（ZIP）", result_zip(run["tables"], export_record), "HerbInsight_first_experiment.zip", "application/zip", key="first_zip")
        st.caption("完整学习：01资料整理 → 02疾病交集 → 03PPI → 04富集。自备数据计算仍在对应课程内，无需额外入口。")
