# -*- coding: utf-8 -*-
import glob
import logging
import os
import sys
import re
import shutil
import copy
import subprocess
from cglcore.util import split_all
from cglcore import assetcore
from cglcore.config import app_config, UserConfig

PROJ_MANAGEMENT = app_config()['account_info']['project_management']
EXT_MAP = app_config()['ext_map']
ROOT = app_config()['paths']['root']
SEQ_RULES = app_config()['rules']['general']['file_sequence']['regex']
SEQ_REGEX = re.compile("\\.[0-9]{4,}\\.")
SPLIT_SEQ_REGEX = re.compile("\\ [0-9]{4,}-[0-9]{4,}$")
SEQ_SPLIT = re.compile("\\#{4,}")


class PathObject(object):
    """
    Representation of a path on disk
    """

    def __init__(self, path_object=None, **kwargs):
        if not path_object:
            logging.error('No Path Object supplied')
            return
        self.data = {}
        self.root = app_config()['paths']['root'].replace('\\', '/')
        self.company = None
        self.project = None
        self.scope = None
        self.context = None
        self.seq = None
        self.shot = None
        self.type = None
        self.asset = None
        self.variant = None
        self.user = None
        self.version = None
        self.major_version = None
        self.minor_version = None
        self.ext = None
        self.filename = None
        self.filename_base = None
        self.resolution = None
        self.frame = None
        self.aov = None
        self.render_pass = None
        self.shotname = None
        self.task = None
        self.cam = None
        self.file_type = None
        self.scope_list = app_config()['rules']['scope_list']
        self.context_list = app_config()['rules']['context_list']
        self.path = None  # string of the properly formatted path
        self.path_root = None # this gives the full path with the root
        self.thumb_path_full = None
        self.preview_path_full = None
        self.start_frame = None
        self.end_frame = None
        self.frame_rate = None
        self.template = []
        self.actual_resolution = None
        self.date_created = None
        self.date_modified = None
        self.project_config = None
        self.company_config = None
        self.software_config = None
        self.asset_json = None
        self.shot_json = None
        self.task_json = None
        self.project_json = None
        self.status = None
        self.due = None
        self.assigned = None
        self.priority = None
        self.ingest_source = '*'

        if type(path_object) is unicode:
            path_object = str(path_object)
        if type(path_object) is dict:
            self.process_dict(path_object)
        elif type(path_object) is str:
            self.process_string(path_object)
        elif type(path_object) is PathObject:
            self.process_dict(path_object.data)
        else:
            logging.error('type: %s not expected' % type(path_object))

    def set_status(self):
        if not self.status:
            if self.version == '000.000':
                self.status = 'assigned'
            if self.user == 'publish':
                self.status = 'published'
            if self.minor_version != '000.000':
                self.status = 'in progress'
        if not self.assigned:
            self.assigned = self.user
        if not self.priority:
            self.priority = 'medium'

    def process_string(self, path_object):
        self.get_company(path_object)
        self.unpack_path(path_object)
        self.set_data_from_attrs()
        self.set_project_config()
        self.set_json()

    def process_dict(self, path_object):
        self.set_attrs_from_dict(path_object)
        self.set_path()
        self.set_project_config()
        self.set_json()

    def get_attrs_from_config(self):
        attrs = []
        for key in app_config()['rules']['path_variables']:
            attrs.append(key)
        return attrs

    def set_attrs_from_dict(self, path_object):
        if 'company' not in path_object:
            logging.error('No company attr found in %s - invalid dict' % path_object)
            return
        for key in path_object:
            self.data[key] = path_object[key]
            self.set_attr(attr=key, value=path_object[key])
        if self.version:
            major_version, minor_version = self.version.split('.')
            self.set_attr(major_version=major_version.replace('.', ''))
            self.set_attr(minor_version=minor_version.replace('.', ''))
        self.set_shotname()

    def get_last_attr(self):
        current_ = 'company'
        self.get_template()
        for t in self.template:
            if t in self.data:
                if self.data[t]:
                    current_ = t
            elif t in app_config()['rules']['scope_list']:
                current_ = 'scope'
        return current_

    def get_template(self):
        self.template = []
        if self.context:
            if self.scope:
                if self.scope == '*':
                    self.template = ['company', 'context', 'project', 'scope']
                    return
                try:
                    path_template = app_config()['templates'][self.scope][self.context]['path'].split('/')
                    if path_template[-1] == '':
                        path_template.pop(-1)
                    version_template = app_config()['templates'][self.scope][self.context]['version'].split('/')
                    template = path_template + version_template
                    for each in template:
                        each = each.replace('{', '').replace('}', '')
                        if each == 'filename.ext':
                            each = 'filename'
                        self.template.append(each)
                    return self.template
                except KeyError:
                    logging.info("Config ERROR: Can't find either %s or %s within app config 'templates'" % (self.scope, self.context))
                    return
            else:
                self.template = ['company', 'context', 'project', 'scope']
        else:
            self.template = ['company']

    def set_scope_list(self):
        self.scope_list = app_config()['rules']['scope_list']

    def set_context_list(self):
        self.context_list = app_config()['rules']['context_list']
        for key in app_config()['templates']:
            if key not in self.context_list:
                self.context_list.append(key)
                for scope in app_config()['templates'][key]:
                    if scope not in self.scope_list:
                        self.scope_list.append(scope)

    def keys(self):
        self.data.keys()

    def set_data_from_attrs(self):
        for each in self.__dict__:
            if each in self.get_attrs_from_config():
                self.data[each] = self.__dict__[each]

    def get_company(self, path_string):
        # TODO - we need to do something based off the order of the regex labels in the config here, this is VERY
        # proned to error. We have to figure out how to make sure we have a valid, registered company somehow.  This
        # can be something we do upon creatoin of a company through the interface, but needs to handle companies outside
        # the interface as well.
        path_string = path_string.replace('\\', '/')
        try:
            temp_ = path_string.split(self.root)[-1]
            temp_ = temp_.replace('\\', '/')
            c = split_all(temp_)[1]
            self.set_attr(company=c)
        except IndexError:
            self.set_attr(company='*')

    def unpack_path(self, path_string):
        path_string = os.path.normpath(path_string.split(self.company)[-1])
        path_ = os.path.normpath(path_string)
        path_parts = path_.split(os.sep)
        if path_parts[0] == '':
            path_parts.pop(0)
        path_parts.insert(0, self.company)
        self.set_attr(context=path_parts[1].lower())
        if len(path_parts) > 3:
            self.set_attr(scope=path_parts[3].lower())
        self.get_template()
        self.data = {}
        for i, attr in enumerate(self.template):
            if attr:
                attr = attr.replace('{', '').replace('}', '')
                try:
                    if attr == self.context:
                        pass
                    elif attr == self.scope:
                        pass
                    elif attr == 'filename':
                        self.set_attr(filename=path_parts[i])
                        filename_base, ext = os.path.splitext(path_parts[i])
                        self.set_attr(filename_base=filename_base)
                        self.set_attr(ext=ext.replace('.', ''))
                    else:
                        self.set_attr(attr=attr, value=path_parts[i])
                except IndexError:
                    pass

        if not self.seq:
            self.set_attr(seq=self.type)
        if not self.shot:
            self.set_attr(shot=self.asset)
        if not self.asset:
            self.set_attr(asset=self.shot)
        if not self.type:
            self.set_attr(type=self.seq)
        if self.version:
            major_version, minor_version = self.version.split('.')
            self.set_attr(major_version=major_version.replace('.', ''))
            self.set_attr(minor_version=minor_version.replace('.', ''))
        self.set_shotname()

    def set_path(self, root=False):
        self.get_template()
        keep_if = self.context_list + self.scope_list
        path_string = ''
        for i, attr in enumerate(self.template):
            if attr:
                # build an array based off the template
                if attr in keep_if:
                    path_string = os.path.join(path_string, attr)
                elif attr == 'filename.ext':
                    path_string = os.path.join(path_string, self.__dict__['filename'])
                else:
                    if self.__dict__[attr]:
                        path_string = os.path.join(path_string, self.__dict__[attr])
        path_string = path_string.replace('\\', '/')
        if sys.platform == 'win32':
            self.path_root = '%s/%s' % (self.root, path_string)
            path_, file_ = os.path.split(self.path_root)
        else:
            self.path_root = os.path.join(self.root, path_string).replace('\\', '/')
            path_, file_ = os.path.split(self.path_root)
        self.path = path_string
        if self.filename:
            if self.filename != '*':
                self.set_file_type()
                self.set_preview_path()
                if sys.platform == 'win32':
                    self.thumb_path_full = '%s\\%s\\%s' % (path_, '.thumb', file_)
                else:
                    self.thumb_path_full = os.path.join(self.root, '.thumb', file_)
        if root:
            return self.path_root
        else:
            return self.path        

    def set_attr(self, attr=None, value=None, **kwargs):
        regex = ''
        if attr:
            kwargs[attr] = value
        for attr in kwargs:
            value = kwargs[attr]
            try:
                regex = app_config()['rules']['path_variables'][attr]['regex']
            except KeyError:
                logging.info('Could not find regex for %s in config, skipping' % attr)
            if value == '*':
                self.__dict__[attr] = value
                self.data[attr] = value
                self.set_path()
            else:
                if value == 'io':
                    value = value.upper()
                if attr == 'scope':
                    if value:
                        if value in self.scope_list:
                            self.__dict__[attr] = value
                            self.data[attr] = value
                            self.set_path()
                        else:
                            logging.error('Scope %s not found in globals: %s' % (value, self.scope_list))
                            return
                elif attr == 'context':
                    if value:
                        if value not in self.context_list:
                            logging.error('Context %s not found in globals: %s' % (value, self.context_list))
                            return
                        else:
                            self.__dict__[attr] = value
                            self.data[attr] = value
                            self.set_path()
                else:
                    self.__dict__[attr] = value
                    self.data[attr] = value
                    self.set_path()
            if attr == 'shot':
                self.__dict__['asset'] = value
                self.data['asset'] = value
                self.set_path()
            elif attr == 'asset':
                self.__dict__['shot'] = value
                self.data['shot'] = value
                self.set_path()
            elif attr == 'seq':
                self.__dict__['type'] = value
                self.data['type'] = value
                self.set_path()
            elif attr == 'type':
                self.__dict__['seq'] = value
                self.data['seq'] = value
                self.set_path()
            elif attr == 'ext':
                if self.filename:
                    base, ext = os.path.splitext(self.filename)
                    self.filename = '%s.%s' % (base, self.ext)
                    self.set_path()
            elif attr == 'filename':
                if value:
                    self.__dict__['filename'] = value
                    self.data['filename'] = value
                    base, ext = os.path.splitext(value)
                    self.__dict__['ext'] = ext.replace('.', '')
                    self.data['ext'] = ext.replace('.', '')
                    self.__dict__['filename_base'] = base
                    self.data['filename_base'] = base
                    self.set_path()
            elif attr == 'version':
                if value:
                    if value is not '*' and value is not '.':
                        major, minor = value.split('.')
                    else:
                        major = '000'
                        minor = '000'
                    self.__dict__['major_version'] = major
                    self.data['major_version'] = major
                    self.__dict__['minor_version'] = minor
                    self.data['minor_version'] = minor
                    self.set_path()

    def glob_project_element(self, attr, full_path=False):
        """
        returns all of the project elements of type "attr" from the system.  Example - you want all projects on disk.
        glob_project_element(attr='project')
        :param self: self
        :param attr: attribute name: 'project', 'scope', 'version', filename, etc...
        :param full_path: if True returns full paths for everything globbed
        :return: returns list of items, or paths.
        """

        list_ = []
        index = self.template.index(attr)
        parts = self.path.split('/')
        i = 0
        path_ = ''
        if index < len(parts):
            while i < index:
                path_ = os.path.join(path_, parts[i])
                i += 1
            path_ = os.path.join(path_, '*')
            path_ = os.path.join(self.root, path_)
            if not full_path:
                for each in glob.glob(path_):
                    list_.append(os.path.basename(each))
            else:
                list_ = glob.glob(path_)
            return list_
        else:
            return []

    def split_after(self, attr):
        # TODO - this must be updated to match how glob_project_element works
        """
        convenience function that returns the path after splitting it at the desired attribute.
        for example split at project would return the path up to and including the project variable.
        :param attr:
        :return:
        """
        value = self.data[attr]
        return os.path.join(self.path_root.split(value)[0], value).replace('\\', '/')

    def glob_multiple_project_elements(self, full_path=False, split_at=None, elements=[]):
        """

        :param self:
        :param split_at:
        :param args:
        :return:
        """
        path_ = self.path_root
        if split_at:
            try:
                index = self.template.index(split_at)
            except ValueError:
                if split_at == 'shot':
                    index = self.template.index('asset')
            split_entity = self.template[index+1]
            path_ = path_.split(self.data[split_entity])[0]
            if path_.endswith('\\'):
                path_ = path_[:-1]
        obj_ = PathObject(path_)
        for attr in elements:
            obj_.set_attr(attr, '*', regex=False)
        glob_list = glob.glob(obj_.path_root)
        return glob_list

    def glob_multiple(self, *args):
        glob_object = self.copy()
        glob_object.eliminate_wild_cards()
        d = {}
        highest_index = None
        for each in args:
            glob_object.set_attr(attr=each, value='*')
            index = self.template.index(each)
            if index > highest_index:
                highest_index = index
            d[str(index)] = each
        split_at = self.template[highest_index]
        return glob_object.glob_project_element(attr=split_at)

    def eliminate_wild_cards(self):
        """
        this goes through a path object and changes all items with astrix into empty strings
        :return:
        """
        for key in self.__dict__:
            if self.__dict__[key] == '*':
                self.__dict__[key] = ''
                self.data[key] = ''
        self.set_path()

    def copy(self, latest=False, set_proper_filename=False, **kwargs):
        new_obj = copy.deepcopy(self)
        for attr in kwargs:
            new_obj.set_attr(attr=attr, value=kwargs[attr])
        if set_proper_filename:
            new_obj.set_proper_filename()
        if latest:
            return new_obj.latest_version()
        else:
            return new_obj

    def latest_version(self):
        """
        Returns a path to the latest version.
        :return:
        """
        new_obj = copy.deepcopy(self)
        if new_obj.user:
            latest_version = new_obj.glob_project_element('version')
            if latest_version:
                new_obj.set_attr(version=latest_version[-1])
                return new_obj
            else:
                new_obj.set_attr(version='000.000')
        return new_obj

    def next_minor_version_number(self):
        if self.version:
            major, minor = self.version.split('.')
            self.major_version = major
            self.minor_version = minor
        if not self.minor_version:
            next_minor = '001'
        else:
            next_minor = '%03d' % (int(self.minor_version)+1)
        if not self.major_version:
            self.set_attr(major_version='000')
        return '%s.%s' % (self.major_version, next_minor)

    def next_major_version_number(self):
        """
        Returns a string of the next major Version Number ex. 001.000.   If you need more flexibility use
        next_major_version which will return a PathObject.
        :return:
        """
        major = self.latest_version().major_version
        next_major = '%03d' % (int(major)+1)
        return '%s.%s' % (next_major, '000')

    def next_major_version(self):
        """
        Returns the next major version within the user's context.   This takes into account circumstances like the
        following:  current version is 003.000, latest version is 005.000, next major_version would be 006.000
        :return:
        """
        next_major = self.next_major_version_number()
        new_obj = copy.deepcopy(self)
        new_obj.set_attr(version=next_major)
        return new_obj

    def new_minor_version_object(self):
        # TODO - this will need to take into account Publish Versions eventually
        next_minor = self.next_minor_version_number()
        new_obj = copy.deepcopy(self)
        new_obj.set_attr('version', next_minor)
        return new_obj

    def set_file_type(self):
        """
        sets attr 'file_type' to reflect the kind of file we're working with, or to let me know if it's a folder
        this is just a convenience attr when working with pathObjects
        :return:
        """
        _, file_ext = os.path.splitext(self.path)
        try:
            _type = EXT_MAP[file_ext]
            if _type:
                if _type == 'movie':
                    self.__dict__['file_type'] = 'movie'
                    self.data['file_type'] = 'movie'
                elif _type == 'image':
                    if '%04d' in self.path:
                        self.__dict__['file_type'] = 'sequence'
                        self.data['file_type'] = 'sequence'
                    elif '####' in self.path:
                        self.__dict__['file_type'] = 'sequence'
                        self.data['file_type'] = 'sequence'
                    else:
                        self.__dict__['file_type'] = 'image'
                        self.data['file_type'] = 'image'
                else:
                    self.__dict__['file_type'] = _type
                    self.data['file_type'] = _type
            else:
                pass
        except KeyError:
            self.__dict__['file_type'] = None
            self.data['file_type'] = None

    def set_preview_path(self):
        if self.file_type == 'movie':
            ext = '.mov'
        elif self.file_type == 'sequence':
            ext = '.mov'
        elif self.file_type == 'image':
            ext = '.jpg'
        elif self.file_type == 'ppt':
            ext = '.jpg'
        elif self.file_type == 'pdf':
            ext = '.jpg'
        else:
            ext = '.jpg'
        name_ = self.filename.replace('####', '')
        name_, o_ext = os.path.splitext(name_)
        name_ = name_.replace(o_ext, ext)
        path_, file_ = os.path.split(self.path_root)
        if sys.platform == 'win32':
            self.preview_path_full = '%s\\%s\\%s' % (path_, '.preview', name_)
        else:
            self.preview_path_full = os.path.join(self.root, '.preview', name_)

    def set_proper_filename(self):
        # TODO - this needs to be basted off formulas like the path object.  Curses.
        self.filename_base = '%s_%s_%s' % (self.seq, self.shot, self.task)
        if self.ext:
            self.filename = '%s.%s' % (self.filename_base, self.ext)
        self.set_path()

    def set_shotname(self):
        self.set_attr(shotname='%s_%s' % (self.seq, self.shot))
        self.set_attr(assetname='%s_%s' % (self.seq, self.shot))

    def set_project_config(self):
        user_dir = os.path.expanduser("~")
        if 'Documents' in user_dir:
            cg_lumberjack_dir = os.path.join(user_dir, 'cglumberjack', 'companies')
        else:
            cg_lumberjack_dir = os.path.join(user_dir, 'Documents', 'cglumberjack', 'companies')
        if self.company:
            self.company_config = os.path.join(cg_lumberjack_dir, self.company, 'global.yaml')
        if self.project:
            self.project_config = os.path.join(os.path.dirname(self.company_config), self.project, 'global.yaml')

    def set_json(self):
        json_obj = self.copy(latest=True, context='render', ext='json', task='lay', set_proper_filename=True)
        self.asset_json = json_obj.path_root
        self.shot_json = json_obj.path_root
        if self.task:
            json_obj = self.copy(context='render', ext='json', set_proper_filename=True)
            self.task_json = json_obj.path_root
        if self.project:
            proj_name = json_obj.data['project']
            self.project_json = os.path.join(json_obj.path_root.split(proj_name)[0], proj_name, '%s.json' % proj_name)


