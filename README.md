# HerbInsight —— 网络药理学教学实训平台

面向初学者的中药网络药理学教学与在线实训平台，并提供多组学证据展示。
第一个示范项目：**五积散 干预 溃疡性结肠炎**。

> 本系统用于科研辅助和教育展示，不用于临床诊断、治疗决策或未经验证的疗效宣传。

## 教学与参赛改进

首页提供可折叠的“三分钟实训”：改变模拟目标集的命中数，调用正式ORA引擎计算全部10个条目、整体BH校正，解释结果并导出输入/结果/参数/版本/hash。使用独立组合公式核对集合1原始P值，仅为模拟数据的数值检查，不冒充真实公共数据复核。输入改变时隐藏旧结果；学习记录同时提供易读Markdown与JSON。

首页明确任务、准备材料、交付物及完成标准，不新增侧栏入口。资料整理、转录组、富集与机器学习课程内提供四个纠错挑战：提交方案、查看原因与修复示例、再次尝试。学习路线/资料模板页可下载当前会话JSON记录，包含首次是否正确、尝试次数和最近结果；不等于真实数据审核或教学效果证明。

`docs/`提供评审演示脚本、真人试用协议与空白记录、真实数据复核方案、原创贡献与AI使用披露模板。转录组课程已加入GSE38713真实数据再分析与论文摘要对照：11,753个基因、两项独立组间Welch比较，7个摘要具名缓解期异常基因均达到全基因BH<0.05。REG1A/CXCL8缓解期非显著不能证明正常。详见`validation/gse38713/README.md`，复算脚本为`scripts/validate_gse38713.py`。本次是同一发现数据再分析，不是独立队列验证；全文严格复现和真人试用仍待完成。

## 技术架构

Python + Streamlit + Pandas + NetworkX + Plotly

## 导航与学习入口

在线计算已并入课程操作步骤：PPI第7步可上传边表建网；GO/KEGG第6步可上传数据做ORA。侧栏不再单列两个实验室，原实验室书签会进入对应课程。

侧栏按任务分成「核心学习与实训」「进阶证据（按需选学）」「案例解读（当前项目）」「项目工具」。直接点击章节，无需先切换使用模式；项目选择在「项目与设置」中，使用声明默认折叠。教学页面只加载当前章节，顶部提供当前位置及上一节/下一节，URL中的 `view` 可用于收藏和刷新。学习路线首页提供四个阶段入口；原8步课程保留在「项目工具 → 8步简明课程」，模板及交付自查位于「项目工具 → 资料模板与交付自查」。

## 教学实训模式

平台采用“学原理—备数据—做分析—读结果—交作业”的统一教学结构。
GO/KEGG 在线实验室已支持用户上传目标基因、背景基因和功能注释表，
现场执行超几何检验与 Benjamini-Hochberg 校正，并导出结果和方法记录。
网络药理学在线实验室支持上传关系边表，现场完成数据清洗、网络构建、
中心性计算、交互可视化以及节点和边结果导出。
各分支的操作课程与能力说明已接入；外部检索、ID映射与多数高级算法仍需按课程使用外部工具，不把课程开放等同于算法上线。

### 网络药理学双路线课程

在「核心学习与实训」按章节学习研究设计、药材/成分/靶点收集、UniProt映射、疾病基因交集、STRING、Cytoscape、GO/KEGG；再按需进入「进阶证据」。原8步简明版保留在「项目工具」。
每步提供输入、产物、传统操作、多工具选择、本站能力边界和自查项；可下载完整Markdown课程及来源/成分靶点/ID映射/疾病基因/节点属性5类CSV空表。
网络实验支持选择STRING等导出文件的端点和权重列，显式将0–1000分数转成0–1。
在线教学计算限500节点、5000条去重边，中心性按无权最短路径计算，边表不能恢复孤立节点；内置网络仅为示意，不是经过核验的数据库证据。
本站不自动抓取外部数据库，不实现cytoHubba/MCODE；机器学习、MR和免疫课程已提供下述限定输入的实际计算。
课程新增「资料检索到UniProt（详细操作）」：6个交付环节说明所需资料、数据库选择、合法下载/手工登记、原始文件留存、ID分批与映射回填；6张工作表提供字段字典、占位示例和CSV空模板。工作表用于检索审核归档，上传本站项目仍需按项目管理字段转换。详细操作同时包含在课程Markdown下载中。
「疾病基因与交集（详细操作）」继续提供疾病实体核对、GeneCards/DISGENET/OMIM与文献路线、来源分别筛选、证据长表与整合规则，附3张审核空表及操作单。粘贴双清单可现场计算交集/独有集并下载，不更改项目、不做ID或跨物种映射；不同来源评分不能混算。Excel与Python传统路线并列说明。
「PPI构图（详细操作）」提供7步STRING到Cytoscape/本站的文件交接，4张参数/映射/边/属性空表，虚构节点的评分换算筛选演示和排错表。说明节点ID连接键、孤立节点、功能/物理网络、算法方向与重复边处理，不自动查询STRING或安装桌面软件。
「GO/KEGG（详细操作）」提供7步ORA/GSEA选择、目标/背景/完整注释准备、g:Profiler与clusterProfiler路线、本站交接与FDR解读，附4张空表、虚构背景超几何演示和未在本环境执行的人类GO注释R导出示例。本站目前仅ORA、基因转大写且跨输入category整体BH；正式分析需说明物种、注释/背景、检验族与资源许可，不自动获取KEGG。
「转录组数据与设计」第5步支持标准化log2连续表达的独立两组Welch检验及BH，输出全量结果、火山图、热图，直接以实际检验基因作为ORA背景。每组至少3个独立样本；不处理原始计数、配对或批次/协变量，非limma收缩模型。
「机器学习与评估」支持逻辑回归和随机森林。25%内部测试集先留出，标准化、常量过滤和ANOVA特征选择在训练折内拟合；输出交叉验证、测试ROC/AUC、混淆矩阵、特征权重与样本划分。每组至少8名独立患者，不做外部队列验证或自动调参；不得用全数据预先筛出的差异基因宣称无泄漏评估。

