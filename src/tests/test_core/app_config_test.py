import pytest
import os
from cglcore.config import app_config


def test_src_is_sources_root():
    import core
    this_path = __file__.split('src')[0]
    core_path = core.__file__.split('src')[0]
    if this_path == core_path:
        assert True
    else:
        print 'The Root of this File: %s \n' \
              'does not match the root of the "core" module path %s\n' \
              'try setting "src" as "Sources Root" in pycharm' % (this_path, core_path)
        assert False


def test_can_call_app_config():
    print 'app config:', app_config()
    app_config()
    assert True


def test_has_user_default():
    app_config()['account_info']['user']
    assert True


def test_has_company():
    app_config()['account_info']['company']
    assert True


def test_has_companies():
    app_config()['account_info']['companies']
    assert True


def test_companies_is_list():
    if type(app_config()['account_info']['companies']) == list:
        assert True
    else:
        assert False


def test_has_company_in_companies():
    company = app_config()['account_info']['company']
    if company in app_config()['account_info']['companies']:
        assert True
    else:
        assert False


def test_has_user_directory():
    app_config()['account_info']['user_directory']
    assert True


def test_user_directory_exists():
    if os.path.exists(app_config()['account_info']['user_directory']):
        assert True
    else:
        print "Does Not Exist %s" % app_config()['account_info']['user_directory']
        assert False


def test_has_paths():
    app_config()['paths']
    assert True


def test_root_dir():
    app_config()['paths']['root']
    assert True


def test_root_exists():
    assert os.path.exists(app_config()['paths']['root'])


def test_all_paths_exist():
    for key in app_config()['paths']:
        if os.path.exists(app_config()['paths'][key]):
            assert True
        else:
            print '%s: %s' % (key, app_config()['paths'][key])
            assert False


def test_context_list_exist():
    app_config()['rules']['context_list']
    assert True


def test_context_list_list():
    assert type(app_config()['rules']['context_list']) == list


def test_scopes_exist():
    assert type(app_config()['rules']['scope_list']) == list


def test_scope_list():
    assert type(app_config()['rules']['scope_list']) == list


def test_scopes_match_templates():
    scope_list = []
    for scope in app_config()['templates']:
        if scope not in scope_list:
            scope_list.append(scope)
    if len(scope_list) == len(app_config()['rules']['scope_list']):
        assert len(set(scope_list).intersection(app_config()['rules']['scope_list'])) == len(scope_list)
    else:
        assert False


def test_context_list_match_templates():
    context_list = []
    for scope in app_config()['templates']:
        for context in app_config()['templates'][scope]:
            if context not in context_list:
                context_list.append(context)
    if len(context_list) == len(app_config()['rules']['context_list']):
        assert len(set(context_list).intersection(app_config()['rules']['context_list'])) == len(context_list)
    else:
        assert False


# As i get deeper into this i can come up with more tests for app config, but this is a fantastic starting off point.







