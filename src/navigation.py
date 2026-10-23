"""按任务直接导航；稳定路由用于刷新和收藏，不依赖横向标签页。"""

NAV_GROUPS = {
    "开始使用": [
        ("home", "作品首页", "作品首页", None),
        ("workspace", "分析工作台", "分析工作台", None),
    ],
    "核心学习与实训": [
        ("learn_home", "学习路线", "网络药理学操作课程", "overview"),
        ("learn_collection", "01 资料检索与ID整理", "网络药理学操作课程", "collection"),
        ("learn_disease", "02 疾病基因与交集", "网络药理学操作课程", "disease"),
        ("learn_ppi", "03 PPI构图", "网络药理学操作课程", "ppi"),
        ("learn_enrichment", "04 GO/KEGG富集", "网络药理学操作课程", "enrichment"),
    ],
    "进阶证据（按需选学）": [
        ("learn_transcriptome", "转录组数据与设计", "网络药理学操作课程", "transcriptome"),
        ("learn_ml", "机器学习与评估", "网络药理学操作课程", "ml"),
        ("learn_immune", "免疫微环境", "网络药理学操作课程", "immune"),
        ("learn_mr", "孟德尔随机化", "网络药理学操作课程", "mr"),
        ("learn_single_cell", "单细胞与细胞通讯", "网络药理学操作课程", "single_cell"),
        ("learn_perturbation", "计算扰动与虚拟敲除", "网络药理学操作课程", "perturbation"),
    ],
    "案例解读（当前项目）": [
        ("case_home", "项目概览", "项目首页", None),
        ("case_herbs", "药材与靶点", "药材-候选靶点", None),
        ("case_overlap", "疾病基因与交集", "疾病基因与交集", None),
        ("case_ppi", "PPI网络结果", "网络药理学 / PPI", None),
        ("case_transcriptome", "转录组结果", "转录组验证", None),
        ("case_ml", "机器学习结果", "机器学习结果", None),
        ("case_mr", "MR结果", "孟德尔随机化", None),
        ("case_immune", "免疫微环境结果", "免疫微环境证据", None),
        ("case_evidence", "综合证据", "综合证据", None),
    ],
    "项目工具": [
        ("resources", "资料模板与交付自查", "网络药理学操作课程", "resources"),
        ("project_manager", "项目管理", "项目管理", None),
        ("project_report", "项目报告", "报告中心", None),
        ("project_guide", "使用指南", "使用指南", None),
        ("learning_center", "平台能力总览", "教学实训中心", None),
        ("lesson_steps", "8步简明课程", "网络药理学操作课程", "lessons"),
    ],
}

ROUTES = {route[0]: (group, *route[1:]) for group, routes in NAV_GROUPS.items() for route in routes}
ROUTES["project_create"] = ("项目工具", "新建学习任务", "新建学习任务", None)
DEFAULT_ROUTE = "home"
COURSE_ORDER = ["learn_home", "learn_collection", "learn_disease", "learn_ppi", "learn_enrichment", "learn_transcriptome", "learn_ml", "learn_immune", "learn_mr", "learn_single_cell", "learn_perturbation", "resources"]


def resolve_route(route_id):
    """未知或过期书签安全返回学习路线，不把URL当作代码/路径使用。"""
    if route_id == "lab_network":
        return "learn_ppi"
    if route_id == "lab_enrichment":
        return "learn_enrichment"
    return route_id if isinstance(route_id, str) and route_id in ROUTES else DEFAULT_ROUTE


def course_neighbors(route_id):
    if route_id not in COURSE_ORDER:
        return None, None
    index = COURSE_ORDER.index(route_id)
    return (COURSE_ORDER[index - 1] if index else None,
            COURSE_ORDER[index + 1] if index + 1 < len(COURSE_ORDER) else None)