class CreateProductionData(object):
    def __init__(self, path_object=None, file_system=True, project_management=PROJ_MANAGEMENT,
                 do_scope=False, test=False, json=True):
        self.test = test
        self.path_object = PathObject(path_object)
        self.do_scope = do_scope
        if file_system:
            self.create_folders()
        if project_management:
            logging.info('Creating Production Management Data for %s: %s' % (project_management, self.path_object.data))
            self.create_project_management_data(self.path_object, project_management)
        if self.path_object.resolution:
            if self.path_object.version == '000.000':
                self.create_default_file()
        #if json:
        #    self.update_json()

    def update_json(self):
        """
        creates json file, or updates an existing one.
        :return:
        """
        if self.path_object.scope != 'IO':
            if self.path_object.task_json:
                self.update_task_json(assigned=self.path_object.user, priority=self.path_object.priority,
                                      status=self.path_object.status)
            if self.path_object.asset_json:
                self.update_asset_json()
            if self.path_object.project_json:
                self.update_project_json()

    def update_task_json(self, status=None, priority=None, due=None, assigned=None):
        """
        if task_json doesn't exist it creates one, if it does exist it edits it with the new information
        :return:
        """
        self.path_object.set_status()
        if os.path.exists(self.path_object.task_json):
            asset_meta = assetcore.MetaObject(jsonfile=self.path_object.task_json)
        else:
            asset_meta = assetcore.MetaObject()
        name = '%s_%s_%s' % (self.path_object.seq, self.path_object.shot, self.path_object.task)

        asset_meta.add(_type='init',
                       name=name,
                       task=self.path_object.task,
                       type='init',
                       uid=name,
                       source_path=self.path_object.path,
                       status=self.path_object.status,
                       due=self.path_object.due,
                       assigned=self.path_object.assigned,
                       priority=self.path_object.priority
                       )
        if not os.path.exists(os.path.dirname(self.path_object.path_root)):
            os.makedirs(os.path.dirname(self.path_object.path_root))
        asset_meta.save(self.path_object.task_json)

    def update_asset_json(self):
        obj = self.path_object
        if os.path.exists(obj.asset_json):
            asset_meta = assetcore.MetaObject(jsonfile=obj.asset_json)
        else:
            asset_meta = assetcore.MetaObject()
        new_obj = PathObject(str(obj.task_json))
        asset_meta.add(_type='link',
                       name=self.path_object.task,
                       task=self.path_object.task,
                       type='link',
                       uid=self.path_object.task,
                       added_from='system',
                       json=new_obj.path,
                       scope=obj.scope,
                       status=obj.status
                       )
        if not os.path.exists(os.path.dirname(obj.asset_json)):
            os.makedirs(os.path.dirname(obj.asset_json))
        asset_meta.save(obj.asset_json)

    def update_project_json(self):
        if os.path.exists(self.path_object.project_json):
            project_meta = assetcore.MetaObject(jsonfile=self.path_object.project_json)
        else:
            project_meta = assetcore.MetaObject()
        asset_obj = PathObject(str(self.path_object.asset_json))
        if self.path_object.user == 'publish':
            status = 'published'
        else:
            status = 'in progress'
        project_meta.add(_type='link',
                         name="%s_%s" % (self.path_object.seq, self.path_object.shot),
                         type='link',
                         uid="%s_%s" % (self.path_object.seq, self.path_object.shot),
                         added_from='system',
                         task='lay',
                         json=asset_obj.path,
                         status=status,
                         scope=self.path_object.scope
                         )
        project_meta.save(self.path_object.project_json)

    def create_folders(self):
        if not self.path_object.root:
            logging.info('No Root Defined')
            return
        if not self.path_object.company:
            logging.info('No Company Defined')
            return
        if not self.path_object.context:
            self.path_object.set_attr(context='source')
        self.safe_makedirs(self.path_object, test=self.test)
        self.create_other_context(self.path_object)
        if self.do_scope:
            self.create_other_scope(self.path_object)

    def create_other_context(self, path_object):
        d = {'source': 'render', 'render': 'source'}  # TODO this should be in the config somewhere
        if path_object.context:
            new_context = d[path_object.context]
            new_obj = path_object.copy(context=new_context)
            self.safe_makedirs(new_obj)

    def create_other_scope(self, path_object):
        if path_object.scope:
            for each in app_config()['rules']['scope_list']:
                if each != path_object.scope:
                    new_obj = path_object.copy(scope=each)
                    self.safe_makedirs(new_obj)
                    self.create_other_context(new_obj)

    @staticmethod
    def safe_makedirs(path_object, test=False):
        if '*' in path_object.path_root:
            path_ = path_object.path_root.split('*')[0]
        else:
            path_ = path_object.path_root
        if path_object.ext:
            if os.path.splitext(path_):
                path_ = os.path.dirname(path_)
        if not test:
            if not os.path.exists(path_):
                os.makedirs(path_)
        else:
            print 'TEST MODE: makeing dirs: %s' % path_

    @staticmethod
    def create_project_management_data(path_object, project_management):
        # TODO I need to do something that syncs my globals to the cloud in case they get toasted.
        # management software
        # and another studio wants a different kind of project management software by default.
        if project_management != 'lumbermill':
            module = "plugins.project_management.%s.main" % project_management
            loaded_module = __import__(module, globals(), locals(), 'main', -1)
            loaded_module.ProjectManagementData(path_object).create_project_management_data()
        else:
            print 'Using Lumbermill built in proj management'

    def create_default_file(self):
        if self.path_object.task == 'prev':
            self.copy_default_file('maya', 'mb')
        if self.path_object.task == 'mdl':
            self.copy_default_file('maya', 'mb')
        if self.path_object.task == 'shd':
            self.copy_default_file('maya', 'mb')
        if self.path_object.task == 'anim':
            self.copy_default_file('maya', 'mb')
        if self.path_object.task == 'lite':
            self.copy_default_file('maya', 'mb')
        if self.path_object.task == 'comp':
            self.copy_default_file('nuke', 'nk')

    def copy_default_file(self, software, ext):
        self.path_object.set_attr(filename='%s_%s_%s.%s' % (self.path_object.seq,
                                                            self.path_object.shot,
                                                            self.path_object.task,
                                                            ext))
        this = __file__.split('src')[0]
        default_file = "%ssrc/%s" % (this, r'plugins/%s/templates/default.%s' % (software, ext))
        logging.info('Creating Default %s file: %s' % (self.path_object.task, self.path_object.path_root))
        shutil.copy2(default_file, self.path_object.path_root)


