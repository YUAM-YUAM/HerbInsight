from pathlib import Path

import yaml

from src.project_workspace import inspect_project_inputs, project_result_zip, run_project_analysis
from tests.ui_helpers import open_route


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "my_test"


def _config():
    return yaml.safe_load((PROJECT / "project.yaml").read_text(encoding="utf-8"))


def test_competition_demo_is_input_only_and_reproducible():
    config = _config()
    assert config["project_name"] == "由我来测试"
    assert config["project_type"] == "competition_demo"
    assert not (PROJECT / "reference").exists()
    status = inspect_project_inputs(PROJECT, config)
    assert status["状态"].eq("可用").all()
    first = run_project_analysis(PROJECT, config)
    second = run_project_analysis(PROJECT, config)
    assert first["overlap"].equals(second["overlap"])
    assert first["ppi_nodes"].equals(second["ppi_nodes"])
    assert len(first["overlap"]) > 0
    assert first["ppi_diagnostics"]["node_count"] > 0
    assert project_result_zip(first)[:2] == b"PK"


def test_judge_path_reaches_and_runs_workspace():
    at = open_route("home")
    assert any("让初学者看懂流程" in markdown.value for markdown in at.markdown)
    at.button(key="home_start_demo").click().run()
    assert not at.exception
    assert at.query_params["view"] == "workspace"
    assert at.session_state["active_project"] == "my_test"
    assert any("当前数据项目：由我来测试" in caption.value for caption in at.caption)
    at.button(key="run_project_workspace").click().run()
    assert not at.exception
    result = at.session_state["workspace_result_my_test"]
    assert len(result["overlap"]) > 0
    assert any("核心分析已完成" in success.value for success in at.success)