### 教学闭环（2026-10-23）

免疫课程支持GSEApy ssGSEA：自备签名、覆盖审核、独立两组Mann–Whitney比较与BH；分数不是细胞比例。MR课程支持外部LD筛选后汇总表的单碱基等位基因协调（保守排除回文）、F筛选、IVW乘法随机效应SE、Q与逐一剔除；不下载GWAS、不执行LD/Egger或因果假设认证。单细胞/通讯与真实表达扰动仍为外部路线，网络删点仅为拓扑示意。
「资源、能力与验收」集中列出实际能力、归档规范、18项学习者自查以及可填写下载的Markdown交付记录。完整课程下载涵盖所有分支与字段。没有使用某分支应注明不适用，不强制运行全部算法；勾选不表示平台自动审核研究有效性。
初学者可选择：核心数据库/ID/交集/PPI/ORA → 按问题选择表达、预测、免疫或遗传证据 → 需要且有数据时再走外部单细胞/扰动路线 → 报告与独立验证。上传算法和虚构练习均在相应课程内，不新增实验室菜单。

## 计算与部署说明

运行环境Python 3.12，依赖见requirements.txt。表达文件首列gene_symbol、后续样本列；分组表sample_id/group，建议subject_id。每文件30 MB；差异计算限50000基因/500样本，机器学习20000基因/300样本，ssGSEA20000基因/200样本及200签名，MR最多10000位点。MR逐一剔除计算随工具数增加，正式大规模任务建议使用专用计算环境。

输入和结果保留在当前Streamlit会话；下载ZIP含CSV及methods.json（参数、版本、UTC时间、输入SHA256）。刷新会失去会话，不把结果自动写回示范项目。更新输入/参数后旧结果隐藏，避免错误复用。示例均为人工生成的占位数据。
ORA的BH校正在完整实际检验条目（含零命中）上执行，再按最少命中数过滤展示。

## 快速开始（Windows）

```powershell
cd C:\Users\32330\Desktop\HerbInsight
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

浏览器打开 http://localhost:8501

已有虚拟环境时也可执行 `./start_platform.ps1`，固定使用项目内Python，避免启动到缺少新依赖的全局环境。
运行验证：`./.venv/Scripts/python.exe scripts/run_tests.py`。
服务器可按Dockerfile构建（`docker build -t herbinsight .`，`docker run --rm -p 8501:8501 herbinsight`）。Docker构建需有Docker及网络，本次Windows环境未安装Docker，容器构建尚未实测。Streamlit Community Cloud可选择现有仓库、main分支、app.py和Python 3.12；公网是否更新以实际部署日志为准。

## 目录结构

```
HerbInsight/
├── app.py                  # Streamlit 入口（主程序）
├── requirements.txt        # Python 依赖
├── config/                 # 平台级配置
├── projects/               # 项目目录（每个复方-疾病一个项目）
│   └── wujisan_uc/         # 示范项目：五积散-溃疡性结肠炎
│       ├── project.yaml    # 项目配置（模块开关 + 数据文件路径）
│       ├── raw/            # 原始数据（只读，勿改动）
│       ├── processed/      # 标准化后的数据
│       ├── results/        # 分析结果
│       ├── figures/        # 图表
│       ├── reports/        # 报告
│       └── metadata/       # 元数据/来源记录
├── src/                    # 分析模块代码
└── tests/                  # 测试
```

## 数据规范（核心 CSV 文件）

每条重要记录至少保留：来源数据库、查询日期、原始ID、证据类型、物种、筛选条件、备注。

| 文件 | 说明 | 关键字段 |
|---|---|---|
| herbs.csv | 药材清单 | herb_name, latin_name, source_db, evidence_type |
| compound_targets.csv | 成分-靶点 | herb, compound, gene_symbol, source_db, query_date |
| disease_genes.csv | 疾病基因 | gene_symbol, source_db, evidence_score, screening_criteria |
| target_overlap.csv | 交集靶点 | gene_symbol, herb_count, evidence_type |
| ppi_nodes.csv | PPI节点 | node_id, gene_symbol, degree, betweenness, closeness |
| ppi_edges.csv | PPI边 | source, target, combined_score |
| go_enrichment.csv | GO富集 | term_id, term_name, category, gene_ratio, p_adjust, genes |
| kegg_enrichment.csv | KEGG富集 | pathway_id, pathway_name, gene_ratio, p_adjust, genes |
| deg_results.csv | 差异表达 | gene_symbol, log2fc, p_value, p_adjust, dataset |
| ml_metrics.csv | 机器学习 | model, auc, acc, feature, importance |
| mr_results.csv | 孟德尔随机化 | exposure, outcome, method, or, ci_low, ci_high, p_value |

## 从"原材料"目录接入数据

1. 现有材料位于 `C:\Users\32330\Desktop\原材料`（只读，勿改动）。
2. 将整理好的 CSV 副本放入 `projects\wujisan_uc\processed\` 和 `results\`。
3. 更新 `project.yaml` 中 `data_files` 字段。
4. 重启 `streamlit run app.py` 即可看到数据。

> 原始材料只读保存，平台处理结果另存，避免破坏已有研究成果。