def icon_path(icon=None):
    if icon:
        return os.path.join(app_config()['paths']['code_root'], 'resources', 'icons', icon)
    else:
        return os.path.join(app_config()['paths']['code_root'], 'resources', 'icons')


def font_path():
    return os.path.join(app_config()['paths']['code_root'], 'resources', 'fonts')


def get_projects(company):
    d = {'root': ROOT,
         'company': company,
         'project': '*',
         'context': 'source'}
    path_object = PathObject(d)
    return path_object.glob_project_element('project')


def get_companies():
    d = {'root': ROOT,
         'company': '*'
         }
    path_object = PathObject(d)
    return path_object.glob_project_element('company')


def start(filepath):
    cmd = "cmd /c start "
    if sys.platform == "darwin":
        cmd = "open "
    elif sys.platform == "linux2":
        cmd = "xdg-open "
    else:
        if os.path.isfile(filepath):
            os.startfile(filepath)
            return
    command = (cmd + filepath)

    subprocess.Popen(command, shell=True)


def replace_illegal_filename_characters(filename):
    return re.sub(r'[^A-Za-z0-9\.#]+', '_', filename)


def show_in_folder(path_string):
    full_path = os.path.dirname(path_string)
    if sys.platform == "darwin":
        cmd = 'open '
    elif sys.platform == "linux2":
        cmd = 'xdg-open '
    else:
        cmd = r"cmd /c start "
        full_path = full_path.replace('/', '\\')

    command = (cmd + full_path)
    logging.info("running command: %s" % command)
    subprocess.Popen(command, shell=True)


