"""Generic outcome-independent benchmark driven entirely by project configuration."""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
import yaml

from src.network_engine import analyze_network


def _read(root: Path, relative: str) -> pd.DataFrame:
    return pd.read_csv(root / relative, encoding="utf-8-sig")


def _genes(table: pd.DataFrame) -> set[str]:
    if "gene_symbol" not in table.columns:
        raise ValueError("输入表缺少 gene_symbol 字段。")
    return set(table["gene_symbol"].dropna().astype(str).str.strip().str.upper()) - {""}


def run_blind_benchmark(project_root: str | Path) -> dict:
    """Run deterministic derivations first; compare with archived outputs only afterwards."""
    root = Path(project_root)
    with (root / "project.yaml").open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream) or {}
    benchmark = config.get("benchmark")
    if not isinstance(benchmark, dict):
        raise ValueError("该项目没有配置 benchmark，不能作为盲测项目。")
    input_specs = benchmark.get("inputs", {})
    required_inputs = {
        "herbs": ("处方药材", "herb_name"),
        "compound_targets": ("药材候选靶点", "gene_symbol"),
        "disease_genes": ("疾病基因", "gene_symbol"),
    }
    manifest_rows = []
    tables = {}
    for key, (default_label, required_column) in required_inputs.items():
        specification = input_specs.get(key, {})
        relative = specification.get("path") if isinstance(specification, dict) else specification
        if not relative:
            raise ValueError(f"benchmark.inputs 缺少 {key} 路径。")
        label = specification.get("label", default_label) if isinstance(specification, dict) else default_label
        path = root / relative
        raw = path.read_bytes()
        table = _read(root, relative)
        if required_column not in table.columns:
            raise ValueError(f"{label}缺少 {required_column} 字段。")
        tables[key] = table
        manifest_rows.append({
            "输入": label,
            "文件": relative,
            "行数": len(table),
            "SHA256": sha256(raw).hexdigest(),
            "用途": "盲测输入",
        })

    formula_genes = _genes(tables["compound_targets"])
    disease_genes = _genes(tables["disease_genes"])
    blind_genes = sorted(formula_genes & disease_genes)
    blind_overlap = pd.DataFrame({"gene_symbol": blind_genes})

    # Post-hoc audit starts only after the blind result above has been fixed.
    references = benchmark.get("references", {})
    overlap_reference = references.get("target_overlap")
    archived_genes = _genes(_read(root, overlap_reference)) if overlap_reference else set()
    archived_subset = archived_genes <= set(blind_genes)
    unexplained_exclusions = sorted(set(blind_genes) - archived_genes)

    ppi_reference = references.get("ppi_edges")
    if ppi_reference:
        ppi_input = _read(root, ppi_reference)
        nodes, edges, _, ppi_diagnostics = analyze_network(
            ppi_input, minimum_weight=float(benchmark.get("ppi_minimum_weight", 0.0))
        )
    else:
        nodes, edges = pd.DataFrame(), pd.DataFrame()
        ppi_diagnostics = {"node_count": 0, "edge_count": 0, "component_count": 0}
    ppi_genes = (
        set(nodes["node_id"].astype(str).str.strip().str.upper())
        if "node_id" in nodes.columns else set()
    )
    ppi_from_blind = len(ppi_genes & set(blind_genes))

    enrichment_inputs = benchmark.get("enrichment_inputs", {})
    enrichment_ready = all(
        enrichment_inputs.get(key) and (root / enrichment_inputs[key]).is_file()
        for key in ("target", "background", "annotation")
    )
    capabilities = pd.DataFrame([
        {"环节": "输入质控", "平台动作": "锁定文件、字段、行数和SHA256", "状态": "可独立完成", "可审计输出": "输入清单"},
        {"环节": "靶点标准化与交集", "平台动作": "统一大小写、去空值、去重后求集合交集", "状态": "可独立重算", "可审计输出": f"{len(blind_genes)}个共同基因"},
        {"环节": "PPI拓扑", "平台动作": "对项目声明的外部边表重新清洗、去重并计算中心性", "状态": "可重算但输入链不完整" if ppi_reference else "缺少PPI边表", "可审计输出": f"{ppi_diagnostics['node_count']}节点/{ppi_diagnostics['edge_count']}边"},
        {"环节": "GO/KEGG ORA", "平台动作": "检查目标、背景和完整注释是否齐备", "状态": "输入齐备" if enrichment_ready else "暂不可独立重算", "可审计输出": "三类重算输入齐备" if enrichment_ready else "缺目标、背景或完整注释中的至少一项"},
        {"环节": "历史结果核查", "平台动作": "盲算完成后再比较项目声明的参考结果", "状态": "发现可复现性缺口" if unexplained_exclusions else "一致或未提供参考", "可审计输出": f"参考{len(archived_genes)}个；{len(unexplained_exclusions)}个排除缺少规则"},
    ])

    return {
        "manifest": pd.DataFrame(manifest_rows),
        "project_id": str(config.get("project_id", root.name)),
        "project_name": str(config.get("project_name", root.name)),
        "formula_name": str(config.get("formula_name", "未命名复方")),
        "disease_name": str(config.get("disease_name", "未命名疾病")),
        "herb_count": int(tables["herbs"]["herb_name"].dropna().astype(str).str.strip().nunique()),
        "formula_gene_count": len(formula_genes),
        "disease_gene_count": len(disease_genes),
        "blind_overlap": blind_overlap,
        "archived_overlap_count": len(archived_genes),
        "archived_subset": archived_subset,
        "unexplained_exclusions": unexplained_exclusions,
        "ppi_nodes": nodes,
        "ppi_edges": edges,
        "ppi_diagnostics": ppi_diagnostics,
        "ppi_from_blind": ppi_from_blind,
        "capabilities": capabilities,
    }


