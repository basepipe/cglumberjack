# -*- coding: utf-8 -*-
import glob
import logging
import os
import sys
import re
import shutil
import copy
import subprocess
from cglcore.util import split_all, copy_file
from cglcore import assetcore
from cglcore.config import app_config, UserConfig

PROJ_MANAGEMENT = app_config()['account_info']['project_management']
EXT_MAP = app_config()['ext_map']
ROOT = app_config()['paths']['root']
SEQ_RULES = app_config()['rules']['general']['file_sequence']['regex']
SEQ_REGEX = re.compile("[0-9]{4,}\\.")
SPLIT_SEQ_REGEX = re.compile("\\ [0-9]{4,}-[0-9]{4,}$")
SEQ_SPLIT = re.compile("\\#{4,}")
SEQ2_SPLIT = re.compile("[%0-9]{2,}d")
SEQ = re.compile('[0-9]{3,}-[0-9]{3,}')
# noinspection PyPep8
CGL_SEQ_TEST = re.compile('.+#+.+\s[0-9]+-[0-9]+$')


class PathObject(object):
    """
    Representation of a path on disk
    """

    def __init__(self, path_object=None):
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
        self.frange = None
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
        self.path_root = None  # this gives the full path with the root
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

        if isinstance(path_object, unicode):
            path_object = str(path_object)
        if isinstance(path_object, dict):
            self.process_dict(path_object)
        elif isinstance(path_object, str):
            self.process_string(path_object)
        elif isinstance(path_object, PathObject):
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
        path_object = path_object.replace('\\', '/')
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

    @staticmethod
    def get_attrs_from_config():
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
                    logging.info("Config ERROR: Can't find either %s or %s within app config 'templates'"
                                 % (self.scope, self.context))
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
        for attr in self.template:
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
                if not self.preview_path_full:
                    self.set_preview_path()
                if not self.thumb_path_full:
                    file_ = os.path.splitext(file_)[0]
                    file_ = '%s.jpg' % file_
                    if sys.platform == 'win32':
                        self.thumb_path_full = '%s/%s/%s' % (path_, '.thumb', file_)
                        self.data['thumb_path_full'] = self.thumb_path_full
                    else:
                        self.thumb_path_full = os.path.join(self.root, '.thumb', file_)
                        self.data['thumb_path_full'] = self.thumb_path_full
        if root:
            return self.path_root
        else:
            return self.path        

    def set_attr(self, attr=None, value=None, **kwargs):
        if attr:
            kwargs[attr] = value
        for attr in kwargs:
            value = kwargs[attr]
            try:
                app_config()['rules']['path_variables'][attr]['regex']
            except KeyError:
                logging.debug('Could not find regex for %s: %s in config, skipping' % (attr, value))
            if value == '*':
                self.__dict__[attr] = value
                self.data[attr] = value
                self.set_path()
            else:
                if attr == 'scope':
                    if value:
                        if value in self.scope_list:
                            self.__dict__[attr] = value
                            self.data[attr] = value
                            self.set_path()
                        else:
                            logging.debug('Scope %s not found in globals: %s' % (value, self.scope_list))
                            return
                elif attr == 'context':
                    if value:
                        if value not in self.context_list:
                            logging.debug('Context %s not found in globals: %s' % (value, self.context_list))
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

    def latest_version(self, publish_=False):
        """
        Returns a path to the latest version.
        :return:
        """
        new_obj = copy.deepcopy(self)
        if new_obj.user:
            if publish_:
                new_obj.set_attr(user='publish')
            latest_version = new_obj.glob_project_element('version')
            if latest_version:
                new_obj.set_attr(version=latest_version[-1])
                return new_obj
            else:
                new_obj.set_attr(version='000.000')
        return new_obj

    def next_minor_version_number(self):
        latest_version = self.latest_version()
        major = latest_version.major_version
        minor = latest_version.minor_version
        next_minor = '%03d' % (int(minor) + 1)
        return '%s.%s' % (major, next_minor)

    def next_major_version_number(self):
        """
        Returns a string of the next major Version Number ex. 001.000.   If you need more flexibility use
        next_major_version which will return a PathObject.

        This also takes into account Publish Versions and will return the greater of the Publish Version and
        User Version
        :return:
        """
        major = self.latest_version().major_version
        print 'major', major
        pub_major = self.latest_version(publish_=True).major_version
        print 'pub_major', pub_major
        if int(major) < int(pub_major):
            major = pub_major
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
        # first see if it's a sequence
        result = split_sequence_frange(self.path)
        if result:
            self.path = result[0]
            self.frange = result[1]
        _, file_ext = os.path.splitext(self.path)
        try:
            _type = EXT_MAP[file_ext.lower()]
            if _type:
                if _type == 'movie':
                    self.__dict__['file_type'] = 'movie'
                    self.data['file_type'] = 'movie'
                elif _type == 'image':
                    if '%0' in self.path:
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
            ext = '.mp4'
        elif self.file_type == 'sequence':
            ext = '.mp4'
        elif self.file_type == 'image':
            ext = '.jpg'
        elif self.file_type == 'ppt':
            ext = '.jpg'
        elif self.file_type == 'pdf':
            ext = '.jpg'
        else:
            ext = '.jpg'
        if '#' in self.filename:
            name_ = self.filename.split('#')[0]
            if name_.endswith('.'):
                ext.replace('.', '')
            name_ = '%s%s' % (name_, ext)
        elif '%' in self.filename:
            name_ = self.filename.split('%')[0]
            if name_.endswith('.'):
                ext.replace('.', '')
            name_ = '%s%s' % (name_, ext)
        else:
            name_, o_ext = os.path.splitext(self.filename)
            if o_ext != ext:
                name_ = self.filename.replace(o_ext, ext)
            else:
                name_ = self.filename
        path_ = os.path.split(self.path_root)[0]
        if sys.platform == 'win32':
            self.preview_path_full = '%s/%s/%s' % (path_, '.preview', name_)
            self.data['preview_path_full'] = self.preview_path_full
        else:
            self.preview_path_full = os.path.join(self.root, '.preview', name_)
            self.data['preview_path_full'] = self.preview_path_full

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
        self.company_config = os.path.join(app_config()['account_info']['globals_path'], 'globals.json')
        self.project_config = os.path.join(app_config()['account_info']['globals_path'], 'globals.json')

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
    def __init__(self, path_object=None, file_system=True,
                 project_management=PROJ_MANAGEMENT,
                 proj_management_user=None,
                 do_scope=False, test=False, json=False, create_default_file=False):
        self.proj_management_user = proj_management_user
        self.test = test
        self.path_object = PathObject(path_object)
        self.do_scope = do_scope
        if file_system:
            self.create_folders()
        if project_management:
            logging.debug('Creating Production Management Data for %s: %s' % (project_management,
                                                                              self.path_object.data))
            self.create_project_management_data(self.path_object, project_management)
        if self.path_object.resolution:
            if self.path_object.version == '000.000':
                self.create_default_file()
            if create_default_file:
                if self.path_object.version:
                    self.create_default_file()
        if json:
            self.update_json()

    def update_json(self):
        """
        creates json file, or updates an existing one.
        :return:
        """
        if self.path_object.scope != 'IO':
            if self.path_object.task_json:
                self.update_task_json()
            if self.path_object.asset_json:
                self.update_asset_json()
            if self.path_object.project_json:
                self.update_project_json()

    def update_task_json(self):
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
            self.safe_makedirs(new_obj, test=self.test)

    def create_other_scope(self, path_object):
        if path_object.scope:
            for each in app_config()['rules']['scope_list']:
                if each != path_object.scope:
                    new_obj = path_object.copy(scope=each)
                    self.safe_makedirs(new_obj, test=self.test)
                    self.create_other_context(new_obj)

    @staticmethod
    def safe_makedirs(path_object, test=False):
        if '*' in path_object.path_root:
            path_ = path_object.path_root.split('*')[0]
        else:
            path_ = path_object.path_root
        if path_object.filename:
            path_ = os.path.dirname(path_)
        # at this stage we're making path_
        logging.info('Creating %s Directory: %s' % (path_object.context, path_))
        if not test:
            if not os.path.exists(path_):
                os.makedirs(path_)
        else:
            logging.info('TEST MODE: No directories were created')

    def create_project_management_data(self, path_object, project_management):

        if project_management != 'lumbermill':
            if path_object.filename:
                module = "plugins.project_management.%s.main" % project_management
                # noinspection PyTypeChecker
                loaded_module = __import__(module, globals(), locals(), 'main', -1)
                loaded_module.ProjectManagementData(path_object,
                                                    user_email=self.proj_management_user).create_project_management_data()
            else:
                print('Creating Paths on Disk, lumbermill will create %s '
                      'versions when you add files' % project_management)
        else:
            logging.debug('Using Lumbermill built in proj management')

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


