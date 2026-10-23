"""Generic, session-only analysis workspace driven by a project's declared data files."""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from src.network_engine import analyze_network


REQUIRED_INPUTS = {
    "herbs": ("药材清单", ["herb_name"]),
    "compound_targets": ("药材候选靶点", ["gene_symbol"]),
    "disease_genes": ("疾病基因", ["gene_symbol"]),
}


def _read(root: Path, relative: str) -> pd.DataFrame:
    return pd.read_csv(root / relative, encoding="utf-8-sig")


def _genes(table: pd.DataFrame) -> set[str]:
    values = table["gene_symbol"].dropna().astype(str).str.strip().str.upper()
    return set(values) - {""}


def inspect_project_inputs(project_root: str | Path, config: dict) -> pd.DataFrame:
    root = Path(project_root)
    data_files = config.get("data_files", {})
    rows = []
    specifications = dict(REQUIRED_INPUTS)
    specifications["ppi_edges"] = ("PPI边表", ["source", "target"])
    for key, (label, required) in specifications.items():
        relative = data_files.get(key)
        path = root / relative if relative else None
        if not relative or not path.is_file():
            rows.append({"资料": label, "状态": "缺失", "记录数": 0, "文件": relative or "未配置"})
            continue
        table = _read(root, relative)
        missing = [column for column in required if column not in table.columns]
        rows.append({
            "资料": label,
            "状态": "字段不完整" if missing else "可用",
            "记录数": len(table),
            "文件": relative,
        })
    return pd.DataFrame(rows)


def run_project_analysis(project_root: str | Path, config: dict) -> dict:
    root = Path(project_root)
    data_files = config.get("data_files", {})
    tables = {}
    manifest = []
    for key, (label, required) in REQUIRED_INPUTS.items():
        relative = data_files.get(key)
        if not relative:
            raise ValueError(f"项目未配置{label}文件。")
        path = root / relative
        raw = path.read_bytes()
        table = _read(root, relative)
        missing = set(required) - set(table.columns)
        if missing:
            raise ValueError(f"{label}缺少字段：" + "、".join(sorted(missing)))
        tables[key] = table
        manifest.append({"资料": label, "文件": relative, "记录数": len(table), "SHA256": sha256(raw).hexdigest()})

    formula_genes = _genes(tables["compound_targets"])
    disease_genes = _genes(tables["disease_genes"])
    common_genes = sorted(formula_genes & disease_genes)
    overlap = pd.DataFrame({
        "gene_symbol": common_genes,
        "formula_name": config.get("formula_name", ""),
        "disease_name": config.get("disease_name", ""),
        "derivation": "normalized set intersection",
    })
    if overlap.empty:
        raise ValueError("标准化后没有共同基因，无法继续PPI分析。")

    ppi_relative = data_files.get("ppi_edges")
    if not ppi_relative:
        raise ValueError("项目未配置PPI边表。")
    ppi_path = root / ppi_relative
    ppi_raw = ppi_path.read_bytes()
    ppi = _read(root, ppi_relative)
    source_column = "source" if "source" in ppi.columns else "#node1" if "#node1" in ppi.columns else None
    target_column = "target" if "target" in ppi.columns else "node2" if "node2" in ppi.columns else None
    if not source_column or not target_column:
        raise ValueError("PPI边表需要 source/target 或 #node1/node2 字段。")
    source = ppi[source_column].astype(str).str.strip().str.upper()
    target = ppi[target_column].astype(str).str.strip().str.upper()
    common_set = set(common_genes)
    ppi_for_overlap = ppi[source.isin(common_set) & target.isin(common_set)].copy()
    if ppi_for_overlap.empty:
        raise ValueError("PPI边表没有覆盖当前共同基因。")
    minimum_weight = float(config.get("analysis_defaults", {}).get("ppi_minimum_weight", 0.0))
    nodes, edges, _, diagnostics = analyze_network(ppi_for_overlap, minimum_weight=minimum_weight)
    network_genes = set(nodes["node_id"].astype(str).str.strip().str.upper())
    manifest.append({"资料": "PPI边表", "文件": ppi_relative, "记录数": len(ppi), "SHA256": sha256(ppi_raw).hexdigest()})

    capabilities = pd.DataFrame([
        {"阶段": "输入检查", "状态": "完成", "平台产物": "字段、记录数与SHA256清单"},
        {"阶段": "共同靶点", "状态": "完成", "平台产物": f"{len(overlap)}个标准化交集基因"},
        {"阶段": "PPI网络", "状态": "完成", "平台产物": f"{diagnostics['node_count']}节点、{diagnostics['edge_count']}边"},
        {"阶段": "GO/KEGG", "状态": "待补输入", "平台产物": "需提供目标、背景及完整基因—条目注释"},
    ])
    return {
        "project_id": str(config.get("project_id", root.name)),
        "project_name": str(config.get("project_name", root.name)),
        "manifest": pd.DataFrame(manifest),
        "herb_count": int(tables["herbs"]["herb_name"].dropna().astype(str).str.strip().nunique()),
        "formula_gene_count": len(formula_genes),
        "disease_gene_count": len(disease_genes),
        "overlap": overlap,
        "ppi_nodes": nodes,
        "ppi_edges": edges,
        "ppi_diagnostics": diagnostics,
        "ppi_coverage": len(network_genes) / len(common_genes),
        "minimum_weight": minimum_weight,
        "capabilities": capabilities,
    }


