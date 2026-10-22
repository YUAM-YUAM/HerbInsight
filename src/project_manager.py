from datetime import date
from io import BytesIO
from pathlib import Path
import re

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
PROJECTS_DIR = ROOT / "projects"


SUPPORTED_MODULES = [
    "herbs",
    "target_overlap",
    "ppi",
    "enrichment",
    "transcriptome",
    "machine_learning",
    "mendelian_randomization",
    "immune_infiltration",
    "integrated_evidence",
]


STANDARD_FILES = {
    "herbs": {
        "path": "processed/herbs.csv",
        "required_columns": [
            "formula_name",
            "herb_name",
        ],
        "description": "复方药材清单",
    },
    "compound_targets": {
        "path": "processed/compound_targets.csv",
        "required_columns": [
            "formula_name",
            "herb_name",
            "gene_symbol",
        ],
        "description": "药材候选靶点",
    },
    "disease_genes": {
        "path": "processed/disease_genes.csv",
        "required_columns": [
            "gene_symbol",
            "disease_name",
        ],
        "description": "疾病相关基因",
    },
    "target_overlap": {
        "path": "processed/target_overlap.csv",
        "required_columns": [
            "gene_symbol",
            "formula_name",
            "disease_name",
        ],
        "description": "复方—疾病共同靶点",
    },
}


def normalize_project_id(project_id):
    """将项目编号转换为安全的小写格式。"""
    normalized = str(project_id).strip().lower()
    normalized = normalized.replace(" ", "_")
    normalized = re.sub(r"[^a-z0-9_-]", "", normalized)
    return normalized


def validate_project_id(project_id):
    """
    校验项目编号。

    项目编号必须：
    1. 以英文字母开头；
    2. 仅包含小写字母、数字、下划线或短横线；
    3. 长度为3至50个字符。
    """
    normalized = normalize_project_id(project_id)

    if not re.fullmatch(
        r"[a-z][a-z0-9_-]{2,49}",
        normalized,
    ):
        raise ValueError(
            "项目编号必须以英文字母开头，长度为3至50个字符，"
            "并且只能包含小写字母、数字、下划线或短横线。"
        )

    return normalized


def get_project_dir(project_id):
    """返回经过安全校验的项目目录。"""
    safe_id = validate_project_id(project_id)

    project_dir = (
        PROJECTS_DIR / safe_id
    ).resolve()

    projects_root = PROJECTS_DIR.resolve()

    if projects_root not in project_dir.parents:
        raise ValueError("项目路径超出允许范围。")

    return project_dir


def create_project(
    project_id,
    project_name,
    formula_name,
    disease_name,
    species="Homo sapiens",
):
    """创建新的通用复方—疾病分析项目。"""
    safe_id = validate_project_id(project_id)
    project_dir = get_project_dir(safe_id)
    config_path = project_dir / "project.yaml"

    if config_path.exists():
        raise FileExistsError(
            f"项目 {safe_id} 已经存在，不能重复创建。"
        )

    for folder in [
        "raw",
        "processed",
        "results",
        "documents",
    ]:
        (project_dir / folder).mkdir(
            parents=True,
            exist_ok=True,
        )

    config = {
        "project_id": safe_id,
        "project_name": str(project_name).strip(),
        "formula_name": str(formula_name).strip(),
        "disease_name": str(disease_name).strip(),
        "species": str(species).strip(),
        "version": "1.0",
        "created_date": date.today().isoformat(),
        "modules": SUPPORTED_MODULES.copy(),
        "data_files": {},
        "disclaimer": (
            "本系统用于科研辅助和教育展示，不用于临床诊断、"
            "治疗决策或未经验证的疗效宣传。"
        ),
    }

    with config_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        yaml.safe_dump(
            config,
            file,
            allow_unicode=True,
            sort_keys=False,
        )

    return project_dir


def load_project_config(project_id):
    """读取项目配置。"""
    project_dir = get_project_dir(project_id)
    config_path = project_dir / "project.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"未找到项目配置：{config_path}"
        )

    with config_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return yaml.safe_load(file)


def save_project_config(project_id, config):
    """安全保存项目配置。"""
    project_dir = get_project_dir(project_id)
    config_path = project_dir / "project.yaml"

    with config_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        yaml.safe_dump(
            config,
            file,
            allow_unicode=True,
            sort_keys=False,
        )


def register_data_file(
    project_id,
    file_key,
    relative_path,
):
    """把数据文件登记到 project.yaml。"""
    config = load_project_config(project_id)

    if "data_files" not in config:
        config["data_files"] = {}

    config["data_files"][file_key] = (
        str(relative_path).replace("\\", "/")
    )

    save_project_config(project_id, config)