def create_project_config(company, project):
    config_dir = os.path.dirname(UserConfig().user_config_path)
    company_config = os.path.join(config_dir, 'companies', company, 'global.yaml')
    project_dir = os.path.join(config_dir, 'companies', company, project)
    project_config = os.path.join(project_dir, 'global.yaml')
    if os.path.exists(company_config):
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
            shutil.copy2(company_config, project_config)


def seq_from_file(basename):
    numbers = re.search(SEQ_REGEX, basename)
    if numbers:
        numbers = numbers.group(0).replace('.', '')
        string = '#' * int(len(numbers))
        string = '.%s.' % string
        this = re.sub(SEQ_REGEX, string, basename)
        return this
    else:
        return basename


def get_frange_from_seq(filepath):
    glob_string = filepath.split('#')[0]
    frames = glob.glob('%s*' % glob_string)
    if frames:
        sframe = re.search(SEQ_REGEX, frames[0]).group(0).replace('.', '')
        eframe = re.search(SEQ_REGEX, frames[-1]).group(0).replace('.', '')
        if sframe and eframe:
            return '%s-%s' % (sframe, eframe)
    else:
        return None


def test_string_against_path_rules(variable, string):
    regex = app_config()['rules']['path_variables'][variable]['regex']
    example = app_config()['rules']['path_variables'][variable]['example']
    compiled_regex = re.compile(r'%s' % regex)
    if re.match(compiled_regex, string):
        return ''
    else:
        message_string = '%s is not a valid %s: \n\n%s' % (string, variable, example)
        return message_string


