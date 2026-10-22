"""已有五积散页面与教学入口的只读加载检查。"""
from streamlit.testing.v1 import AppTest


def test_existing_case_pages_load_without_exceptions():
    import app
    # 直接调用页面避免测试工具对segmented_control支持差异；不点击任何写入按钮。
    for page_name in app.NAVIGATION["五积散案例"] + ["报告中心", "使用指南"]:
        source = (
            "import app\n"
            "cfg = app.load_project_config('wujisan_uc')\n"
            f"app.PAGES[{page_name!r}](cfg, 'wujisan_uc')\n"
        )
        at = AppTest.from_string(source, default_timeout=45).run()
        assert not at.exception, f"{page_name}: {[e.message for e in at.exception]}"
