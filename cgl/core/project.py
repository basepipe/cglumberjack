# -*- coding: utf-8 -*-
import os
from cgl.core.config import app_config, UserConfig
from cgl.core.path import PathObject, CreateProductionData

CONFIG = app_config()
PROJ_MANAGEMENT = CONFIG['account_info']['project_management']
ROOT = CONFIG['paths']['root']


def get_projects(company):
    """
    returns projects for "company"
    :param company:
    :return:
    """
    d = {'root': ROOT,
         'company': company,
         'project': '*',
         'context': 'source'}
    path_object = PathObject(d)
    return path_object.glob_project_element('project')


def get_companies():
    """
    returns all companies the system is aware of.
    :return:
    """
    d = {'root': ROOT,
         'company': '*'
         }
    path_object = PathObject(d)
    companies = path_object.glob_project_element('company')
    if '_config' in companies:
        companies.remove('_config')
    return companies


def get_task_info(path_object, force=False):
    """
    Gets Task info in a format ready for display in lumbermill
    :param path_object:
    :param force:
    :return:
    """
    print 11
    print UserConfig().d
    print path_object.company, path_object.project
    print path_object.path_root
    if path_object.company in UserConfig().d['my_tasks'].keys():
        if path_object.project in UserConfig().d['my_tasks'].keys():
            all_tasks = UserConfig().d['my_tasks'][path_object.company][path_object.project]
        else:
            return
    else:
        return
    if path_object.task:
        if path_object.scope == 'assets':
            path_object.task_name = '%s_%s_%s' % (path_object.category, path_object.asset, path_object.task)
        elif path_object.scope == 'shots':
            path_object.task_name = '%s_%s_%s' % (path_object.seq, path_object.shot, path_object.task)
        if path_object.task_name:
            if force:
                task_info = pull_task_info(path_object)
                return task_info
            else:
                if path_object.task_name in all_tasks:
                    task_info = all_tasks[path_object.task_name]
                else:
                    task_info = pull_task_info(path_object)
                return task_info


def pull_task_info(path_object):
    from cgl.core.util import current_user
    if PROJ_MANAGEMENT == 'ftrack':
        from plugins.project_management.ftrack.main import find_user_assignments
        login = CONFIG['project_management']['ftrack']['users'][current_user()]
        project_tasks = find_user_assignments(path_object, login, force=True)
        task_info = project_tasks[path_object.task_name]
        return task_info


def create_project_config(company, project):
    """
    Creates the config for a project
    :param company:
    :param project:
    :return:
    """
    from cgl.core.util import cgl_copy
    config_dir = os.path.dirname(UserConfig().user_config_path)
    company_config = os.path.join(config_dir, 'companies', company, 'global.yaml')
    project_dir = os.path.join(config_dir, 'companies', company, project)
    project_config = os.path.join(project_dir, 'global.yaml')
    if os.path.exists(company_config):
        if not os.path.exists(project_dir):
            print project_dir
            os.makedirs(project_dir)
            cgl_copy(company_config, project_config)


def get_company_config():
    """
    Get Company Config (not currently used anywhere)
    :return:
    """
    user_dir = os.path.expanduser("~")
    if 'Documents' in user_dir:
        cg_lumberjack_dir = os.path.join(user_dir, 'cglumberjack', 'companies')
    else:
        cg_lumberjack_dir = os.path.join(user_dir, 'Documents', 'cglumberjack', 'companies')
    return cg_lumberjack_dir


def get_cgl_config():

    user_dir = os.path.expanduser("~")
    if 'Documents' in user_dir:
        cg_lumberjack_dir = os.path.join(user_dir, 'cglumberjack')
    else:
        cg_lumberjack_dir = os.path.join(user_dir, 'Documents', 'cglumberjack')
    return cg_lumberjack_dir


def get_cgl_tools():
    return CONFIG['paths']['cgl_tools']