def load_style_sheet(style_file='stylesheet.css'):
    f = open(style_file, 'r')
    data = f.read()
    data.strip('\n')
    # path = APP_PATH.replace('\\', '/')
    # data = data.replace('<PATH>', path)
    return data


def lj_list_dir(directory, path_filter=None, basename=False):
    """
    Returns Files that are ready to be displayed in a LJWidget, essentially we run
    all output
    :param list_: list to put into the table.
    :param path_filter: return a specific element from the path rather than the filename.  For instance if you
    wanted to pull out only the "shot" name you'd use 'shot' as a path filter.
    :param basename: if true we only return the os.path.basename() result of the string.
    :return: list of prepared files/items.
    """
    ignore = ['publish_data.csv']
    list_ = os.listdir(directory)
    if not list_:
        return
    list_.sort()
    output_ = []
    dirname = os.path.dirname(list_[0])
    for each in list_:
        if path_filter:
            filtered = PathObject(each).data[path_filter]
            output_.append([filtered])
        else:
            if basename:
                seq_string = str(seq_from_file(os.path.basename(each)))
                if seq_string:
                    if seq_string not in output_:
                        output_.append(seq_string)
                else:
                    output_.append(each)
            else:
                output_.append(each)
    for each in output_:
        if '#' in each:
            frange = get_frange_from_seq(os.path.join(directory, each))
            if frange:
                index = output_.index(each)
                output_[index] = '%s %s' % (each, frange)
        if each in ignore:
            output_.remove(each)
    return output_


def split_sequence_frange(sequence):
    """
    takes the result of a lj_list_dir, and gives back the file path as well as the sequence
    :return:
    """
    frange = re.search(SPLIT_SEQ_REGEX, sequence)
    if frange:
        return sequence.split(frange.group(0))[0], frange.group(0).replace(' ', '')
    else:
        return

def split_sequence(sequence):
    frange = re.search(SEQ_SPLIT, sequence)
    print frange
    print frange.group(0)
    if frange:
        return sequence.split(frange.group(0))[0]
    else:
        return


def get_file_icon(filepath):
    if "." not in filepath:
        ip = icon_path('folder24px.png')
    if '###' in filepath:
        ip = icon_path('sequence24px.png')
    return ip


def get_file_type(filepath):
    if "." not in filepath:
        ft = 'folder'
    if '###' in filepath:
        ft = 'sequence'
    return ft