def create_previews(path_object):
    from cglcore.convert import create_thumbnail, create_hd_proxy, create_movie_thumb, create_mov
    path_object = PathObject(path_object)
    preview_dir = os.path.dirname(str(path_object.preview_path_full))
    thumb_dir = os.path.dirname(str(path_object.thumb_path_full))
    if not os.path.exists(preview_dir):
        os.makedirs(preview_dir)
    if not os.path.exists(thumb_dir):
        os.makedirs(thumb_dir)

    if path_object.file_type == 'image':
        if path_object.thumb_path_full:
            logging.info('Creating Thumbnail: %s' % path_object.thumb_path_full)
            create_thumbnail(path_object.path_root, path_object.thumb_path_full)
        if path_object.preview_path_full:
            logging.info('Creating Preview: %s' % path_object.preview_path_full)
            create_hd_proxy(path_object.path_root, path_object.preview_path_full)
    elif path_object.file_type == 'sequence':
        if path_object.thumb_path_full:
            create_movie_thumb(path_object.path_root, path_object.thumb_path_full)
        if path_object.preview_path_full:
            if path_object.file_type == 'sequence':
                # create hdProxy for the exr sequence
                hd_proxy = create_hd_proxy(sequence=path_object.path_root)
                # time.sleep(2)  # if we don't sleep here the directory hasn't had time to refresh.
                create_mov(hd_proxy, output=path_object.preview_path_full)
    elif path_object.file_type == 'movie':
        if path_object.thumb_path_full:
            create_movie_thumb(path_object.path_root, path_object.thumb_path_full)
        if path_object.preview_path_full:
            if path_object.path_root.endswith('mp4'):
                print('Copying %s to %s' % (path_object.path_root, path_object.preview_path_full))
                copy_file(path_object.path_root, path_object.preview_path_full)
            else:
                create_mov(path_object.path_root, output=path_object.preview_path_full)
    else:
        print path_object.file_type, 'is not set up for preview creation'