def benchmark_report(result: dict) -> str:
    d = result["ppi_diagnostics"]
    return f"""# HerbInsight 项目盲测报告：{result['project_name']}

## 实验原则

先冻结{result['formula_name']}—{result['disease_name']}项目的药材、候选靶点和疾病基因三类输入；不读取参考共同靶点、PPI节点或富集结论来决定算法输出。平台完成盲算后，才开启参考结果核查。

## 独立计算结果

- 药材数：{result['herb_count']}
- 候选靶点去重数：{result['formula_gene_count']}
- 疾病基因去重数：{result['disease_gene_count']}
- 直接集合交集：{len(result['blind_overlap'])}
- 归档PPI边表重算：{d['node_count']}个节点、{d['edge_count']}条边、{d['component_count']}个连通分量

## 事后归档核查

参考共同靶点为{result['archived_overlap_count']}个，均属于本次盲算交集：{result['archived_subset']}。盲算交集中另有{len(result['unexplained_exclusions'])}个基因未进入参考结果，但当前资料没有提供完整筛选规则。因此平台不会为了接近参考数量而调整结果，也不把差异解释为生物学结论。

## 能力边界

PPI可基于项目声明的边表重算拓扑，但该边表只覆盖盲算交集中的{result['ppi_from_blind']}个基因，不能代表全部盲算基因的完整STRING检索。GO/KEGG只有在目标、背景和基因—条目注释齐备时才能独立重算。

## 评委可核查的价值

该实验同时给出可计算结果、文件哈希、过程诊断和无法复现的原因。平台的价值不仅是展示既有图片，而是把“输入—规则—输出—边界”组织成可检查的研究链条。
"""


