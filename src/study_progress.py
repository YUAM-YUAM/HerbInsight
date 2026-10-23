"""Session-private project milestones; uploaded evidence never mutates shared cases."""
import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

TASKS = {
 'collection': [('herbs','药材与来源登记',['herb_name','source_url']), ('targets','审核后的药材候选靶点',['herb_name','gene_symbol'])],
 'disease': [('disease','疾病基因与来源',['gene_symbol','disease_name']), ('common','共同靶点清单',['gene_symbol'])],
 'ppi': [('edges','STRING互作边表',['source','target'])],
 'enrichment': [('target','富集目标基因',['gene_symbol']),('background','背景基因',['gene_symbol']),('annotation','完整功能注释',['gene_symbol','term_id','term_name'])],
 'transcriptome': [('expression','标准化log2表达矩阵',['gene_symbol']),('samples','样本分组',['sample_id','group'])],
 'ml': [('expression','建模表达矩阵',['gene_symbol']),('samples','独立样本分组',['sample_id','group'])],
 'immune': [('expression','标准化表达矩阵',['gene_symbol']),('samples','样本分组',['sample_id','group']),('signature','免疫签名',['signature_id','gene_symbol'])],
 'mr': [('instruments','已去连锁的工具变量',['snp','beta_exposure','se_exposure','beta_outcome','se_outcome','effect_allele_exposure','other_allele_exposure','effect_allele_outcome','other_allele_outcome'])],
 'single_cell': [('manifest','单细胞数据与注释文件登记',['file_name','data_type','source_url'])],
 'perturbation': [('manifest','扰动方法与输入登记',['file_name','method','source_url'])],
}


def validate_milestone(upload, section, task, columns):
    from src.expression_analysis import read_analysis_table
    if upload.name.lower().endswith('.txt') and columns == ['gene_symbol']:
        import pandas as pd
        raw = upload.getvalue()
        if len(raw) > 30*1024*1024:
            raise ValueError('文件超过30MB。')
        genes = [line.strip() for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
        if genes and genes[0] == 'gene_symbol':
            genes = genes[1:]
        table = pd.DataFrame({'gene_symbol':genes})
    else:
        table = read_analysis_table(upload)
    # Accept the documented raw STRING endpoint aliases, without changing files.
    if task == 'edges':
        table = table.rename(columns={'#node1':'source','node1':'source','node2':'target'})
    missing = set(columns)-set(table.columns)
    if missing:
        raise ValueError('缺少列：'+', '.join(sorted(missing)))
    if table.empty:
        raise ValueError('只有表头，还没有资料记录。')
    for column in columns:
        values = table[column].astype('string').str.strip()
        if values.isna().any() or values.eq('').any():
            raise ValueError(f'{column}存在空值，请补齐本次提交的记录。')
    if task == 'expression':
        import numpy as np
        if table.columns[0] != 'gene_symbol' or table.shape[1] < 3:
            raise ValueError('表达矩阵首列为gene_symbol，至少包含两列样本。')
        if table.gene_symbol.duplicated().any():
            raise ValueError('表达矩阵包含重复基因。')
        if not np.isfinite(table.iloc[:,1:].astype(float).to_numpy()).all():
            raise ValueError('表达值存在缺失或非有限值。')
    if task == 'samples' and table.sample_id.duplicated().any():
        raise ValueError('分组表包含重复样本ID。')
    return {'filename':upload.name, 'rows':len(table), 'sha256':hashlib.sha256(upload.getvalue()).hexdigest(),
            'submitted_utc':datetime.now(timezone.utc).isoformat(), 'status':'completed',
            'scope':'资料提交与基础格式检查；不代表科学审核或算法完成'}


def render_project_controls():
    import streamlit as st
    projects = st.session_state.setdefault('study_projects', {})
    with st.expander('＋ 新建学习项目'):
        with st.form('new_study_project', clear_on_submit=True):
            name = st.text_input('项目名称', max_chars=80)
            formula = st.text_input('复方名称', max_chars=80)
            disease = st.text_input('研究疾病', max_chars=80)
            submit = st.form_submit_button('创建并开始')
        if submit:
            if not all(value.strip() for value in (name,formula,disease)):
                st.error('填写项目名称、复方和疾病后即可开始。')
            else:
                identifier = 'study_'+uuid4().hex
                projects[identifier] = {'name':name.strip(),'formula':formula.strip(),'disease':disease.strip()}
                st.session_state['study_selected'] = identifier
                st.session_state['study_just_created'] = True
                st.query_params['view'] = 'learn_collection'
                st.rerun()
    if projects:
        st.selectbox('我的学习项目', list(projects), format_func=lambda x:projects[x]['name'], key='study_selected')
        st.caption('学习项目与示范案例分开保存；上传资料仅在当前会话处理，不写入公共案例。离开前下载进度记录，当前版本不提供跨设备恢复。')


def render_study_progress(section, project_id):
    import streamlit as st
    scope = st.session_state.get('study_selected', 'case_'+project_id)
    projects = st.session_state.get('study_projects', {})
    name = projects.get(scope, {}).get('name', '当前案例的学习练习')
    all_progress = st.session_state.setdefault('study_progress', {})
    records = all_progress.setdefault(scope, {})
    core = ['collection','disease','ppi','enrichment']
    core_keys = [f'{s}:{task}' for s in core for task,_,_ in TASKS[s]]
    completed = sum(key in records for key in core_keys)
    st.caption('学习项目：'+name)
    st.progress(completed/len(core_keys), text=f'核心资料里程碑 {completed}/{len(core_keys)} · 进阶资料按需完成')
    if st.session_state.pop('study_just_created', False):
        st.success('项目已创建。先从第一份药材登记开始，逐步积累你的研究资料。')
    if section in TASKS:
        with st.expander('本节任务 · 手动收集与提交', expanded=True):
            st.caption('已完成 = 资料已提交并通过基础格式检查。来源真实性、物种、筛选依据和研究设计仍需你审核；算法结果在下方计算区生成。此处只登记，不自动送入算法。')
            for task, label, columns in TASKS[section]:
                key = f'{section}:{task}'
                state = records.get(key)
                with st.container(border=True):
                    st.markdown(('✅ 已完成 · ' if state else '○ 待完成 · ')+label)
                    st.caption('手动收集 / 外部整理 · 必需列：'+', '.join(columns))
                    if state:
                        st.caption(f"已提交：{state['filename']} · {state['rows']}行。再次提交通过检查后才替换记录。")
                    file = st.file_uploader('上传收集好的文件', type=['csv','tsv','txt'], key=f'milestone_file_{scope}_{key}')
                    if st.button('检查并提交', key=f'milestone_submit_{scope}_{key}'):
                        if file is None:
                            st.warning('先选择文件，再提交。')
                        else:
                            try:
                                record = validate_milestone(file, section, task, columns)
                            except (ValueError,UnicodeError) as error:
                                st.error(str(error))
                            else:
                                records[key] = record
                                st.rerun()
    if section in TASKS or section in ('overview','resources'):
        payload = {'project':projects.get(scope, {'name':name}), 'milestones':records,
                   'scope':'当前会话的学习资料提交记录；非科研认证，不包含文件原文'}
        st.download_button('保存我的学习进度（JSON）',json.dumps(payload,ensure_ascii=False,indent=2).encode('utf-8'),
                           'HerbInsight_progress.json','application/json',key='study_progress_download')