def read_uploaded_table(file_name, file_bytes):
    """读取用户上传的 CSV 或 Excel 表格。"""
    suffix = Path(file_name).suffix.lower()
    file_buffer = BytesIO(file_bytes)

    if suffix in [".xlsx", ".xls"]:
        return pd.read_excel(file_buffer)

    if suffix != ".csv":
        raise ValueError(
            "仅支持 CSV、XLSX 或 XLS 文件。"
        )

    encodings = [
        "utf-8-sig",
        "utf-8",
        "gb18030",
    ]

    last_error = None

    for encoding in encodings:
        try:
            file_buffer.seek(0)
            return pd.read_csv(
                file_buffer,
                encoding=encoding,
            )
        except UnicodeDecodeError as error:
            last_error = error

    raise ValueError(
        "无法识别CSV文件编码，请将文件另存为UTF-8格式。"
    ) from last_error


def validate_standard_table(file_key, dataframe):
    """检查上传表格是否包含平台要求的标准字段。"""
    if file_key not in STANDARD_FILES:
        raise KeyError(
            f"不支持的数据类型：{file_key}"
        )

    required_columns = STANDARD_FILES[
        file_key
    ]["required_columns"]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "缺少必需字段："
            + "、".join(missing_columns)
        )

    if dataframe.empty:
        raise ValueError("上传的数据表不能为空。")

    return True


def save_uploaded_table(
    project_id,
    file_key,
    file_name,
    file_bytes,
):
    """
    校验并保存上传的数据表。

    所有表格统一转换为UTF-8编码CSV，
    并登记到project.yaml。
    """
    if file_key not in STANDARD_FILES:
        raise KeyError(
            f"不支持的数据类型：{file_key}"
        )

    dataframe = read_uploaded_table(
        file_name,
        file_bytes,
    )

    validate_standard_table(
        file_key,
        dataframe,
    )

    project_dir = get_project_dir(project_id)
    relative_path = STANDARD_FILES[
        file_key
    ]["path"]
    output_path = project_dir / relative_path

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    register_data_file(
        project_id,
        file_key,
        relative_path,
    )

    return {
        "file_key": file_key,
        "output_path": output_path,
        "row_count": len(dataframe),
        "column_count": len(dataframe.columns),
        "columns": dataframe.columns.tolist(),
    }


def build_target_overlap(project_id):
    """
    根据药材候选靶点与疾病基因，
    自动生成复方—疾病共同靶点表。
    """
    config = load_project_config(project_id)
    project_dir = get_project_dir(project_id)
    data_files = config.get("data_files", {})

    compound_path = data_files.get(
        "compound_targets"
    )
    disease_path = data_files.get(
        "disease_genes"
    )

    if not compound_path or not disease_path:
        raise FileNotFoundError(
            "请先上传药材候选靶点和疾病相关基因。"
        )

    compound_targets = pd.read_csv(
        project_dir / compound_path,
        encoding="utf-8-sig",
    )
    disease_genes = pd.read_csv(
        project_dir / disease_path,
        encoding="utf-8-sig",
    )

    validate_standard_table(
        "compound_targets",
        compound_targets,
    )
    validate_standard_table(
        "disease_genes",
        disease_genes,
    )

    compound_symbols = (
        compound_targets["gene_symbol"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
    )

    disease_symbols = (
        disease_genes["gene_symbol"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
    )

    common_genes = sorted(
        set(compound_symbols)
        & set(disease_symbols)
    )

    overlap = pd.DataFrame(
        {
            "gene_symbol": common_genes,
            "formula_name": config.get(
                "formula_name",
                "",
            ),
            "disease_name": config.get(
                "disease_name",
                "",
            ),
            "evidence_type": (
                "网络药理学共同靶点"
            ),
        }
    )

    relative_path = STANDARD_FILES[
        "target_overlap"
    ]["path"]
    output_path = project_dir / relative_path

    overlap.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    register_data_file(
        project_id,
        "target_overlap",
        relative_path,
    )

    return overlap


def get_project_data_status(project_id):
    """返回项目基础数据文件状态。"""
    config = load_project_config(project_id)
    project_dir = get_project_dir(project_id)
    data_files = config.get("data_files", {})

    status_rows = []

    for file_key, specification in (
        STANDARD_FILES.items()
    ):
        relative_path = data_files.get(file_key)
        exists = bool(
            relative_path
            and (project_dir / relative_path).exists()
        )

        status_rows.append(
            {
                "file_key": file_key,
                "description": specification[
                    "description"
                ],
                "required_columns": "、".join(
                    specification[
                        "required_columns"
                    ]
                ),
                "registered_path": (
                    relative_path or "未登记"
                ),
                "status": (
                    "已上传"
                    if exists
                    else "待上传"
                ),
            }
        )

    return pd.DataFrame(status_rows)


if __name__ == "__main__":
    print(
        "project_manager.py 已就绪，"
        "请通过网页项目管理页面调用。"
    )