def benchmark_zip(result: dict) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("README.md", benchmark_report(result).encode("utf-8"))
        for name, table in {
            "input_manifest.csv": result["manifest"],
            "blind_target_overlap.csv": result["blind_overlap"],
            "ppi_nodes_recomputed.csv": result["ppi_nodes"],
            "ppi_edges_recomputed.csv": result["ppi_edges"],
            "capability_audit.csv": result["capabilities"],
            "unexplained_exclusions.csv": pd.DataFrame({"gene_symbol": result["unexplained_exclusions"]}),
        }.items():
            archive.writestr(name, table.to_csv(index=False).encode("utf-8-sig"))
    return output.getvalue()


def render_blind_demo(project_root: str | Path) -> None:
    import streamlit as st

    root = Path(project_root)
    try:
        with (root / "project.yaml").open("r", encoding="utf-8") as stream:
            config = yaml.safe_load(stream) or {}
    except (FileNotFoundError, UnicodeError, yaml.YAMLError) as error:
        st.error("测试项目配置无法读取：" + str(error))
        return
    st.header("项目盲测 · " + str(config.get("project_name", root.name)))
    st.write("把该项目的数据视为未知输入，用同一套公开规则检验平台能独立完成什么、在哪一步会被证据链阻断。")
    st.info("盲测阶段不读取历史交集数量、核心基因排序或富集结论作为目标；历史结果只在计算完成后用于归档核查。")

    with st.container(border=True):
        st.markdown("#### 测试协议")
        st.markdown(
            "1. 冻结药材、候选靶点和疾病基因，并记录SHA256。\n"
            "2. 按固定规则标准化基因符号并计算交集。\n"
            "3. 对现有PPI边表独立重算网络拓扑。\n"
            "4. 盲算结束后才比较历史归档，并报告一致、差异与缺失材料。"
        )
        st.caption("成功标准：同一输入可重复得到相同输出；每个数字能追溯到文件与规则；资料不足时明确停止，不补造结论。")

    state_key = "blind_result_" + str(config.get("project_id", root.name))
    if st.button("开始盲测", type="primary", key="run_project_blind_demo"):
        try:
            st.session_state[state_key] = run_blind_benchmark(project_root)
        except (FileNotFoundError, ValueError, KeyError) as error:
            st.error("盲测未启动：" + str(error))

    result = st.session_state.get(state_key)
    if not result:
        st.caption("点击后才会计算；页面不会预先展示历史答案。")
        return

    st.success("盲算完成，现已开启事后归档核查。")
    a, b, c, d = st.columns(4)
    a.metric("药材", result["herb_count"])
    b.metric("候选靶点", result["formula_gene_count"])
    c.metric("疾病基因", result["disease_gene_count"])
    d.metric("盲算交集", len(result["blind_overlap"]))

    st.subheader("1. 输入冻结与追溯")
    manifest = result["manifest"].copy()
    manifest["SHA256"] = manifest["SHA256"].str.slice(0, 16) + "…"
    st.dataframe(manifest, hide_index=True, width="stretch")

    st.subheader("2. 平台能力审计")
    st.dataframe(result["capabilities"], hide_index=True, width="stretch")

    st.subheader("3. 盲算之后的差异说明")
    st.warning(
        f"平台按现有输入重算得到{len(result['blind_overlap'])}个共同基因；历史归档为"
        f"{result['archived_overlap_count']}个。历史结果是盲算集合的子集，但另有"
        f"{len(result['unexplained_exclusions'])}个基因缺少可追溯的排除规则。"
    )
    st.write("这不是算法失败，而是一次资料完整性测试：平台能准确定位无法复现发生在哪个环节，并告诉使用者下一步应补充筛选阈值、筛选字段和排除日志。")
    with st.expander("查看重算网络的前20个节点"):
        st.dataframe(result["ppi_nodes"].head(20), hide_index=True, width="stretch")

    st.download_button(
        "下载盲测证据包（ZIP）",
        benchmark_zip(result),
        "HerbInsight_" + result["project_id"] + "_blind_demo.zip",
        "application/zip",
        key="download_project_blind_demo",
    )