def project_result_zip(result: dict) -> bytes:
    methods = f"""# 分析记录

- 项目：{result['project_name']}
- 共同靶点：基因符号去空值、统一大写、去重后取集合交集
- PPI阈值：{result['minimum_weight']}
- 网络：无向图；移除自环；重复边保留最高权重；计算degree、betweenness与closeness
- GO/KEGG：本次未运行，原因是项目未提供目标、背景和完整注释三类输入
- 用途：教学与科研辅助，不构成机制或疗效证明
"""
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("METHODS.md", methods.encode("utf-8"))
        for name, table in {
            "input_manifest.csv": result["manifest"],
            "target_overlap.csv": result["overlap"],
            "ppi_nodes.csv": result["ppi_nodes"],
            "ppi_edges.csv": result["ppi_edges"],
            "run_status.csv": result["capabilities"],
        }.items():
            archive.writestr(name, table.to_csv(index=False).encode("utf-8-sig"))
    return output.getvalue()


def render_project_workspace(project_root: str | Path, config: dict) -> None:
    import streamlit as st

    project_name = str(config.get("project_name", Path(project_root).name))
    st.header("分析工作台")
    st.caption("当前数据项目：" + project_name)
    st.write("从项目声明的输入出发，现场完成格式检查、共同靶点计算和PPI拓扑分析；没有输入支撑的步骤不会生成结论。")

    status = inspect_project_inputs(project_root, config)
    st.subheader("输入准备")
    st.dataframe(status, hide_index=True, width="stretch")
    ready = status[status["资料"].isin(["药材清单", "药材候选靶点", "疾病基因", "PPI边表"])]["状态"].eq("可用").all()
    state_key = "workspace_result_" + str(config.get("project_id", Path(project_root).name))
    if st.button("运行核心分析", type="primary", key="run_project_workspace", disabled=not ready):
        try:
            st.session_state[state_key] = run_project_analysis(project_root, config)
        except (FileNotFoundError, ValueError, KeyError) as error:
            st.error("分析未完成：" + str(error))

    result = st.session_state.get(state_key)
    if result is None:
        st.caption("运行后将在本页生成共同靶点、PPI节点表、边表、方法记录和可下载结果包。")
        return

    st.success("核心分析已完成。结果仅来自当前项目输入和页面所示规则。")
    first, second, third, fourth = st.columns(4)
    first.metric("药材", result["herb_count"])
    second.metric("候选靶点", result["formula_gene_count"])
    third.metric("共同靶点", len(result["overlap"]))
    fourth.metric("PPI节点", result["ppi_diagnostics"]["node_count"])

    st.subheader("运行状态与边界")
    st.dataframe(result["capabilities"], hide_index=True, width="stretch")
    st.caption(f"当前PPI输入覆盖共同靶点的{result['ppi_coverage']:.1%}。覆盖率用于描述输入完整性，不用于证明生物学重要性。")
    with st.expander("查看PPI中心性排名"):
        st.dataframe(result["ppi_nodes"].head(30), hide_index=True, width="stretch")
    st.download_button(
        "下载本次分析结果包",
        project_result_zip(result),
        result["project_id"] + "_analysis.zip",
        "application/zip",
        key="download_project_workspace",
    )

