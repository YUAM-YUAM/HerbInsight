from pathlib import Path

from src.blind_demo import benchmark_report, benchmark_zip, run_blind_benchmark
from tests.ui_helpers import open_route


ROOT = Path(__file__).resolve().parents[1] / "projects" / "wujisan_uc"


def test_blind_benchmark_is_deterministic_and_honest():
    first = run_blind_benchmark(ROOT)
    second = run_blind_benchmark(ROOT)
    assert first["manifest"].equals(second["manifest"])
    assert first["blind_overlap"].equals(second["blind_overlap"])
    assert len(first["blind_overlap"]) == 1047
    assert first["archived_overlap_count"] == 191
    assert first["archived_subset"] is True
    assert len(first["unexplained_exclusions"]) == 856
    statuses = dict(zip(first["capabilities"]["环节"], first["capabilities"]["状态"]))
    assert statuses["GO/KEGG ORA"] == "暂不可独立重算"
    assert "不会把1047个结果强行调整为191个" in benchmark_report(first)
    assert benchmark_zip(first)[:2] == b"PK"


def test_blind_demo_route_requires_explicit_run():
    at = open_route("blind_demo")
    assert not at.exception
    assert "wujisan_blind_result" not in at.session_state
    assert any(button.key == "run_wujisan_blind_demo" for button in at.button)
    at.button(key="run_wujisan_blind_demo").click().run()
    assert not at.exception
    assert len(at.session_state["wujisan_blind_result"]["blind_overlap"]) == 1047
    assert any("平台能力审计" in heading.value for heading in at.subheader)