def image_path(image=None):
    if image:
        return os.path.join(app_config()['paths']['code_root'], 'resources', 'images', image)
    else:
        return os.path.join(app_config()['paths']['code_root'], 'resources', 'images')


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


def start_url(url):
    import webbrowser
    webbrowser.open(url)


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
        string = '%s.' % string
        this = re.sub(SEQ_REGEX, string, basename)
        return this
    else:
        return basename


def get_frange_from_seq(filepath):
    _, ext = os.path.splitext(filepath)
    glob_string = filepath.split('#')[0]
    frames = glob.glob('%s*%s' % (glob_string, ext))
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


def lj_list_dir(directory, path_filter=None, basename=True, return_sequences=False):
    """
    Returns Files that are ready to be displayed in a LJWidget, essentially we run
    all output
    :param path_filter: return a specific element from the path rather than the filename.  For instance if you
    wanted to pull out only the "shot" name you'd use 'shot' as a path filter.
    :param basename: if true we only return the os.path.basename() result of the string.
    :param return_sequences:
    :param directory:
    :return: list of prepared files/items.
    """
    ignore = ['publish_data.csv']
    print 'Directory is:', directory
    print os.listdir(directory)
    list_ = os.listdir(directory)
    print list_
    if not list_:
        return
    list_.sort()
    output_ = []
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
    if return_sequences:
        seq_only = []
        for each in output_:
            this = re.search(CGL_SEQ_TEST, each)
            if this:
                seq_only.append(each)
        return seq_only
    else:
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
    """
    Splits a sequence with a match for ######, as well as %0#d
    :param sequence:
    :return:
    """
    frange = None
    group = None
    if '#' in sequence:
        frange = re.search(SEQ_SPLIT, sequence)
        group = frange.group(0)
    elif '%' in sequence:
        frange = re.search(SEQ2_SPLIT, sequence)
        group = frange.group(0)
    elif '.*.' in sequence:
        frange = 'this'
        group = '*.'
    if frange:
        return sequence.split(group)[0]
    else:
        return


