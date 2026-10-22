from pathlib import Path

import pandas as pd


# 项目目录
ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "projects" / "wujisan_uc"
RAW_DIR = PROJECT_DIR / "raw"
PROCESSED_DIR = PROJECT_DIR / "processed"
RESULTS_DIR = PROJECT_DIR / "results"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def read_csv_robust(file_path: Path) -> pd.DataFrame:
    """尝试使用常见编码读取 CSV。"""
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise UnicodeError(f"无法识别文件编码：{file_path}")


def save_csv(df: pd.DataFrame, file_path: Path):
    """使用适合 Excel 的编码保存 CSV。"""
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"已生成：{file_path.name}，共 {len(df)} 条记录")


def prepare_herbs_and_targets():
    """整理药材及药材候选靶点。"""
    drug_dir = RAW_DIR / "药物数据"
    drug_files = sorted(drug_dir.glob("*.csv"))

    if not drug_files:
        raise FileNotFoundError(f"没有找到药材 CSV：{drug_dir}")

    herb_records = []
    target_tables = []

    for file_path in drug_files:
        herb_name = file_path.stem

        if herb_name.endswith("sy"):
            herb_name = herb_name[:-2]

        df = read_csv_robust(file_path)

        herb_records.append(
            {
                "formula_id": "wujisan",
                "formula_name": "五积散",
                "herb_name": herb_name,
                "source_file": file_path.name,
                "species": "Homo sapiens",
            }
        )

        rename_map = {
            "Target id": "target_id",
            "Gene symbol": "gene_symbol",
            "Chromosome": "chromosome",
            "Gene name": "gene_name",
            "Protein name": "protein_name",
            "Ensembl id": "ensembl_id",
            "UniProt id": "uniprot_id",
            "P_value": "p_value",
            "FDR(BH)": "fdr_bh",
            "FDR(Bonferroni)": "fdr_bonferroni",
            "Relationship": "relationship",
            "Inferred evidence score": "evidence_score",
        }

        df = df.rename(columns=rename_map)
        df.insert(0, "herb_name", herb_name)
        df.insert(0, "formula_name", "五积散")
        df["source_file"] = file_path.name
        df["species"] = "Homo sapiens"

        if "gene_symbol" in df.columns:
            df["gene_symbol"] = (
                df["gene_symbol"]
                .astype("string")
                .str.strip()
                .str.upper()
            )

        target_tables.append(df)

    herbs = pd.DataFrame(herb_records).drop_duplicates(
        subset=["herb_name"]
    )

    compound_targets = pd.concat(
        target_tables,
        ignore_index=True,
    )

    save_csv(herbs, PROCESSED_DIR / "herbs.csv")
    save_csv(
        compound_targets,
        PROCESSED_DIR / "compound_targets.csv",
    )


def prepare_disease_genes():
    """整理 GeneCards 疾病相关基因。"""
    file_path = RAW_DIR / "疾病数据" / "genecard2.25.csv"

    if not file_path.exists():
        raise FileNotFoundError(f"找不到疾病基因文件：{file_path}")

    df = read_csv_robust(file_path)

    rename_map = {
        "Gene Symbol": "gene_symbol",
        "Description": "description",
        "Category": "category",
        "Uniprot ID": "uniprot_id",
        "Gifts": "gifts",
        "GC Id": "genecards_id",
        "Relevance score": "relevance_score",
        " GeneCards Link": "source_link",
    }

    df = df.rename(columns=rename_map)

    if "gene_symbol" in df.columns:
        df["gene_symbol"] = (
            df["gene_symbol"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    df["disease_name"] = "溃疡性结肠炎"
    df["source"] = "GeneCards"
    df["species"] = "Homo sapiens"

    save_csv(df, PROCESSED_DIR / "disease_genes.csv")


def prepare_target_overlap():
    """整理网络药理学重要共同靶点。"""
    file_path = RAW_DIR / "网药重要基因.csv"

    if not file_path.exists():
        raise FileNotFoundError(f"找不到重要基因文件：{file_path}")

    df = read_csv_robust(file_path)

    if "shared name" in df.columns:
        df = df.rename(columns={"shared name": "gene_symbol"})
    elif len(df.columns) == 1:
        df.columns = ["gene_symbol"]

    df["gene_symbol"] = (
        df["gene_symbol"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df = df.dropna(subset=["gene_symbol"])
    df = df.drop_duplicates(subset=["gene_symbol"])

    df["formula_name"] = "五积散"
    df["disease_name"] = "溃疡性结肠炎"
    df["evidence_type"] = "网络药理学共同靶点"

    save_csv(df, PROCESSED_DIR / "target_overlap.csv")


def prepare_ppi_nodes():
    """整理 Cytoscape 节点拓扑数据。"""
    file_path = RAW_DIR / "Cytoscape数据.csv"

    if not file_path.exists():
        raise FileNotFoundError(f"找不到网络数据：{file_path}")

    df = read_csv_robust(file_path)

    rename_map = {
        "name": "gene_symbol",
        "shared name": "shared_name",
        "Degree unDir": "degree",
        "Betweenness unDir": "betweenness",
        "Closeness unDir": "closeness",
    }

    df = df.rename(columns=rename_map)

    if "gene_symbol" in df.columns:
        df["gene_symbol"] = (
            df["gene_symbol"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    save_csv(df, PROCESSED_DIR / "ppi_nodes.csv")


def ratio_to_number(value):
    """把 52/191 转换为数值。"""
    try:
        numerator, denominator = str(value).split("/")
        return float(numerator) / float(denominator)
    except (ValueError, ZeroDivisionError):
        return None


def prepare_enrichment():
    """整理 GO 和 KEGG 富集结果。"""
    files = [
        (
            RAW_DIR / "GO显著富集结果.txt",
            RESULTS_DIR / "go_enrichment.csv",
        ),
        (
            RAW_DIR / "KEGG显著富集结果.txt",
            RESULTS_DIR / "kegg_enrichment.csv",
        ),
    ]

    for input_file, output_file in files:
        if not input_file.exists():
            raise FileNotFoundError(
                f"找不到富集结果：{input_file}"
            )

        df = pd.read_csv(input_file, sep="\t")

        rename_map = {
            "ID": "term_id",
            "Description": "term_name",
            "GeneRatio": "gene_ratio_text",
            "BgRatio": "background_ratio",
            "RichFactor": "rich_factor",
            "FoldEnrichment": "fold_enrichment",
            "pvalue": "p_value",
            "p.adjust": "p_adjust",
            "qvalue": "q_value",
            "geneID": "gene_list",
            "Count": "count",
        }

        df = df.rename(columns=rename_map)

        if "gene_ratio_text" in df.columns:
            df["gene_ratio"] = df[
                "gene_ratio_text"
            ].apply(ratio_to_number)

        save_csv(df, output_file)


def main():
    print("=" * 60)
    print("开始整理五积散—溃疡性结肠炎项目数据")
    print("=" * 60)

    prepare_herbs_and_targets()
    prepare_disease_genes()
    prepare_target_overlap()
    prepare_ppi_nodes()
    prepare_enrichment()

    print("=" * 60)
    print("数据标准化完成")
    print("说明：目前只有 PPI 节点数据，尚未导入 PPI 边数据。")
    print("=" * 60)


if __name__ == "__main__":
    main()