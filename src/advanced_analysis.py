"""Restricted, auditable MR and signature-scoring calculations."""
import numpy as np
import pandas as pd
from scipy import stats
from src.enrichment_engine import benjamini_hochberg
from src.expression_analysis import validate_expression


MR_COLUMNS = ["snp", "effect_allele_exposure", "other_allele_exposure", "beta_exposure", "se_exposure",
              "effect_allele_outcome", "other_allele_outcome", "beta_outcome", "se_outcome"]


def ivw_estimate(x, y, se):
    weight = 1 / np.square(se)
    beta = float(np.sum(weight*x*y) / np.sum(weight*x*x))
    fixed_se = float(np.sqrt(1 / np.sum(weight*x*x)))
    q = float(np.sum(weight * np.square(y-beta*x)))
    df = len(x)-1
    random_se = fixed_se * np.sqrt(max(1, q/df))
    return {"beta": beta, "se_fixed": fixed_se, "se_multiplicative_random": float(random_se),
            "p_value_random": float(2*stats.norm.sf(abs(beta/random_se))),
            "ci_low_random": float(beta-1.96*random_se), "ci_high_random": float(beta+1.96*random_se),
            "q": q, "q_df": df, "q_p_value": float(stats.chi2.sf(q, df)), "n_instruments": len(x)}


def run_mr(data, minimum_f=10):
    if not set(MR_COLUMNS) <= set(data.columns):
        raise ValueError("MR表缺少字段：" + ", ".join(sorted(set(MR_COLUMNS)-set(data.columns))))
    if not 3 <= len(data) <= 10000:
        raise ValueError("需要3–10000个候选工具变量。")
    table = data.copy()
    if table.snp.isna().any() or table.snp.astype(str).str.strip().eq("").any() or table.snp.astype(str).str.strip().duplicated().any():
        raise ValueError("SNP ID缺失或重复，请先核查。")
    for name in ("beta_exposure", "se_exposure", "beta_outcome", "se_outcome"):
        table[name] = pd.to_numeric(table[name], errors="raise")
        if not np.isfinite(table[name]).all():
            raise ValueError("效应与标准误不能缺失或为无穷值。")
    if (table.se_exposure <= 0).any() or (table.se_outcome <= 0).any():
        raise ValueError("标准误必须大于0。")
    if not np.isfinite(minimum_f) or minimum_f < 0:
        raise ValueError("F阈值须为非负有限值。")
    table["F_statistic"] = (table.beta_exposure/table.se_exposure)**2
    table["status"] = ""
    table["aligned_beta_outcome"] = np.nan
    complements = str.maketrans("ACGT", "TGCA")
    for idx, row in table.iterrows():
        alleles = [str(row[c]).strip().upper() for c in ["effect_allele_exposure", "other_allele_exposure", "effect_allele_outcome", "other_allele_outcome"]]
        ea, oa, ey, oy = alleles
        if any(a not in ("A", "C", "G", "T") for a in alleles) or ea == oa or ey == oy:
            status, sign = "excluded_invalid_or_indel_alleles", None
        elif {ea, oa} in ({"A", "T"}, {"C", "G"}):
            status, sign = "excluded_palindromic", None
        elif row.beta_exposure == 0 or row.F_statistic < minimum_f:
            status, sign = "excluded_weak_instrument", None
        elif (ea, oa) == (ey, oy):
            status, sign = "kept_same", 1
        elif (ea, oa) == (oy, ey):
            status, sign = "kept_swapped", -1
        elif (ea, oa) == (ey.translate(complements), oy.translate(complements)):
            status, sign = "kept_complement", 1
        elif (ea, oa) == (oy.translate(complements), ey.translate(complements)):
            status, sign = "kept_complement_swapped", -1
        else:
            status, sign = "excluded_allele_mismatch", None
        table.loc[idx, "status"] = status
        if sign:
            table.loc[idx, "aligned_beta_outcome"] = sign*row.beta_outcome
    kept = table[table.status.str.startswith("kept")]
    if len(kept) < 3:
        raise ValueError(f"协调并按F阈值过滤后仅{len(kept)}个工具，至少需要3个。请核对等位基因、弱工具及回文位点。")
    x, y, se = kept.beta_exposure.to_numpy(), kept.aligned_beta_outcome.to_numpy(), kept.se_outcome.to_numpy()
    summary = ivw_estimate(x, y, se)
    loo = []
    for i, snp in enumerate(kept.snp):
        mask = np.arange(len(x)) != i
        loo.append({"excluded_snp": snp, **ivw_estimate(x[mask], y[mask], se[mask])})
    return pd.DataFrame([summary]), table, pd.DataFrame(loo)