def get_file_icon(filepath):
    ip = icon_path('picture24px.png')
    if "." not in filepath:
        ip = icon_path('folder24px.png')
    if '###' in filepath:
        ip = icon_path('sequence24px.png')
    return ip


def get_file_type(filepath):
    ft = 'file'
    if "." not in filepath:
        ft = 'folder'
    if '###' in filepath:
        ft = 'sequence'
    return ft


def get_company_config():
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
    return app_config()['paths']['cgl_tools']


def hash_to_number(sequence):
    frange = re.search(SEQ_SPLIT, sequence)
    count = frange.group(0).count('#')
    if count < 10:
        num = '%0'+str(count)+'d'
    else:
        num = '%'+str(count)+'d'
    return frange.group(0), num


def number_to_hash(sequence, full=False):
    frange = re.search(SEQ2_SPLIT, sequence)
    number = frange.group(0)
    count = frange.group(0).replace('%', '').replace('d', '')
    if full:
        return sequence.replace(number, '%'+count+'d')
    else:
        return '#'*int(count), '%'+count+'d'


def get_start_frame(sequence):
    dir_ = os.path.split(sequence)[0]
    results = lj_list_dir(dir_)
    for each in results:
        this = re.search(SEQ, each)
        if this:
            return this.group(0).split('-')[0]
    return None


def prep_seq_delimiter(sequence, replace_with='*', ext=None):
    """
    takes a sequence ('####', '%04d', '*') transforms it to another type.  This is used for instances where one
    piece of software needs sequences delimited in a particular way.
    :param sequence: file sequence - sequence.*.dpx, sequence.%04d.dpx, sequence.####.dpx
    :param replace_with: '*': for sequences like .*.dpx, '%': for %04d style sequence definition, '#': for '####'
    :param ext: extension
    style sequence definition
    :return:
    """
    path_object = PathObject(sequence)
    if not ext:
        ext = path_object.ext
    dir_ = os.path.dirname(sequence)
    seq_split = split_sequence(sequence)
    stuff = lj_list_dir(dir_)
    hash_seq = ''
    for each in stuff:
        this = re.search(SEQ, each)
        if this:
            frange = this.group(0).split('-')[0]
            hash_seq = each.replace(' %s' % frange, '')
    if replace_with == '*':
        return '%s%s.%s' % (split_sequence(sequence), replace_with, ext)
    elif replace_with == '#':
        return os.path.join(dir_, hash_seq)
    elif replace_with == '%':
        return '%s%s.%s' % (seq_split, hash_to_number(hash_seq)[-1], ext)
    elif replace_with == '':
        return '%s.%s' % (split_sequence(sequence), ext)


def publish(path_obj):
    """
    Requires a path with render folder with existing data.
    Creates the next major version of the "USER" directory and copies all source & render files to it.
    Creates the Next Major Version of the "PUBLISH" directory and copies all source & render files to it.
    As a first step these will be the same as whatever is the highest directory.
    :param path_obj: this can be a path object, a string, or a dictionary
    :return: boolean depending on whether publish is successful or not.
    """
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
            shutil.copytree(os.path.join(source_object.path_root, each), os.path.join(source_next.path_root, each))
            shutil.copytree(os.path.join(source_object.path_root, each), os.path.join(source_pub.path_root, each))

        for each in os.listdir(render_object.path_root):
            logging.info('Copying Render Resolution %s from %s to %s' % (each, render_object.path_root,
                                                                         render_next.path_root))
            logging.info('Copying Render Resolution %s from %s to %s' % (each, render_object.path_root,
                                                                         render_pub.path_root))
            shutil.copytree(os.path.join(render_object.path_root, each), os.path.join(render_next.path_root, each))
            shutil.copytree(os.path.join(render_object.path_root, each), os.path.join(render_pub.path_root, each))
        # Register with Production Management etc...
        CreateProductionData(source_next)
        CreateProductionData(source_pub)

        return render_pub.copy(filename=filename, resolution=resolution, ext=ext)
    return False






