from pathlib import Path

from src.blind_demo import benchmark_report, benchmark_zip, run_blind_benchmark
from tests.ui_helpers import open_route


REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "projects" / "my_test"


def test_blind_benchmark_is_deterministic_and_honest():
    first = run_blind_benchmark(ROOT)
    second = run_blind_benchmark(ROOT)
    assert first["manifest"].equals(second["manifest"])
    assert first["blind_overlap"].equals(second["blind_overlap"])
    assert len(first["blind_overlap"]) > first["archived_overlap_count"] > 0
    assert first["archived_subset"] is True
    assert len(first["unexplained_exclusions"]) == len(first["blind_overlap"]) - first["archived_overlap_count"]
    statuses = dict(zip(first["capabilities"]["环节"], first["capabilities"]["状态"]))
    assert statuses["GO/KEGG ORA"] == "暂不可独立重算"
    assert "不会为了接近参考数量而调整结果" in benchmark_report(first)
    assert benchmark_zip(first)[:2] == b"PK"
    source = (REPO / "src" / "blind_demo.py").read_text(encoding="utf-8").lower()
    assert "wujisan" not in source and "1047" not in source and "191" not in source


def test_blind_demo_route_requires_explicit_run():
    at = open_route("blind_demo")
    assert not at.exception
    assert at.session_state["active_project"] == "my_test"
    assert "blind_result_my_test" not in at.session_state
    assert any(button.key == "run_project_blind_demo" for button in at.button)
    at.button(key="run_project_blind_demo").click().run()
    assert not at.exception
    result = at.session_state["blind_result_my_test"]
    assert result["project_name"] == "由我来测试"
    assert len(result["blind_overlap"]) > 0
    assert any("平台能力审计" in heading.value for heading in at.subheader)
