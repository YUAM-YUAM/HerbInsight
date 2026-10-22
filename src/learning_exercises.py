"""Small, explicit error-repair activities embedded in existing courses.

All fixtures are teaching examples, not biological evidence or a live ID mapper.
"""
from datetime import datetime, timezone
import json

EXERCISES = {
    "collection": {
        "title": "纠错挑战：同一个靶点，被数了两次？",
        "task": "练习卡提供的已核对关系为 P04637 → TP53（人类）；原始列表是 P04637、TP53、UNRESOLVED_DEMO。请决定如何整理，而不是猜测未知ID。此关系仅用于本题，不提供实时UniProt查询。",
        "options": ["把三个字符串全部大写后当作三个基因", "保留原始ID与映射记录，合并已核实的TP53，未知项单独待核查", "删除所有不像基因名的记录，不保留原始表"],
        "answer": 1,
        "why": "字符去重不是生物学ID映射。只有已核实、同物种、同一ID体系的记录才可合并；未知项保留在排除/待核查清单。正式数据应下载UniProt映射结果并记录版本、日期和证据。",
        "output": [{"original_id": "P04637", "gene_symbol": "TP53", "status": "本题给定映射"}, {"original_id": "TP53", "gene_symbol": "TP53", "status": "合并前保留来源"}, {"original_id": "UNRESOLVED_DEMO", "gene_symbol": "", "status": "待核查；不进入目标集"}],
    },
    "transcriptome": {
        "title": "纠错挑战：样本数相同，分组就对了吗？",
        "task": "表达矩阵列为 S1、S2、S3、S4。分组表行依次为 S3=case、S1=control、S4=case、S2=control。直接按行贴标签会怎样？请选择修复方法。",
        "options": ["按当前行号复制分组，只要样本数相同即可", "先按组名排序，再贴到矩阵", "验证ID唯一且集合一致，再按矩阵列名匹配分组"],
        "answer": 2,
        "why": "按行号贴标签会把S1标成case、S4标成control。需要以样本ID作连接键；缺失、重复或额外ID应先解决，不能静默丢弃。",
        "output": [{"sample_id": s, "错误按行分组": wrong, "修复后分组": right} for s, wrong, right in zip(["S1", "S2", "S3", "S4"], ["case", "control", "case", "control"], ["control", "control", "case", "case"])],
    },
    "enrichment": {
        "title": "纠错挑战：背景越大，结果越可靠吗？",
        "task": "假设目标20个、命中某条目5个；条目在100个实际可检出的背景基因中有10个成员。另有900个未被检测、且不在该条目的基因。应选哪种背景？下面可比较两种计算。",
        "options": ["加入未检测的900个基因，让P值更小", "只用有机会被选入目标的可检出背景，并核对注释覆盖", "仅将20个目标基因作为背景"],
        "answer": 1,
        "why": "ORA比较目标与其抽样总体。加入不可能入选的基因会改变零假设；不能为获得显著性选择背景。真实分析还需完整条目集合及多重校正。此处只演示单条目原始P值，不是GO/KEGG结果。",
    },
    "ml": {
        "title": "纠错挑战：为什么很高的AUC仍可能不可信？",
        "task": "有人先在所有样本上筛选差异基因，再划分训练集和测试集，得到很高AUC。请选择正确的重新分析路线。",
        "options": ["保留全体样本筛选的基因，只更换随机种子", "先按独立受试者划分数据，所有学习型预处理和特征筛选放入训练集交叉验证，再一次性评估测试集", "反复查看测试AUC，挑选最高的一组基因"],
        "answer": 1,
        "why": "测试标签参与特征筛选就泄露了信息。调参、标准化和筛选均须在训练折内完成。反复依测试表现选择模型也会使测试集变成验证集；内部留出评估不等于独立外部验证。",
        "output": [{"阶段": "训练折", "允许": "拟合标准化、特征选择、模型"}, {"阶段": "验证折", "允许": "应用训练折拟合步骤并评估"}, {"阶段": "锁定测试集", "允许": "方案确定后评估，不用来选择模型"}],
    },
}