def publish(path_obj):
    """
    Requires a path with render folder with existing data.
    Creates the next major version of the "USER" directory and copies all source & render files to it.
    Creates the Next Major Version of the "PUBLISH" directory and copies all source & render files to it.
    As a first step these will be the same as whatever is the highest directory.
    :param path_obj: this can be a path object, a string, or a dictionary
    :return: boolean depending on whether publish is successful or not.
    """
    # TODO this could be integrated with PathObject more elegantly
    import logging
    from cgl.core.util import cgl_copy
    path_object = PathObject(path_obj)
    filename = path_object.filename
    resolution = path_object.resolution
    ext = path_object.ext
    # remove filename and ext to make sure we're dealing with a folder
    path_object = path_object.copy(filename='', ext='', resolution='')
    user = path_object.user
    if user != 'publish':
        if path_object.context == 'source':
            source_object = path_object
            render_object = PathObject.copy(path_object, context='render')
        else:
            source_object = PathObject.copy(path_object, context='source')
            render_object = path_object
        # Get the Right Version Number
        source_next = source_object.next_major_version()
        render_next = render_object.copy(version=source_next.version)
        source_pub = source_next.copy(user='publish')
        render_pub = render_next.copy(user='publish')

        for each in os.listdir(source_object.path_root):
            logging.info('Copying Source Resolution %s from %s to %s' % (each, source_object.path_root,
                                                                         source_next.path_root))
            logging.info('Copying Source Resolution %s from %s to %s' % (each, source_object.path_root,
                                                                         source_pub.path_root))
            cgl_copy(os.path.join(source_object.path_root, each), os.path.join(source_next.path_root, each))
            cgl_copy(os.path.join(source_object.path_root, each), os.path.join(source_pub.path_root, each))

        for each in os.listdir(render_object.path_root):
            logging.info('Copying Render Resolution %s from %s to %s' % (each, render_object.path_root,
                                                                         render_next.path_root))
            logging.info('Copying Render Resolution %s from %s to %s' % (each, render_object.path_root,
                                                                         render_pub.path_root))
            cgl_copy(os.path.join(render_object.path_root, each), os.path.join(render_next.path_root, each))
            cgl_copy(os.path.join(render_object.path_root, each), os.path.join(render_pub.path_root, each))
        # Register with Production Management etc...
        CreateProductionData(source_next)
        CreateProductionData(source_pub)

        return render_pub.copy(filename=filename, resolution=resolution, ext=ext)
    return False


def do_review(progress_bar=None, path_object=None):
    import shutil
    import logging
    from cgl.core.util import cgl_copy
    from cgl.ui.widgets.dialog import InputDialog
    job_id = None
    if not path_object:
        print 'No Valid PathObject() found for review'
        return None
    else:
        selection = path_object
    if not os.path.exists(selection.preview_path):
        print('No Web Preview Found, creating one')
        job_info = selection.make_preview()
        job_id = job_info['job_id']
    if selection.context == 'render':
        # lin_images = ['exr', 'dpx']
        # LUMBERMILL REVIEWS
        if PROJ_MANAGEMENT == 'lumbermill':
            # do this for movies
            print 'Lumbermill Not connected to review features'
        # FTRACK REVIEWS
        elif PROJ_MANAGEMENT == 'ftrack':
            if selection.filename:
                if selection.file_type == 'folder' or not selection.file_type:
                    dialog = InputDialog(title='Error: unsupported folder or file_type',
                                         message="%s is a folder or undefined file_type\nunsure how to proceed" %
                                         selection.filename)
                    dialog.exec_()
                    if dialog.button == 'Ok' or dialog.button == 'Cancel':
                        dialog.accept()
                        return
                else:
                    selection.upload_review(job_id=job_id)
                    # CreateProductionData(selection)
            else:
                print('Select file for Review')

        elif PROJ_MANAGEMENT == 'shotgun':
            print 'Shotgun Reviews not connected yet'
        selection.set_attr(filename='')
        selection.set_attr(ext='')
    else:
        dialog = InputDialog(title="Prep for Review", message="Move or copy files to review area?",
                             buttons=['Move', 'Copy'])
        dialog.exec_()
        move = False
        if dialog.button == 'Move':
            move = True
        if selection.file_type == 'sequence':
            # sequence_name = selection.filename
            from_path = os.path.dirname(selection.path_root)
            to_object = PathObject(from_path)
            to_object.set_attr(context='render')
            for each in os.listdir(from_path):
                from_file = os.path.join(from_path, each)
                to_file = os.path.join(to_object.path_root, each)
                if move:
                    shutil.move(from_file, to_file)
                else:
                    cgl_copy(from_file, to_file)
            selection.set_attr(filename='')
            selection.set_attr(ext='')
        else:
            to_object = PathObject.copy(selection, context='render')
            logging.info('Copying %s to %s' % (selection.path_root, to_object.path_root))
            if move:
                shutil.move(selection.path_root, to_object.path_root)
            else:
                cgl_copy(selection.path_root, to_object.path_root)
            selection.set_attr(filename='')
            selection.set_attr(ext='')
    if progress_bar:
        progress_bar.hide()
    return True