def immune_ssgsea(expression, metadata, signatures, control, case, minimum_genes=5):
    import gseapy
    matrix, aligned = validate_expression(expression, metadata, control, case)
    if len(matrix) > 20000 or matrix.shape[1] > 200:
        raise ValueError("ssGSEA当前限20000基因、200样本。")
    if not {"signature_id", "gene_symbol"} <= set(signatures):
        raise ValueError("签名表需要signature_id、gene_symbol，每行一个签名—基因关系。")
    if signatures[["signature_id", "gene_symbol"]].isna().any().any():
        raise ValueError("签名名或基因名不能为空。")
    signatures = signatures[["signature_id", "gene_symbol"]].astype(str).apply(lambda col: col.str.strip()).drop_duplicates()
    if signatures.eq("").any().any():
        raise ValueError("签名名或基因名不能为空。")
    if signatures.signature_id.nunique() > 200 or len(signatures) > 200000:
        raise ValueError("最多200个签名、200000条关系。")
    sets, coverage = {}, []
    for name, frame in signatures.groupby("signature_id"):
        all_genes = set(frame.gene_symbol)
        matched = all_genes & set(matrix.index)
        included = minimum_genes <= len(matched) < len(matrix)
        coverage.append({"signature_id": name, "total_genes": len(all_genes), "matched_genes": len(matched),
                         "coverage": len(matched)/len(all_genes), "included": included})
        if included:
            sets[name] = sorted(matched)
    if not sets:
        raise ValueError("无签名达到最小覆盖基因数（且签名不能覆盖所有表达基因）。请核查物种与ID。")
    run = gseapy.ssgsea(data=matrix, gene_sets=sets, outdir=None, min_size=minimum_genes,
                      max_size=len(matrix)-1, sample_norm_method="rank", correl_norm_type="rank",
                      weight=0.25, permutation_num=0, threads=1, no_plot=True, seed=42, verbose=False)
    scores = run.res2d[["Name", "Term", "ES", "NES"]].rename(columns={"Name":"sample_id", "Term":"signature_id", "ES":"ES", "NES":"NES"})
    scores[["ES", "NES"]] = scores[["ES", "NES"]].astype(float)
    if not np.isfinite(scores[["ES", "NES"]]).all().all():
        raise ValueError("评分归一化得到非有限值，签名或样本缺乏可比较的变化。")
    scores = scores.merge(aligned[["sample_id", "group"]], on="sample_id", validate="many_to_one")
    comparisons = []
    for name, frame in scores.groupby("signature_id"):
        a = frame.loc[frame.group == control, "NES"]
        b = frame.loc[frame.group == case, "NES"]
        u, p = stats.mannwhitneyu(b, a, alternative="two-sided", method="asymptotic")
        comparisons.append({"signature_id":name, "median_case": b.median(), "median_control": a.median(), "u":u, "p_value":p})
    comparison = pd.DataFrame(comparisons)
    comparison["p_adjust"] = benjamini_hochberg(comparison.p_value)
    return scores, comparison, pd.DataFrame(coverage)


def mr_example():
    return pd.DataFrame({"snp":["DEMO_SNP1", "DEMO_SNP2", "DEMO_SNP3", "DEMO_SNP4"],
        "effect_allele_exposure":["A"]*4, "other_allele_exposure":["C"]*4,
        "beta_exposure":[0.12,0.2,0.15,0.18], "se_exposure":[0.02]*4,
        "effect_allele_outcome":["A","C","T","A"], "other_allele_outcome":["C","A","G","C"],
        "beta_outcome":[0.06,-0.08,0.09,0.07], "se_outcome":[0.03]*4})
