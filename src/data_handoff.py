"""Distinguish research evidence, executable input and saved output."""
HANDOFFS = {
 'collection': [
 ('资料留存', 'symmap_herb_register.csv / symmap_herb_targets.csv 或所选通用工作表', '来源、审核与排除记录；不是直接计算文件'),
 ('项目输入', 'processed/herbs.csv', 'formula_name、herb_name；与现有项目管理必需字段一致'),
 ('项目输入', 'processed/compound_targets.csv', 'formula_name、herb_name、gene_symbol；保留额外来源列。历史文件名虽含compound，当前接口接受药材候选靶点，不证明存在成分关系'),
 ('疾病交集输入', 'drug_target_genes.txt', '已审核基因每行一个，无标题；SymMap路线下方可转换导出')],
 'disease': [
 ('资料留存','疾病检索/筛选工作表','保留来源评分和排除理由；不能只存交集'),
 ('项目输入','processed/disease_genes.csv','gene_symbol、disease_name；来源列可另保留'),
 ('交集/STRING输入','共同基因清单','每行一个审核基因，无标题。项目归档target_overlap.csv还需formula_name、disease_name；不是PPI边表')],
 'ppi': [
 ('计算输入','STRING导出边表或source/target表','在计算区指定端点和分数列、确认尺度；source/target是两个端点，不是任意两基因组合'),
 ('结果归档','processed/ppi_edges.csv、ppi_nodes.csv','既有项目边与节点结果；节点结果不能替代输入边表。边表重算可能漏掉孤立节点')],
 'enrichment': [
 ('ORA计算输入','目标表 + 背景表','建议单列gene_symbol；两者均为审核后的同物种同ID基因'),
 ('ORA计算输入','完整功能注释表','gene_symbol、term_id、term_name；可选category。不是只含显著条目的结果表'),
 ('结果归档','results/go_enrichment.csv、kegg_enrichment.csv','原案例已算好的结果，不能改后缀当完整注释重新计算')],
 'transcriptome': [
 ('计算输入','expression_log2.csv','首列gene_symbol，后续列为唯一样本ID；已规范化log2数值，不是DEG结果或原始计数'),
 ('计算输入','sample_metadata.csv','sample_id、group，建议subject_id；样本集合与表达列完全一致，每组至少3个独立样本'),
 ('结果归档','processed/transcriptome_degs.csv','原案例筛后的差异结果，不是表达矩阵；当前全量Welch输出列也不能直接冒充旧导入脚本的Gene/logFC/adj.P.Val列')],
 'ml': [
 ('本站计算输入','表达矩阵 + 分组表','与转录组计算区格式相同，基因为行、样本为列，每组至少8例；本站内部转置。传统建模X可能是样本行，不能混用'),
 ('结果归档','results/ml_auc.csv等','模型评估结果，不是训练数据；不能从AUC表复现模型')],
 'immune': [
 ('计算输入','表达矩阵 + 分组表 + 签名','表达首列gene_symbol、后续样本列；分组sample_id/group；签名signature_id/gene_symbol。签名覆盖须审核，ssGSEA分数不是细胞比例'),
 ('结果归档','processed/immune_scores.csv等','案例评分是输出，不替代原始表达或签名')],
 'mr': [
 ('计算输入','已去连锁的暴露—结局工具变量表','按计算区9字段模板填写snp、两侧beta/se及两侧效应/其他等位基因；不是结果OR表'),
 ('结果归档','results/mr_results.csv等','既有MR结果，不是可重新执行MR的工具变量输入')],
 'single_cell': [('外部工具输入','表达/细胞注释及适用对象','按CellChat/CellPhoneDB版本要求；本站没有统一可计算上传接口，课程模板只用于准备')],
 'perturbation': [('外部算法或演示','方法特定输入','真实表达扰动需方法适用数据；网络删点是拓扑演示，不能用同一个表宣称完成生物学敲除')],
}


def render_data_handoff(section):
    import pandas as pd
    import streamlit as st
    if section not in HANDOFFS:
        return
    with st.expander('本节文件交接：哪些是输入，哪些只是记录？'):
        st.caption('以下是本站当前接口约定，不是全行业唯一标准。字段合格不等于证据真实或研究设计合格；原始文件不覆盖。')
        st.dataframe(pd.DataFrame(HANDOFFS[section], columns=['用途','文件/对象','实际要求与去向']), hide_index=True, width='stretch')
        st.write('raw/保留原下载；working/保留检索、映射和筛选明细；审核后才生成分析输入。processed/与results/是现有项目归档位置，不是每张教学空表的保存位置。')