def grade_exercise(section, selected):
    item = EXERCISES[section]
    return selected == item["options"][item["answer"]]


def learning_record(state):
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "当前会话纠错练习；非考试证书、非教学效果验证；不包含上传的研究数据",
        "activities": [{"course": section, "title": item["title"], **state.get(section, {"attempts": 0, "passed": False})} for section, item in EXERCISES.items()],
    }


def learning_record_markdown(state):
    record = learning_record(state)
    lines = ["# HerbInsight 纠错学习记录", record["scope"],
             "生成时间（UTC）：" + record["generated_at_utc"],
             "首次正确与阅读反馈后改正分开记录；本记录不证明独立掌握或真实数据审核通过。"]
    for activity in record["activities"]:
        attempted = activity.get("attempts", 0)
        first = "未作答" if not attempted else ("正确" if activity.get("first_attempt_passed") else "需纠正")
        latest = "未作答" if not attempted else ("正确" if activity.get("passed") else "需纠正")
        lines.extend(["## " + activity["title"], f"首次：{first}；最近：{latest}；提交次数：{attempted}",
                      "处理依据：" + EXERCISES[activity["course"]]["why"]])
    return "\n\n".join(lines)


def render_exercise(section):
    import pandas as pd
    import streamlit as st
    if section not in EXERCISES:
        return
    item = EXERCISES[section]
    with st.expander(item["title"]):
        st.caption("约2分钟 · 练习数据，不是科研结论 · 选方案 → 看反馈 → 改正 → 下载记录")
        st.write(item["task"])
        selected = st.radio("你会怎样修复？", item["options"], index=None, key=f"repair_choice_{section}")
        if st.button("提交并检查", key=f"repair_submit_{section}"):
            if selected is None:
                st.warning("先选一个处理方案，再提交。")
            else:
                records = dict(st.session_state.get("repair_records", {}))
                previous = records.get(section, {})
                passed = grade_exercise(section, selected)
                records[section] = {"attempts": previous.get("attempts", 0) + 1, "passed": passed, "selected": selected, "first_attempt_passed": previous.get("first_attempt_passed", passed)}
                st.session_state["repair_records"] = records
        record = st.session_state.get("repair_records", {}).get(section)
        if record and record.get("selected") == selected:
            if record["passed"]:
                st.success("本次修复方案正确。接下来把这条规则用到自己的数据。")
            else:
                st.warning("这个方案仍有风险。阅读原因，再选一次。")
            st.write(item["why"])
            if "output" in item:
                st.dataframe(pd.DataFrame(item["output"]), hide_index=True, width="stretch")
            if section == "enrichment":
                from scipy.stats import hypergeom
                st.dataframe(pd.DataFrame([
                    {"背景": "实际可检出", "N": 100, "条目基因K": 10, "目标n": 20, "命中k": 5, "原始P值": float(hypergeom.sf(4, 100, 10, 20))},
                    {"背景": "额外加入未检测基因（不适用）", "N": 1000, "条目基因K": 10, "目标n": 20, "命中k": 5, "原始P值": float(hypergeom.sf(4, 1000, 10, 20))},
                ]), hide_index=True, width="stretch")
            st.caption("这里检查的是本题处理方案，不代表你的真实数据已经通过审核。")


def render_learning_record():
    import streamlit as st
    records = st.session_state.get("repair_records", {})
    passed = sum(bool(row.get("passed")) for row in records.values())
    st.caption(f"当前会话纠错练习：{passed}/{len(EXERCISES)}项最近提交正确。刷新重连可能丢失记录，请下载保存。")
    st.download_button("下载可阅读的学习记录（Markdown）", learning_record_markdown(records).encode("utf-8-sig"), "HerbInsight_learning_record.md", "text/markdown", key="download_repair_readable")
    st.download_button("下载纠错学习记录（JSON）", json.dumps(learning_record(records), ensure_ascii=False, indent=2).encode("utf-8"), "HerbInsight_learning_record.json", "application/json", key="download_repair_record")
