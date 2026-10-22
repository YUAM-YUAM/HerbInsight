"""SymMap-specific file handoff grounded in the user's actual target export."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    ('Target id', 'target_id', '原样保留SymMap靶点ID；不是UniProt ID'),
    ('Gene symbol', 'gene_symbol', '基因符号；审核后用于疾病交集'),
    ('Gene name', 'gene_name', '基因全名，用于核对，不替代基因符号'),
    ('Protein name', 'protein_name', '蛋白名称，辅助核对'),
    ('UniProt id', 'uniprot_id', '核对蛋白身份与物种；多值不可直接取第一项'),
    ('Ensembl id', 'ensembl_id', '保留原始Ensembl标识，供交叉核对'),
    ('Chromosome', 'chromosome', '原样保留；缺失不补造'),
    ('Relationship', 'relationship', '原样保留，如By_ingredient；不能由此推出具体是哪一个成分'),
    ('P_value', 'p_value', '数据库关系推断的统计字段，定义需查对应版本文档；不是本站表达差异P值'),
    ('FDR(BH)', 'fdr_bh', '保留数据库BH校正值；不把它误认作你全部药材合并后的重新校正'),
    ('FDR(Bonferroni)', 'fdr_bonferroni', '保留另一种校正值，不与BH混用'),
    ('Inferred evidence score', 'evidence_score', '保留推断评分；不能解释成结合强度、疗效或概率'),
]

TABLES = {
 'symmap_herb_register.csv': ('一行一味已核对的药材', [
    ('formula_name','复方名，如五积散'), ('herb_name','规范药名，如半夏'),
    ('symmap_herb_id','药材条目中的数据库ID，实际抄录，不从文件名猜'),
    ('herb_latin_name','条目或药典记录的拉丁名；来源需注明'),
    ('botanical_origin','药材基原，可能涉及多种植物/动物'), ('medicinal_part','药用部位'),
    ('processing','炮制信息；处方与数据库条目需核对'), ('source_db','SymMap'),
    ('source_url','本味药材的详情页URL，不只填首页'), ('database_version','查到的版本；查不到写未报告'),
    ('query_date','真实检索日期，YYYY-MM-DD'), ('source_file','实际下载文件名'),
    ('target_species','靶点研究物种；不是药材物种'), ('species_evidence','物种确认依据；未确认则留空'),
    ('notes','同名、缺失或身份疑问')]),
 'symmap_herb_targets.csv': ('一行一条药材—靶点—来源关系（主表）', [
    ('herb_name','从本次检索药材登记带入'), ('symmap_herb_id','连接药材登记表'),
    *[(dest, note) for _, dest, note in FIELDS],
    ('source_db','SymMap'), ('source_url','药材或靶点记录URL'), ('query_date','真实检索日期'),
    ('database_version','实际版本或未报告'), ('source_file','原始靶点表文件名'),
    ('target_species','经过核查的靶点物种'), ('mapping_status','pending/mapped/ambiguous/unmapped'),
    ('included','pending/yes/no；下载完成不等于已纳入'),
    ('decision_reason','依据预先规定规则填写；排除项也保留')]),
 'symmap_herb_ingredients.csv': ('需要成分网络时才补：一行一条药材—成分关系', [
    ('herb_name','药材名'), ('symmap_herb_id','药材数据库ID'),
    ('ingredient_id','从成分关联列表实际取得的ID'), ('ingredient_name','原始成分名'),
    ('pubchem_cid','仅在有可靠对应关系时填写'), ('smiles','有来源的结构；没有就留空'),
    ('source_url','关联或详情页URL'), ('source_file','成分导出文件'), ('query_date','真实检索日期')]),
 'symmap_ingredient_targets.csv': ('需要成分网络时才补：一行一条有证据的成分—靶点关系', [
    ('ingredient_id','与成分表相连'), ('target_id','与靶点表相连'), ('gene_symbol','审核符号'),
    ('relationship','来源报告的关系类型'), ('evidence_reference','文献/数据库关系出处'),
    ('source_url','关系详情或原始数据出处'), ('source_file','关系导出文件'), ('query_date','真实检索日期')]),
}

STEPS = [
 '1. 逐味检索，不直接搜整个复方代替逐味收集：例如输入“半夏”，打开匹配的药材详情。核对中文名、别名、条目ID、可获得的拉丁名/基原与药用部位；生品/炮制品不自动合并。剂量与处方出处应从处方资料补，不假定SymMap提供。',
 '2. 看药材关联的靶点信息：定位靶点/Target关联区域，优先保存完整可许可导出的列表。你的半夏sy.csv就是这种靶点表，不是成分清单。记录来自哪味药、哪一个条目及检索日期；界面名称和导出按钮以实际版本为准。',
 '3. 下载后先核对表头：Target id、Gene symbol、UniProt id、Relationship、P_value、FDR(BH)等。原文件放raw/不覆盖；在副本添加herb_name、来源URL、日期和审核字段，再统一字段名。下面逐列给出对应关系。',
 '4. 如果只做药材候选靶点与疾病交集，先完成药材登记表和药材—靶点主表即可。如果要画药材—成分—靶点网络，再找成分/Ingredient关联列表和成分—靶点关系。仅有By_ingredient标签，不能把所有成分与所有靶点两两连接。',
 '5. 分开做身份审核与证据筛选：核查UniProt/物种和一对多映射；再按预先说明的关系类型、评分或校正值规则标记included。SymMap没有可直接套用的统一筛选阈值；不要为凑191个基因反调门槛，也不要补造缺失的OB/DL。',
 '6. 最后才生成下游集合：从物种正确、mapping_status=mapped、included=yes且gene_symbol非空的行抽出基因符号去重，每行一个保存drug_target_genes.txt（无标题）。主表仍保留各药材来源、重复关系及排除原因。与疾病清单求交后才进入STRING。',
]


def symmap_markdown():
    lines = ['# SymMap：从药材条目到候选靶点表',
             '五积散数据来源：研究者已确认SymMap。字段依据现存半夏sy.csv核对；没有声称实时核验当前网站按钮或字段定义版本。', *STEPS,
             '## 原始靶点导出列如何整理']
    lines += [f'- {raw} → {dest}：{note}' for raw,dest,note in FIELDS]
    for filename, (grain, fields) in TABLES.items():
        lines += ['## '+filename, grain] + [f'- {name}：{note}' for name,note in fields]
    lines += ['## 重要边界', 'Homo sapiens是目标蛋白研究物种，不是药材基原。原项目导入脚本统一赋值species=Homo sapiens，因此这列本身不是逐条物种审核证据。SymMap药材关联或推断关系不是临床疗效证明。']
    return '\n\n'.join(lines)


def render_symmap_workflow():
    import streamlit as st
    st.subheader('SymMap具体怎么查、怎么整理？')
    st.caption('本案例来源由研究者确认：SymMap。以下表头已与现有半夏sy.csv核对；当前网站菜单名称、访问与导出权限以实际页面为准。')
    st.info('最少先做两张表：药材登记表 + 药材—靶点主表。要做成分网络时，再补两张成分关系表。')
    for step in STEPS:
        st.write(step)
    st.dataframe(pd.DataFrame(FIELDS, columns=['原始下载列','整理后列名','保留与解释']), hide_index=True, width='stretch')
    st.warning('截图里的species=Homo sapiens由原导入脚本统一填写，只代表项目设定，不是药材的物种，也不能替代逐条靶点物种核对。新模板用botanical_origin与target_species分别记录。')
    with st.expander('照着填：半夏已有记录怎样进入主表'):
        data = pd.read_csv(ROOT / 'projects/wujisan_uc/processed/compound_targets.csv')
        sample = data.loc[data.herb_name.eq('半夏'), ['herb_name','target_id','gene_symbol','uniprot_id','relationship','p_value','fdr_bh','evidence_score','source_file']].head(2).copy()
        sample['source_db'] = 'SymMap'
        sample['mapping_status'] = 'pending'
        sample['included'] = 'pending'
        st.dataframe(sample, hide_index=True, width='stretch')
        st.caption('前两行数值来自你的现存文件，不是虚构示例；pending是本教学整理建议，不覆盖原结果。药材ID、检索日期、URL和版本目前未取得，不填假值。两条都不能仅因存在于表中就默认纳入。')
    for filename, (grain, fields) in TABLES.items():
        with st.expander(filename+' · '+grain):
            st.dataframe(pd.DataFrame(fields, columns=['列名','怎么填写']), hide_index=True, width='stretch')
            st.download_button('下载空表 · '+filename, pd.DataFrame(columns=[name for name,_ in fields]).to_csv(index=False).encode('utf-8-sig'), filename, 'text/csv', key='symmap_'+filename)
    st.caption('CSV用UTF-8保存；一格一个ID/值，不合并单元格。未知信息留空并写备注，不能以0替代缺失评分。以上是证据整理表，不保证直接匹配项目管理上传接口。')
    st.download_button('下载SymMap逐步操作单', symmap_markdown().encode('utf-8-sig'), 'SymMap_workflow.md', 'text/markdown', key='symmap_workflow')
