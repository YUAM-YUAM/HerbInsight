"""Competition-facing product landing page with a short, verifiable user journey."""


def render_product_home(start_demo, start_learning, open_case) -> None:
    import streamlit as st

    st.markdown(
        """
        <div style="padding:2.2rem 2.4rem;border-radius:1.5rem;
                    background:linear-gradient(135deg,#123b34 0%,#256c5c 68%,#d7b56d 140%);
                    color:white;margin-bottom:1.2rem;box-shadow:0 14px 35px rgba(18,59,52,.16)">
          <div style="font-size:.82rem;letter-spacing:.12em;opacity:.78">HERBINSIGHT · 中药复方机制学习与分析</div>
          <div style="font-size:2.35rem;font-weight:760;line-height:1.18;margin:.55rem 0">让初学者看懂流程，也能亲手完成分析</div>
          <div style="font-size:1.05rem;max-width:52rem;line-height:1.75;opacity:.92">
            将资料检索规范、真实算法计算、五积散案例解读和可追溯结果包连接成一条完整学习路径。
            面向刚接触网络药理学与多组学分析的中医药和生命科学学习者。
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    action, learn, case = st.columns(3)
    action.button("运行测试项目", key="home_start_demo", type="primary", width="stretch", on_click=start_demo)
    learn.button("进入教学路线", key="home_start_learning", width="stretch", on_click=start_learning)
    case.button("查看五积散案例", key="home_open_case", width="stretch", on_click=open_case)

    st.subheader("作品解决什么问题")
    st.write(
        "传统教程通常把数据库检索、文件整理、网站操作和结果图片分散在不同位置；"
        "初学者知道要做PPI或富集，却不知道该下载什么、表格怎样整理、算法输入是否合格。"
        "HerbInsight把每一步的资料标准、人工操作、在线计算、结果解释和研究边界放在同一工作流中。"
    )

    first, second, third = st.columns(3)
    with first.container(border=True):
        st.markdown("#### 学得会")
        st.write("按资料检索、疾病基因、PPI、GO/KEGG逐步学习；每一步说明来源、字段、软件和交付文件。")
    with second.container(border=True):
        st.markdown("#### 算得出")
        st.write("在网页内执行交集和网络拓扑等真实计算，保留参数、方法和输入指纹，不用只看静态图片。")
    with third.container(border=True):
        st.markdown("#### 查得到")
        st.write("结果与来源文件、规则和限制对应；材料不足时明确停止，避免把关联结果包装成机制或疗效证明。")

    st.subheader("三分钟可验证路径")
    st.markdown(
        """
1. 点击 **运行测试项目**，系统载入独立项目“由我来测试”。
2. 查看平台识别出的四类输入文件，点击 **运行核心分析**。
3. 检查共同靶点、PPI网络规模、中心性排名与输入覆盖率。
4. 下载结果包，核对输入清单、SHA256、方法记录及CSV结果。
        """
    )

    with st.expander("作品创新与原创贡献", expanded=False):
        st.markdown(
            """
- **教学与计算一体化**：课程不止告诉用户点哪个网站，而是明确“收集什么—保留什么—整理成什么—如何计算”。
- **同屏案例对照**：五积散案例嵌入对应操作步骤，帮助学习者把抽象字段和真实研究资料联系起来。
- **证据链交付**：分析输出同时包含数据表、参数、方法和限制，强调可复核性而非只生成图片。
- **研究边界设计**：区分教学示例、计算结果、案例关联与科学验证，避免功能数量替代结论质量。
            """
        )
    with st.expander("数据、第三方资源与AI使用说明", expanded=False):
        st.markdown(
            """
- 五积散资料来源于团队前期整理的公开数据库与分析文件；具体数据库、检索字段和整理要求在课程及项目文件中标注。
- 平台使用 Python、Streamlit、pandas、NetworkX、SciPy 与 scikit-learn 等开源技术组件，第三方数据库数据仍遵循其原许可与引用要求。
- 开发过程使用了AI辅助编程。功能定义、研究流程、数据选择、结果核查和最终取舍由参赛者负责；提交材料中应继续如实列明工具名称、使用环节和人工修改过程。
- 平台用于教学与科研辅助，不用于临床诊断、治疗决策或未经验证的疗效宣传。
            """
        )

