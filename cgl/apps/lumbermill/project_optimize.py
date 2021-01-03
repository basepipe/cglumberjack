from cgl.core.path import PathObject
from cgl.core.utils.general import load_json, save_json, cgl_copy
from cgl.core.config.config import get_root
import glob
import os
import time
import re

COMPANY = 'VFX'
# PROJECT = '02BTH_2021_Kish'
PROJECT = '18BTH_2019_Brinkley'


def get_shots(company, project, scope='shots', task=False):
    context = 'render'
    d_ = {'company': company,
          'project': project,
          'scope': scope,
          'context': context,
          'seq': '*',
          'shot': '*',
          }
    if task:
        d_['task'] = '*'
    path_object = PathObject(d_)
    glob_path = "{}".format(path_object.path_root)
    shots = glob.glob(glob_path)
    return shots


def get_latest_publishes(company, project, scope='shots'):
    start_time = time.time()
    tasks = get_shots(company, project, scope=scope, task=True)
    publish_list = []
    for t in tasks:
        t = t.replace('\\', '/')
        if 'cgl_info' not in t:
            pub_dir = '{}/publish'.format(t)
            res_dir = PathObject(pub_dir).copy(latest=True, resolution='high').path_root
            source_res_dir = res_dir.replace('/render/', '/source/')
            if os.path.exists(res_dir):
                publish_list.append(res_dir)
                publish_list.append(source_res_dir)
    print('{} {} publishes Computed in {} seconds'.format(len(publish_list), scope, time.time()-start_time))
    return publish_list


def get_published_msd_files(company, project, task='anim'):
    shots = get_shots(company, project)
    msd_list = []
    for s in shots:
        s = s.replace('\\', '/')
        if 'cgl_info' not in s:
            pub_dir = ('{}/{}/publish'.format(s, task))
            msd = PathObject(pub_dir).copy(latest=True, resolution='high', set_proper_filename=True, ext='msd').path_root
            if os.path.exists(msd):
                msd_list.append(msd)
    return msd_list


def get_latest_shot_publishes(company, project):
    return get_latest_publishes(company, project, scope='shots')


def get_latest_asset_publishes(company, project):
    return get_latest_publishes(company, project, scope='assets')


def get_all_publishes(company, project):
    start_time = time.time()
    all_publishes = get_latest_asset_publishes(company, project) + get_latest_shot_publishes(company, project)
    print('Found all latest publishes in {} seconds'.format(time.time()-start_time))
    return all_publishes


def optimize_project(company, project, new_company=None, new_project=None, test=True):
    """

    :param company:
    :param project:
    :param new_company:
    :param new_project:
    :param test:
    :return:
    """
    if not new_company:
        new_company = company
    if not new_project:
        new_project = '{}_clean'.format(project)
    create_clean_project(company, project, new_company, new_project, test)
    # create_project_backup(company, project)
    # rename_clean_copy(company, project, new_company, new_project)


def create_clean_project(company, project, new_company, new_project, test=True):
    latest_publishes = get_all_publishes(company, project)
    #
    print('Creating optimized version of project {}: {}'.format(project, new_project))
    for l in latest_publishes:
        clean_copy = l.replace(project, new_project)
        if company != new_company:
            clean_copy = l.replace(company, new_company)
        copy_publish(l, clean_copy, test)
    # TODO - copy over the globals from the current project to the new one.


def copy_publish(old, new, test=True):
    """
    copies the latest version to the new location.
    :param old:
    :param new:
    :return:
    """
    if test:
        print('Copying {} to {}'.format(old, new))
    else:
        cgl_copy(old, new)


def create_project_backup(company, project, test=True):
    context = 'render'
    d_ = {'company': company,
          'project': project,
          'context': context,
          }
    d_bkp = {'company': '{}_BKP'.format(company),
             'project': project,
             'context': context,
             }
    path_object_render = PathObject(d_)
    path_object_source = path_object_render.copy(context='source')
    bkp_render = PathObject(d_bkp)
    bkp_source = bkp_render.copy(context='source')
    print('Creating backup of {} at: {}'.format(path_object_render.path_root, bkp_render.path_root))
    print('Creating backup of {} at: {}'.format(path_object_source.path_root, bkp_source.path_root))
    if not test:
        print('have to figure out how to simply "move" a project and rename it')


def rename_clean_copy(company, project, new_company, new_project):
    print('Renaming {}/{} to: {}/{}'.format(new_company, new_project, company, project))


