from io import BytesIO
from src.study_progress import validate_milestone, TASKS
from tests.ui_helpers import open_route


def test_milestone_validation():
    def upload(data):
        obj = BytesIO(data.encode()); obj.name = 'input.csv'; return obj
    result = validate_milestone(upload('herb_name,gene_symbol\nDemo,TP53\n'),'collection','targets',['herb_name','gene_symbol'])
    assert result['rows'] == 1 and len(result['sha256']) == 64
    for content in ['herb_name,gene_symbol\n', 'herb_name,gene_symbol\nDemo,\n', 'wrong\nvalue\n']:
        try:
            validate_milestone(upload(content),'collection','targets',['herb_name','gene_symbol'])
        except ValueError:
            pass
        else:
            raise AssertionError('invalid milestone accepted')


def test_study_project_creation_and_isolation():
    at = open_route('learn_home')
    at.text_input[0].set_value('我的学习项目')
    at.text_input[1].set_value('示例方')
    at.text_input[2].set_value('示例病')
    next(b for b in at.button if b.label == '创建并开始').click().run()
    assert not at.exception
    assert at.query_params['view'] == 'learn_collection'
    scope = at.session_state['study_selected']
    assert at.session_state['study_projects'][scope]['name'] == '我的学习项目'
    assert at.session_state['active_project'] == 'wujisan_uc'
    assert at.session_state['study_progress'][scope] == {}
    key = f'milestone_submit_{scope}_collection:herbs'
    at.button(key=key).click().run()
    assert not at.session_state['study_progress'][scope]
    assert not at.exception
