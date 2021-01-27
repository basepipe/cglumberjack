import os
import time
import glob
from cgl.core.path import PathObject, remove_root
from cgl.core.utils.general import load_json, save_json
from cgl.core.config.config import user_config


def get_all(company, project, branch):
    scope = ['assets', 'shots']
    root = user_config()['paths']['root']
    project_msd_file = r'{}\{}\render\{}\{}\project.msd'.format(root, company, project, branch)
    asset_list, shot_list = get_all_assets_and_shots(PathObject(project_msd_file.replace('project.msd', '*')))
    if os.path.exists(project_msd_file):
        project_msd = load_json(project_msd_file)
        project_msd['asset_list'] = asset_list
        project_msd['shot_list'] = shot_list
    else:

        project_msd = {'assets': {},
                       'shots': {},
                       'asset_list': asset_list,
                       'shot_list': shot_list}
    for s in scope:
        dict = {'project': project,
                'company': company,
                'branch': branch,
                'context': 'render',
                'scope': s,
                'seq': '*',
                'shot': '*',
                'task': '*'}
        base_path_object = PathObject(dict)
        files = glob.glob(base_path_object.path_root)
        for i, f in enumerate(files):
            if '.' not in f:
                po = PathObject(f)
                if po.seq not in project_msd[po.scope].keys():
                    project_msd[po.scope][po.seq] = {}
                if po.shot not in project_msd[po.scope][po.seq].keys():
                    project_msd[po.scope][po.seq][po.shot] = {}
                if po.task not in project_msd[po.scope][po.seq][po.shot].keys():
                    project_msd[po.scope][po.seq][po.shot][po.task] = {}
                project_msd[po.scope][po.seq][po.shot][po.task] = process_publish_and_latest_user(po)
    save_json(project_msd_file, project_msd)
    print('Successfully Updated {}'.format(project_msd_file))


def process_publish_and_latest_user(path_object):
    task_dict = {'publish': {'render': {},
                             'source': {}},
                 'latest_user': {'render': {},
                                 'source': {}}}
    if os.path.exists(path_object.path_root):
        task_dict['publish']['render'] = get_render_dict(path_object)
        task_dict['latest_user']['render'] = get_render_dict(path_object, user=True)
        task_dict['publish']['source'] = get_source_dict(path_object)
        task_dict['latest_user']['source'] = get_source_dict(path_object, user=True)
    return task_dict


def get_source_dict(path_object, user=False):
    path_object = path_object.copy(latest=True, resolution='high', user='publish', context='source')
    dict_ = {'date': "",
             'folder': "",
             'source_file': "",
             'preview_file': "",
             'thumb_file': "",
             'source_files': "",
             'size': "",
             }
    if not os.path.exists(path_object.path_root):
        if not user:
            return dict_
    if user:
        folder = get_latest_user_folder(path_object)
        if folder:
            path_object = PathObject(folder)
        else:
            return dict_
    else:
        folder = path_object.path_root
    cgl_info_file = '{}/cgl_info.json'.format(folder)
    source_file = ""
    modified = ""
    if os.path.exists(folder):
        modified = time.ctime(max(os.stat(root).st_mtime for root, _, _ in os.walk(folder)))
    path_object = path_object.copy(set_proper_filename=True, ext='jpg')
    source_files = glob.glob(path_object.path_root.replace('jpg', '*'))
    source_files_clean = []
    for s in source_files:
        source_files_clean.append(remove_root(s))
    if len(source_files) == 1:
        source_file = source_files[0]
    size = {'bytes': "",
            'mb': "",
            'gb': ""}
    if os.path.exists(cgl_info_file):
        info = load_json(cgl_info_file)
        try:
            size = {'bytes': info[folder]['total_bytes'],
                    'mb': info[folder]['total_mb'],
                    'gb': info[folder]['total_gb']}
        except KeyError:
            pass
    preview_path = ""
    thumb_path = ""
    preview = path_object.preview_path
    if preview:
        if os.path.exists(preview):
            preview_path = preview
        thumb = path_object.thumb_path
        if os.path.exists(thumb):
            thumb_path = thumb

    dict_ = {'date': modified,
             'folder': remove_root(folder),
             'source_file': remove_root(source_file),
             'preview_file': remove_root(preview_path),
             'thumb_file': remove_root(thumb_path),
             'source_files': source_files_clean,
             'size': size,
             }
    return dict_


def get_latest_user_folder(path_object):
    if path_object.version:
        pattern = path_object.path_root.replace('publish', '*').replace(path_object.version, '*')
    else:
        pattern = "{}/*/*/*".format(path_object.path_root)
    folders = glob.glob(pattern)
    latest = 0
    latest_folder = ""
    for f in folders:
        if 'publish' not in f:
            raw_time = os.path.getctime(f)
            if raw_time > latest:
                latest = raw_time
                latest_folder = f
    return latest_folder


def get_all_assets_and_shots(path_object):
    path = path_object.split_after('branch')
    stuff = glob.glob('{}/*/*/*'.format(path))
    assets = []
    shots = []
    for s in stuff:
        s = s.replace('\\', '/')
        s = remove_root(s)
        if 'cgl_info' not in s:
            if 'assets' in s:
                assets.append(s)
            elif 'shots' in s:
                shots.append(s)
    return assets, shots


def get_render_dict(path_object, user=False):
    path_object = path_object.copy(latest=True, resolution='high', user='publish', context='render')
    folder = path_object.path_root
    dict_ = {'date': "",
             'msd': "",
             'size': {},
             'folder': ""}
    if not user and not os.path.exists(folder):
        return dict_
    if user:
        folder = get_latest_user_folder(path_object)
        if folder:
            path_object = PathObject(folder)
        else:
            return dict_
    cgl_info_file = '{}/cgl_info.json'.format(folder)
    modified = ""
    if os.path.exists(folder):
        modified = time.ctime(max(os.stat(root).st_mtime for root, _, _ in os.walk(folder)))
    path_object = path_object.copy(set_proper_filename=True, ext='jpg')
    size = {'bytes': "",
            'mb': "",
            'gb': ""}
    if os.path.exists(cgl_info_file):
        info = load_json(cgl_info_file)
        try:
            size = {'bytes': info[folder]['total_bytes'],
                    'mb': info[folder]['total_mb'],
                    'gb': info[folder]['total_gb']}
        except KeyError:
            pass
    msd_path = path_object.relative_msd_path
    if not os.path.exists(path_object.msd_path):
        msd_path = ""
    dict_ = {'date': modified,
             'msd': msd_path,
             'size': size,
             'folder': remove_root(folder)}
    return dict_




get_all('cmpa-animation', '02BTH_2021_Kish', 'master')