def get_asset_dependencies(company, project):
    start_time = time.time()
    msds = get_published_msd_files(company, project)
    root = get_root(project)
    proj_dependencies = []
    for msd in msds:
        deps = get_dependencies(msd, company, project, root)
        for d in deps:
            if d not in proj_dependencies:
                proj_dependencies.append(d)
    end_time = time.time() - start_time
    print('{} Unique Asset Dependencies Computed in {} seconds'.format(len(proj_dependencies), end_time))
    return proj_dependencies


def add_root(company, root, path):
    new_path = None
    if company not in path:
        new_path = '{}/{}/{}'.format(root, company, path)
    else:
        new_path = '{}/{}'.format(root, path)
    new_path = new_path.split('/high/')[0].replace('//', '/').replace('\\', '/')

    return new_path


def fix_rig_path_from_abc(company, project, root, abc_path, msd, chop=True):
    print('Broken Rig "source_path" found in {}'.format(msd))
    print('\t{}'.format(abc_path))
    asset = os.path.split(abc_path)[-1]
    asset = os.path.splitext(asset)[0]
    type_, asset = asset.split('_')
    if re.search('[0-9]+', asset):
        asset = re.sub('[0-9]+', '', asset)
    d_ = {'company': company,
          'root': root,
          'project': project,
          'scope': 'assets',
          'context': 'render',
          'user': 'publish',
          'task': 'rig',
          'seq': type_,
          'shot': asset,
          'resolution': 'high'}
    path_object = PathObject(d_).copy(latest=True, set_proper_filename=True, ext='mb')
    if os.path.exists(path_object.path_root):
        if chop:
            rig_publish = path_object.path.split('/high/')[0]
        else:
            rig_publish = path_object.path
        return rig_publish
    else:
        print('Path does not exist: {}\n\tFound in: {}'.format(path_object.path_root, msd))


def get_dependencies(msd, company, project, root):
    msd_dict = load_json(msd)
    dependencies = []
    for key in msd_dict:
        if 'type' in msd_dict[key].keys():
            type_ = msd_dict[key]['type']
            if type_ == 'anim':
                if msd_dict[key]['source_path']:
                    if '/shots/' in msd_dict[key]['source_path']:
                        print(msd_dict[key]['source_path'])
                    else:
                        rig_publish = add_root(company, root, msd_dict[key]['source_path'])
                        if rig_publish not in dependencies:
                            dependencies.append(rig_publish)
            elif type_ == 'bndl':
                bndl_publish_path = '{}/{}'.format(root, msd_dict[key]['source_path'])
                bndl_publish = add_root(company, root, msd_dict[key]['source_path'])
                if bndl_publish not in dependencies:
                    dependencies.append(bndl_publish)
                bndl_dependencies = get_dependencies(bndl_publish_path, company, project, root)
                for b in bndl_dependencies:
                    if b not in dependencies:
                        dependencies.append(b)
            elif type_ == 'asset':
                asset_publish = add_root(company, root, msd_dict[key]['source_path'])
                if asset_publish not in dependencies:
                    dependencies.append(asset_publish)
                pass
            else:
                print('\tFound Unlisted type: {}'.format(type_))
                print('\t\t{}: {}'.format(key, msd_dict[key]['source_path']))
        else:
            print('\t ERROR: no "type" found in {}'.format(msd_dict[key]))
    return dependencies


def fix_msd(company, project, msd):
    """
    This is a tool i created for a temporary fix as i was going through and adjusting .msd files (tom)
    :param company:
    :param project:
    :param msd:
    :return:
    """
    print(msd)
    msd_dict = load_json(msd)
    root = get_root(project)
    for asset in msd_dict:
        type_ = msd_dict[asset]['type']
        if type_ == 'anim':
            if '/shots/' in msd_dict[asset]['source_path']:
                rig_path_fix = fix_rig_path_from_abc(company, project, root, msd_dict[asset]['abc'], msd, chop=False)
                msd_dict[asset]['source_path'] = rig_path_fix
        for key in msd_dict[asset]:
            value = str(msd_dict[asset][key])
            if 'tmikota' in value:
                new_value = value.replace('tmikota', 'publish')
                msd_dict[asset][key] = new_value
    return msd_dict


if __name__ == '__main__':
    optimize_project(COMPANY, PROJECT, test=False)


