# -*- coding: utf-8 -*-
import glob
import pyperclip
import click
import logging
import os
import sys
import re
import copy
import importlib
from cgl.core.utils.general import split_all, cgl_copy, cgl_execute, clean_file_list
from cgl.core.config import app_config, UserConfig
from cgl.core import convert

CONFIG = app_config()
PROJ_MANAGEMENT = CONFIG['account_info']['project_management']
PADDING = CONFIG['default']['padding']
try:
    PROCESSING_METHOD = UserConfig().d['methodology']
except AttributeError:
    PROCESSING_METHOD = 'local'
EXT_MAP = CONFIG['ext_map']
ROOT = CONFIG['paths']['root']
SEQ_RULES = CONFIG['rules']['general']['file_sequence']['regex']
SEQ_REGEX = re.compile("[0-9]{4,}\\.")
SPLIT_SEQ_REGEX = re.compile(" \d{3,}-\d{3,}$")
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
        self.root = CONFIG['paths']['root'].replace('\\', '/')
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
        self.assetname = None
        self.task = None
        self.camera = None
        self.aov = None
        self.file_type = None
        self.frame_padding = CONFIG['default']['padding']
        self.scope_list = CONFIG['rules']['scope_list']
        self.context_list = CONFIG['rules']['context_list']
        self.path = None  # string of the properly formatted path
        self.path_root = None  # this gives the full path with the root
        self.thumb_path = None
        self.preview_path = None
        self.preview_file = None
        self.preview_seq = None
        self.hd_proxy_path = None
        self.start_frame = None
        self.end_frame = None
        self.frame_rate = None
        self.frame_range = None
        self.template = []
        self.filename_template = []
        self.actual_resolution = None
        self.date_created = None
        self.date_modified = None
        self.project_config = None
        self.company_config = None
        self.software_config = None
        self.asset_json = None
        self.shot_json = None
        self.task_json = None
        self.command_base = ''
        self.project_json = None
        self.status = None
        self.due = None
        self.assigned = None
        self.priority = None
        self.ingest_source = '*'
        self.processing_method = PROCESSING_METHOD
        self.publish_source = None
        self.publish_render = None
        self.parts_length = 0
        self.template_type = 'version'
        self.path_template = []
        self.version_template = []
        # TODO python 3 doesn't like unicode
        try:
            if isinstance(path_object, unicode):
                path_object = str(path_object)
        except NameError:
            pass
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
        # self.set_json()

    def process_dict(self, path_object):
        self.set_attrs_from_dict(path_object)
        self.set_path()
        self.set_project_config()
        self.set_preview_path()
        # self.set_json()

    @staticmethod
    def get_attrs_from_config():
        attrs = []
        for key in CONFIG['rules']['path_variables']:
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
            elif t in CONFIG['rules']['scope_list']:
                current_ = 'scope'
        return current_

    def get_version_template(self):
        if self.scope and self.context and self.user:
            self.version_template = []
            version = 'version_%s' % self.task
            if version in CONFIG['templates'][self.scope][self.context].keys():
                version_template = CONFIG['templates'][self.scope][self.context][version].split('/')
            else:
                version_template = CONFIG['templates'][self.scope][self.context]['version'].split('/')
            self.version_template = self.clean_template(version_template)
        elif self.scope == "IO":
            version_template = CONFIG['templates'][self.scope]['source']['version'].split('/')
            self.version_template = self.clean_template(version_template)
        else:
            self.version_template = []
        # self.template = self.template + self.version_template

    def clean_template(self, template):
        clean_template = []
        for each in template:
            each = each.replace('{', '').replace('}', '')
            if each == 'filename.ext':
                each = 'filename'
            clean_template.append(each)
        return clean_template

    def get_path_template(self):
        self.path_template = []
        if self.context:
            if self.scope:
                if self.scope == '*':
                    self.path_template = ['company', 'context', 'project', 'scope']
                    return
                path_template = CONFIG['templates'][self.scope][self.context]['path'].split('/')
                self.path_template = self.clean_template(path_template)
                return
            else:
                self.path_template = ['company', 'context', 'project', 'scope']
        else:
            self.path_template = ['company']

    def get_template(self):
        self.get_path_template()
        self.get_version_template()
        self.template = self.path_template + self.version_template

    def set_scope_list(self):
        self.scope_list = CONFIG['rules']['scope_list']

    def set_context_list(self):
        self.context_list = CONFIG['rules']['context_list']
        for key in CONFIG['templates']:
            if key not in self.context_list:
                self.context_list.append(key)
                for scope in CONFIG['templates'][key]:
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
            self.set_attr(company=c, do_set_path=False)
        except IndexError:
            self.set_attr(company='*', do_set_path=False)

    def unpack_version(self, path_parts):
        """
        unpacks the "version" part of the path.
        :param path_string:
        :return:
        """
        self.get_version_template()
        for i, attr in enumerate(self.version_template):
            if attr:
                try:
                    self.set_attr(attr=attr, value=path_parts[i], do_set_path=False)
                except IndexError:
                    pass
        pass

    def get_template_old(self):
        self.template = []
        if self.context:
            if self.scope:
                if self.scope == '*':
                    self.template = ['company', 'context', 'project', 'scope']
                    return
                try:
                    path_template = CONFIG['templates'][self.scope][self.context]['path'].split('/')
                    if path_template[-1] == '':
                        path_template.pop(-1)
                    version_template = CONFIG['templates'][self.scope][self.context]['version'].split('/')
                    template = path_template + version_template
                    for each in template:
                        each = each.replace('{', '').replace('}', '')
                        if each == 'filename.ext':
                            each = 'filename'
                        self.template.append(each)
                    return self.template
                except KeyError:
                    logging.debug("Config ERROR: Can't find either %s or %s within app config 'templates'"
                                 % (self.scope, self.context))
                    return
            else:
                self.template = ['company', 'context', 'project', 'scope']
        else:
            self.template = ['company']

    def unpack_path(self, path_string):
        """
        parse a path_string and unpack it into the various values within a pathObject.
        :param path_string: string value representing a path.
        :return:
        """
        path_string = os.path.normpath(path_string.split(self.company)[-1])
        path_ = os.path.normpath(path_string)
        path_parts = path_.split(os.sep)
        if path_parts[0] == '':
            path_parts.pop(0)
        path_parts.insert(0, self.company)
        self.set_attr(context=path_parts[1].lower(), do_set_path=False)
        if len(path_parts) > 3:
            self.set_attr(scope=path_parts[3].lower(), do_set_path=False)
        split_at = -1
        self.get_path_template()
        self.data = {}
        for i, attr in enumerate(self.path_template):
            if attr:
                attr = attr.replace('{', '').replace('}', '')
                try:
                    if attr == self.context:
                        pass
                    elif attr == self.scope:
                        pass
                    elif attr == 'filename':
                        self.set_attr(filename=path_parts[i], do_set_path=False)
                        filename_base, ext = os.path.splitext(path_parts[i])
                        self.set_attr(filename_base=filename_base, do_set_path=False)
                        self.set_attr(ext=ext.replace('.', ''), do_set_path=False)
                    else:
                        self.set_attr(attr=attr, value=path_parts[i], do_set_path=False)
                        if attr == 'user':
                            split_at = i
                except IndexError:
                    pass
        if not self.seq:
            self.set_attr(seq=self.type, do_set_path=False)
        if not self.shot:
            self.set_attr(shot=self.asset, do_set_path=False)
        if not self.asset:
            self.set_attr(asset=self.shot, do_set_path=False)
        if not self.type:
            self.set_attr(type=self.seq, do_set_path=False)
        if self.user:
            del path_parts[0:split_at+1]
            self.unpack_version(path_parts)
        if self.version:
            major_version, minor_version = self.version.split('.')
            self.set_attr(major_version=major_version.replace('.', ''), do_set_path=False)
            self.set_attr(minor_version=minor_version.replace('.', ''), do_set_path=False)
        self.set_shotname()
        self.set_path()

    def set_path(self):
        """
        set's self.path_root, self.path, self.filename, self.command_base, self.hd_proxy_path, self.thumb_path, and
        self.preview_path
        :return:
        """
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
        if path_string.endswith('.'):
            path_string = path_string[:-1]
        if sys.platform == 'win32':
            self.path_root = '%s/%s' % (self.root, path_string)
        else:
            self.path_root = os.path.join(self.root, path_string).replace('\\', '/')
        self.path = path_string
        self.set_command_base()
        if self.filename:
            if self.filename != '*':
                self.set_file_type()
                # TODO - probably can get rid of all the if not statements
                self.set_hd_proxy_path()
                self.set_preview_path()
                self.set_thumb_path()
        return self.path

    def set_attr(self, attr=None, value=None, do_set_path=True, **kwargs):
        """
        sets attribute on the path object.  You can use "attr"/"value" or simply put attr=value into the function
        :param attr: attribute name
        :param do_set_path: True if you want to set the path and path_root after setting attr.
        :param value: value for corresponding attribute name
        :param kwargs: expecting any number of key value pairs.
        :return:
        """
        if attr:
            kwargs[attr] = value
        for attr in kwargs:
            value = kwargs[attr]
            try:
                CONFIG['rules']['path_variables'][attr]['regex']
            except KeyError:
                logging.debug('Could not find regex for %s: %s in config, skipping' % (attr, value))
                return
            if value == '*':
                self.__dict__[attr] = value
                self.data[attr] = value
                # self.set_path()
            else:
                if attr == 'scope':
                    if value:
                        if value in self.scope_list:
                            self.__dict__[attr] = value
                            self.data[attr] = value
                            # self.set_path()
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
                            # self.set_path()
                else:
                    self.__dict__[attr] = value
                    self.data[attr] = value
                    # self.set_path()
            if attr == 'shot':
                self.__dict__['asset'] = value
                self.data['asset'] = value
                # self.set_path()
            elif attr == 'asset':
                self.__dict__['shot'] = value
                self.data['shot'] = value
                # self.set_path()
            elif attr == 'seq':
                self.__dict__['type'] = value
                self.data['type'] = value
                # self.set_path()
            elif attr == 'type':
                self.__dict__['seq'] = value
                self.data['seq'] = value
                # self.set_path()
            elif attr == 'filename':
                if value:
                    self.__dict__['filename'] = value
                    self.data['filename'] = value
                    base, ext = os.path.splitext(value)
                    self.__dict__['ext'] = ext.replace('.', '')
                    self.data['ext'] = ext.replace('.', '')
                    self.__dict__['filename_base'] = base
                    self.data['filename_base'] = base
                    # self.set_path()
            elif attr == 'ext':
                if self.ext:
                    if self.filename:
                        base, ext = os.path.splitext(self.filename)
                        self.filename = '%s.%s' % (base, self.ext)
                        # self.set_path()
            elif attr == 'version':
                if value:
                    if value != '*' and value != '.':
                        major, minor = value.split('.')
                    else:
                        major = '000'
                        minor = '000'
                    self.__dict__['major_version'] = major
                    self.data['major_version'] = major
                    self.__dict__['minor_version'] = minor
                    self.data['minor_version'] = minor
                    # self.set_path()
        if do_set_path:
            self.set_path()
            # logging.debug('setting path for kwargs: %s' % kwargs)

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
        try:
            index = self.template.index(attr)
        except ValueError:
            logging.debug('%s not found in template, skipping')
            return []
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

            return clean_file_list(list_)
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
        split_after_thing = os.path.join(self.path_root.split(value)[0], value)
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
        elif new_obj.scope == 'IO':
            latest_version = new_obj.glob_project_element('version')
            if latest_version:
                new_obj.set_attr(version=latest_version[-1])
                return new_obj
            else:
                new_obj.set_attr(version='000.000')
        return new_obj

    def next_minor_version_number(self):
        """
        versions up the minor version part of the version number.
        :return:
        """

        latest_version = self.latest_version()
        major = latest_version.major_version
        minor = latest_version.minor_version
        if self.minor_version >= minor:
            minor = self.minor_version
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
        pub_major = self.latest_version(publish_=True).major_version
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
        """
        returns a new minor version object.
        :return:
        """
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
        sequence = Sequence(self.path_root)
        if sequence.is_valid_sequence():
            self.filename = os.path.basename(sequence.hash_sequence)
            self.frame_range = sequence.frame_range
            self.__dict__['file_type'] = 'sequence'
            self.file_type = 'sequence'
            return
        _, file_ext = os.path.splitext(self.path)
        try:
            _type = EXT_MAP[file_ext.lower()]
            if _type:
                if _type == 'movie':
                    self.__dict__['file_type'] = 'movie'
                    self.data['file_type'] = 'movie'
                elif _type == 'image':
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

    def set_hd_proxy_path(self):
        """
        sets the hd_proxy_path variable to a standard location
        :return:
        """
        if self.path_root and self.resolution:
            resolution = CONFIG['default']['resolution']['video_review']
            name_ = os.path.splitext(self.filename)[0]
            filename = '%s.jpg' % name_
            dir_ = os.path.dirname(self.path_root.replace(self.resolution, resolution))
            self.hd_proxy_path = os.path.join(dir_, filename)
            self.data['hd_proxy_path'] = self.hd_proxy_path

    def set_thumb_path(self):
        if sys.platform == 'win32':
            p_path = os.path.splitext(self.preview_path)[0]
            self.thumb_path = '%s%s' % (p_path.replace('.preview', '.thumb'), '.jpg')
            self.data['thumb_path'] = self.thumb_path

    def set_preview_path(self):
        """
        sets the .preview_path variable to a standard location
        :return:
        """
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
        if self.filename:
            if '#' in self.filename:
                name_ = self.filename.split('#')[0]
                if name_.endswith('.'):
                    name_ = name_[:-1]
                    # ext.replace('.', '')
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
                self.preview_path = '%s/%s/%s' % (path_, '.preview', name_)
                self.preview_seq = self.preview_path.replace(ext, '.####%s' % ext)
                self.data['preview_path'] = self.preview_path
                self.set_thumb_path()
            else:
                self.preview_path = os.path.join(self.root, '.preview', name_)
                self.preview_seq = self.preview_path.replace(ext, '.####%s' % ext)
                self.set_thumb_path()
                self.data['preview_path'] = self.preview_path

    def set_proper_filename(self):
        """
        function that sets filename according to patterns in globals.
        :return:
        """
        # TODO - this needs to be basted off formulas like the path object.  Curses.
        self.filename_base = '%s_%s_%s' % (self.seq, self.shot, self.task)
        if self.ext:
            self.filename = '%s.%s' % (self.filename_base, self.ext)
        self.set_path()

    def set_shotname(self):
        """
        sets shot name and asset name if seq is 010 and shot is 0100 shot name is 010_0100
        :return:
        """
        self.set_attr(shotname='%s_%s' % (self.seq, self.shot), do_set_path=False)
        self.set_attr(assetname='%s_%s' % (self.seq, self.shot), do_set_path=False)

    def set_project_config(self):
        """
        sets the .company_config and .project_config values
        :return:
        """
        self.company_config = os.path.join(CONFIG['account_info']['globals_path'], 'globals.json')
        self.project_config = os.path.join(CONFIG['account_info']['globals_path'], 'globals.json')

    def set_json(self):
        json_obj = self.copy(latest=True, context='render', ext='json', task='lay', set_proper_filename=True)
        if self.asset or self.shot:
            self.asset_json = json_obj.path_root
            self.shot_json = json_obj.path_root
        if self.task:
            json_obj = self.copy(context='render', ext='json', set_proper_filename=True)
            self.task_json = json_obj.path_root
        if self.project:
            proj_name = json_obj.data['project']
            self.project_json = os.path.join(json_obj.path_root.split(proj_name)[0], proj_name, '%s.json' % proj_name)

    def set_command_base(self):
        """
        sets a base string for command_names for the render farm.   seq_shot_task is the default.
        :return:
        """
        self.command_base = '%s_%s_%s' % (self.seq, self.shot, self.task)

    def upload_review(self, job_id=None, processing_method='local'):
        """
        uploads a review file to project management/review software as defined in globals.  where review file
        is not present it attempts to make one.
        :param job_id: job_id for dependencies on the farm.  Essentially if a job_id is present this is sent to the farm
        :return:
        """
        if job_id:
            pyfile = '%s.py' % os.path.splitext(__file__)[0]
            command = r'python %s -p %s -r True' % (pyfile, self.path_root)
            process_info = cgl_execute(command, command_name='%s: upload_review()' % self.command_base,
                                       methodology=processing_method, WaitForJobID=job_id)
            return process_info
        else:
            if os.path.exists(self.preview_path):
                if PROJ_MANAGEMENT == 'ftrack':
                    prod_data = CreateProductionData(path_object=self)
                    print(333)
                    return True
                elif PROJ_MANAGEMENT == 'lumbermill':
                    logging.debug('no review process defined for default lumbermill')
            else:
                logging.debug('No preview file found for uploading: %s' % self.preview_path)
                info = self.make_preview()
                self.upload_review(job_id=info['job_id'], processing_method=processing_method)
                return False

    def make_thumbnail(self, job_id=None, new_window=False, type_='movie'):
        #TODO make this smart enough to know based off the self.thumb_path
        if os.path.exists(self.preview_path):
            if type_ == 'movie':
                logging.debug('Creating Thumbnail %s' % self.thumb_path)
                thumb_info = convert.create_movie_thumb(self.preview_path, self.thumb_path,
                                                        command_name='%s: create_movie_thumb()' % self.command_base,
                                                        dependent_job=job_id,
                                                        processing_method=PROCESSING_METHOD, new_window=new_window)
                return thumb_info

    def make_preview(self, job_id=None, new_window=False):
        """
        Creates web optimized preview of PathObject.  For movies and image sequences it's a 1920x1080 quicktime h264,
        for images it's a jpeg within the boundaries of 1920x1080
        :return:
        """
        # Check for self.hd_proxy_path

        if self.file_type == 'sequence':
            # make sure that an hd_proxy exists:
            review_res = CONFIG['default']['resolution']['video_review']
            # proxy_info = self.make_proxy(resolution=review_res, ext='jpg', job_id=job_id)
            if hd_proxy_exists(self.hd_proxy_path, self.frame_range):
                #logging.debug(proxy_info)
                #logging.debug('proxy id %s' % proxy_info['job_id'])
                mov_info = convert.create_web_mov(self.hd_proxy_path, self.preview_path,
                                                  command_name='%s: create_web_mov()' % self.command_base,
                                                  dependent_job=None, processing_method=PROCESSING_METHOD,
                                                  new_window=new_window)
                logging.debug('mov info id %s' % mov_info['job_id'])
                logging.debug('Creating Thumbnail %s' % self.thumb_path)
                thumb_info = convert.create_movie_thumb(self.preview_path, self.thumb_path,
                                                        command_name='%s: create_movie_thumb()' % self.command_base,
                                                        dependent_job=mov_info['job_id'],
                                                        processing_method=PROCESSING_METHOD, new_window=new_window)
                return thumb_info
        elif self.file_type == 'movie':
            print('I will be able to create a movie preview soon.')
            print(PROCESSING_METHOD)
            mov_info = convert.create_web_mov(self.path_root, self.preview_path,
                                              command_name='%s: create_web_mov()' % self.command_base,
                                              dependent_job=None, processing_method=PROCESSING_METHOD,
                                              new_window=new_window)
            # logging.debug('mov info id %s' % mov_info['job_id'])
            # logging.debug('Creating Thumbnail %s' % self.thumb_path)
            # thumb_info = convert.create_movie_thumb(self.preview_path, self.thumb_path,
            #                                         command_name='%s: create_movie_thumb()' % self.command_base,
            #                                         dependent_job=mov_info['job_id'],
            #                                         processing_method=PROCESSING_METHOD, new_window=new_window)
            return mov_info
        elif self.file_type == 'image':
            logging.debug('making image preview not supported')
        elif self.file_type == 'ppt':
            logging.debug('making ppt preview not supported')
        elif self.file_type == 'pdf':
            logging.debug('making pdf preview not supported')

    def make_proxy(self, resolution=None, copy_input_padding=True, ext='jpg', new_window=False, job_id=None):
        """
        :param resolution: HEIGHTxWIDTH ex: (1920x1080)
        :param copy_input_padding: if True use padding from input sequence, if False use padding from Globals
        :param ext: extension for the proxy file.  Default is jpg
        :param new_window: start process in a new command window
        :param job_id: job_id of dependent job.
        :return:
        """

        if resolution:
            width, height = resolution.split('x')
        else:
            if self.project.lower() in CONFIG['default']['proxy_resolution'].keys():
                proxy_resolution = CONFIG['default']['proxy_resolution'][self.project.lower()]
            else:
                proxy_resolution = CONFIG['default']['proxy_resolution']['default']
            width, height = proxy_resolution.split('x')
        name_ = os.path.splitext(self.filename)[0]
        filename = '%s.%s' % (name_, ext)
        dir_ = os.path.dirname(self.path_root.replace(self.resolution, '%sx%s' % (width, height)))
        output_sequence = os.path.join(dir_, filename)
        self.hd_proxy_path = output_sequence
        proc_meth = PROCESSING_METHOD
        if job_id:
            proc_meth = 'smedge'
        proxy_info = convert.create_proxy_sequence(self.path_root, output_sequence=output_sequence, width=width,
                                                   height=height, copy_input_padding=copy_input_padding,
                                                   processing_method=proc_meth, dependent_job=job_id,
                                                   new_window=new_window,
                                                   command_name='%s: create_proxy_sequence()' % self.command_base)
        return proxy_info

    def publish(self):
        """
        This will create a publish version from the current pathObject.   Essentially that means:
        we will create the next major version for this user and copy all elements into the new version
        we will create a "publish" version of it as well to
        :param source:
        :param render:
        :return:
        """
        if self.user == 'publish':
            logging.debug("This is a publish user already, traditionally you'll be publishing from a user context.")
            return
        if not self.resolution:
            logging.debug('You must have resolution in order to publish')
            return

        # current folders to be copied
        current_source = self.copy(context='source', filename=None, ext=None).path_root
        current_render = self.copy(context='render', filename=None, ext=None).path_root
        # create the next major version folders to copy to
        next_major = self.copy(context='source', filename=None, ext=None)
        next_major = next_major.next_major_version()
        next_major_render = next_major.copy(context='render').path_root
        next_major_source = next_major.path_root
        publish = next_major.copy(user='publish')
        publish_source = publish.path_root
        self.publish_source = publish_source
        publish_render_object = publish.copy(context='render')
        publish_render = publish_render_object.path_root
        self.publish_render = publish_render
        logging.debug('Publishing %s to %s' % (current_source, next_major_source))
        cgl_copy(current_source, next_major_source)
        logging.debug('Publishing %s to %s' % (current_source, publish_source))
        cgl_copy(current_source, publish_source)
        logging.debug('Publishing %s to %s' % (current_render, next_major_render))
        cgl_copy(current_render, next_major_render)
        logging.debug('Publishing %s to %s' % (current_render, publish_render))
        cgl_copy(current_render, publish_render)
        logging.debug('--------- Finished Publishing')
        return publish_render_object
        # if UserConfig().d["sync_thing_machine_type"] == 'remote workstation':
        #     from cgl.ui.widgets.sync_master import SharingDialog
        #     dialog_sharing = SharingDialog([publish, publish_render_object])
        #     dialog_sharing.exec_()
        #     if dialog_sharing.button == 'Ok':
        #         all_device_id = dialog_sharing.device_list
        #         logging.debug('Sharing Folders to: %s' % all_device_id)
        #         logging.debug(publish.path_root)
        #         logging.debug(publish_render_object.path_root)
        #         return publish_render_object
        #     else:
        #         logging.debug('skipping remote publish')
        #         return publish_render_object
        # else:


    def show_in_folder(self):
        """
        open the folder location of the current path_object
        :return:
        """
        show_in_folder(self.path_root)

    def show_web_page(self):
        """
        assuming project management is set - it shows the web page for the current path_object in that tool.
        :return:
        """
        show_in_project_management(self)

    def open(self):
        """
        opens the path_root with default application
        :return:
        """
        start(self.path_root)

    def copy_path(self):
        """
        copies the full path to the clipboard
        :return:
        """
        pyperclip.copy(str(self.path_root))
        # pyperclip.paste()

    def copy_folder(self):
        """
        copies the directory path to the clipboard
        :return:
        """
        pyperclip.copy(str(os.path.dirname(self.path_root)))


class CreateProductionData(object):
    def __init__(self, path_object=None, file_system=True,
                 project_management=PROJ_MANAGEMENT,
                 user_login=None,
                 do_scope=False, test=False, json=False, create_default_file=False,
                 force_pm_creation=False,
                 session=None,
                 status=None):
        self.session = session
        self.force_pm_creation = force_pm_creation
        self.user_login = user_login
        self.test = test
        self.path_object = PathObject(path_object)
        self.path_object.set_path()
        self.path_object.set_json()
        self.do_scope = do_scope
        if file_system:
            self.create_folders()
        if project_management:
            logging.debug('Creating Production Management Data for %s: %s' % (project_management,
                                                                              self.path_object.data))
            self.create_project_management_data(self.path_object, project_management, self.user_login, status)
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
        from cgl.core import assetcore

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
        from cgl.core import assetcore

        obj = self.path_object
        if os.path.exists(obj.asset_json):
            logging.debug(obj.asset_json, 'exists')
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
        from cgl.core import assetcore
        logging.debug('updating project json')
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
            logging.debug('No Root Defined')
            return
        if not self.path_object.company:
            logging.debug('No Company Defined')
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
            for each in CONFIG['rules']['scope_list']:
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
            # does it have a 3-4 digit extension?
            if path_object.ext:
                path_ = os.path.dirname(path_)
            if path_.endswith('.'):
                path_ = path_[:-1]
        # at this stage we're making path_
        logging.debug('Creating %s Directory: %s' % (path_object.context, path_))
        if not test:
            if not os.path.exists(path_):
                os.makedirs(path_)
        else:
            logging.debug('TEST MODE: No directories were created')

    def create_project_management_data(self, path_object, project_management, user_login=None, status=None):

        if project_management != 'lumbermill':
            if path_object.filename or self.force_pm_creation:
                session = None
                if self.session:
                    session = self.session
                module = "cgl.plugins.project_management.%s.main" % project_management
                # noinspection PyTypeChecker
                try:
                    loaded_module = __import__(module, globals(), locals(), 'main', -1)  # Python 2.7 way of doing this
                except ValueError:
                    loaded_module = importlib.import_module(module, 'main')
                loaded_module.ProjectManagementData(path_object,
                                                    session=session,
                                                    user_email=user_login,
                                                    status=status).create_project_management_data()
            else:
                logging.debug('Creating Paths on Disk, lumbermill will create %s '
                      'versions when you add files' % project_management)
        else:
            logging.debug('Using Lumbermill built in proj management')

    def create_default_file(self):
        if self.path_object.task == 'prev':
            self.copy_default_file('blender', 'blend')
        if self.path_object.task == 'lay':
            self.copy_default_file('blender', 'blend')
        if self.path_object.task == 'anim':
            self.copy_default_file('blender', 'blend')
        if self.path_object.task == 'mdl':
            self.copy_default_file('blender', 'blend')
        if self.path_object.task == 'shd':
            self.copy_default_file('blender', 'blend')
        if self.path_object.task == 'anim':
            self.copy_default_file('blender', 'blend')
        if self.path_object.task == 'lite':
            self.copy_default_file('blender', 'blend')
        if self.path_object.task == 'comp':
            self.copy_default_file('nuke', 'nk')
        if self.path_object.task == 'key':
            self.copy_default_file('nuke', 'nk')
        if self.path_object.task == 'dnoise':
            self.copy_default_file('nuke', 'nk')
        if self.path_object.task == 'noise':
            self.copy_default_file('nuke', 'nk')

    def copy_default_file(self, software, ext):
        self.path_object.set_attr(filename='%s_%s_%s.%s' % (self.path_object.seq,
                                                            self.path_object.shot,
                                                            self.path_object.task,
                                                            ext))
        this = __file__.split('cglumberjack')[0]
        this = this.replace('\\', '/')
        this = '%scglumberjack/cgl' % this
        default_file = "%s/plugins/%s/templates/default.%s" % (this, software, ext)
        logging.debug('Creating Default %s file: %s' % (self.path_object.task, self.path_object.path_root))
        cgl_copy(default_file, self.path_object.path_root, methodology='local')


class Sequence(object):
    """
    Class for dealing with "Sequences" of images or files in general as defined within a vfx/animation/games pipeline
    """
    sequence = None
    frame_range = None
    start_frame = None
    end_frame = None
    middle_frame = None
    hash_sequence = None
    num_sequence = None
    star_sequence = None
    padding = None
    ext = None
    num = None
    hash = None

    def __init__(self, sequence, padding=PADDING, verbose=False):
        self.sequence = sequence
        self.verbose = verbose
        if not self.is_valid_sequence():
            return
        self.padding = padding
        self.set_frange()
        self.set_sequence_strings()
        # self.print_info()

    def is_valid_sequence(self):
        """
        Checks "sequence" to ensure it matches our definition of a sequence:
        sequence.####.ext, sequence.%04d.ext, sequence.*.ext
        :return: boolean
        """
        self.set_ext()
        valid = False
        if not self.sequence:
            return False
        if self.sequence.endswith('#%s' % self.ext):
            valid = True
        elif '%' in self.sequence:
            valid = True
        elif self.sequence.endswith('*%s' % self.ext):
            valid = True
        if not valid and self.verbose:
            logging.error('%s is not a valid sequence' % self.sequence)
        return valid

    def set_ext(self):
        """
        sets the ext value for the sequence
        :return:
        """
        _, self.ext = os.path.splitext(self.sequence)

    def print_info(self):
        logging.debug('---------------- sequence info -------------------')
        logging.debug('Star: %s' % self.star_sequence)
        logging.debug('Hash: %s' % self.hash_sequence)
        logging.debug('Num: %s' % self.num_sequence)
        logging.debug('Frame Range: %s' % self.frame_range)
        logging.debug('Start Frame: %s' % self.start_frame)
        logging.debug('End Frame: %s' % self.end_frame)
        logging.debug('Middle Frame: %s' % self.middle_frame)

    def set_sequence_strings(self):
        """
        THis is a utility function for setting all the various string formats we need for sequences depending
        on the software we happen to be working in:
        ####.exr - hash_sequence
        %04d.exr - num_sequence
        *.exr - star_sequence
        :return:
        """
        seq_base = self.split_sequence()
        self.star_sequence = '%s*%s' % (seq_base, self.ext)
        self.num_sequence = '%s%s%s' % (seq_base, self.num, self.ext)
        self.hash_sequence = '%s%s%s' % (seq_base, self.hash, self.ext)

    def split_sequence(self):
        """
        We split the sequence at the delimeter ('*', '%0Nd', or '###') and return the first value.
        Examples:
        sequence.####.exr returns - sequence.
        sequence.%04d.exr returns - sequence.
        sequence.*.exr returns - sequence.
        :return:
        """
        frange = None
        group = None
        if self.sequence.endswith('#%s' % self.ext):
            frange = re.search(SEQ_SPLIT, self.sequence)
            group = frange.group(0)
        elif '%' in self.sequence:
            frange = re.search(SEQ2_SPLIT, self.sequence)
            group = frange.group(0)
        elif self.sequence.endswith('*%s' % self.ext):
            frange = True
            group = '*.'
        if frange:
            return self.sequence.split(group)[0]
        else:
            return

    def set_frange(self):
        """
        sets all information regarding frame range for the sequence
        start_frame, end_frame, middle_frame, frame_range are all set by this function
        :return:
        """
        seq_match = r'\s[\d]+-[\d]+$'
        regex = re.compile(r'\s[\d]+-[\d]+$')
        current_sel = self.sequence
        frange = re.search(regex, current_sel)
        if frange:
            sframe, eframe = frange[0].split('-')
        else:
            # This requires the # form of the sequence
            glob_string = ''
            if '#' in self.sequence:
                glob_string = '%s*%s' % (self.sequence.split('#')[0], self.ext)
            elif '%' in self.sequence:
                glob_string = '%s*%s' % (self.sequence.split('%')[0], self.ext)
            elif '*' in self.sequence:
                glob_string = self.sequence
            frames = glob.glob(glob_string)
            if frames:
                try:
                    sframe = re.search(SEQ_REGEX, frames[0]).group(0).replace('.', '')
                    eframe = re.search(SEQ_REGEX, frames[-1]).group(0).replace('.', '')
                except AttributeError:
                    logging.error('problem with filepath: %s and frames: '
                                  '%s in get_frange_from_seq, skipping.' % (self.sequence, frames))
            else:
                self.start_frame = CONFIG['default']['start_frame']
                self.hash = '#' * self.padding
                if self.padding < 10:
                    self.num = '%0' + str(self.padding) + 'd'
                else:
                    self.num = '%' + str(self.padding) + 'd'
                return
        if sframe and eframe:
            self.frame_range = '%s-%s' % (sframe, eframe)
            self.start_frame = sframe
            self.end_frame = eframe
            self.padding = len(self.start_frame)
            self.hash = '#'*self.padding
            if self.padding < 10:
                self.num = '%0'+str(self.padding)+'d'
            else:
                self.num = '%'+str(self.padding)+'d'
            mid_frame = int((int(eframe) - int(sframe)) / 2) + int(sframe)
            self.middle_frame = self.int_as_padded_frame(mid_frame, self.padding)



    @staticmethod
    def int_as_padded_frame(number, padding=None):
        """
        given number, return a string with padding of padding:
        example, given 3 return string with padding of 4 = 0003
        :param number: int
        :param padding: int (number of the string padding)
        :return:
        """
        if padding == 2:
            return '%02d' % number
        elif padding == 3:
            return '%03d' % number
        elif padding == 4:
            return '%04d' % number
        elif padding == 5:
            return '%05d' % number
        elif padding == 6:
            return '%06d' % number
        elif padding == 7:
            return '%07d' % number
        elif padding == 8:
            return '%08d' % number
        elif padding == 9:
            return '%09d' % number
        elif padding == 10:
            return '%10d' % number
        elif padding == 11:
            return '%11d' % number


def get_resources_path():
    """
    get the resources path
    :return: path string
    """
    return os.path.join(CONFIG['paths']['code_root'], 'resources')


def image_path(image=None):
    """
    get the path where images are stored
    :param image:
    :return:
    """
    if image:
        return os.path.join(CONFIG['paths']['code_root'], 'resources', 'images', image)
    else:
        return os.path.join(CONFIG['paths']['code_root'], 'resources', 'images')


def icon_path(icon=None):
    """
    get the path where icons are stored.
    :param icon:
    :return:
    """
    if icon:
        return os.path.join(CONFIG['paths']['code_root'], 'resources', 'icons', icon)
    else:
        return os.path.join(CONFIG['paths']['code_root'], 'resources', 'icons')


def font_path():
    """
    get the path where fonts for the app are stored
    :return:
    """
    return os.path.join(CONFIG['paths']['code_root'], 'resources', 'fonts')


def start(filepath):
    """
    opens a file on any os
    :param filepath:
    :return:
    """
    try:
        path_object = PathObject(filepath)
        if path_object.task.lower() == 'paperedit':
            from robogary.src.apps.robo_gary import main
            dialog = main.RoboGary(transcript_file=filepath)
            dialog.exec_()
            return
        if path_object.task.lower() == 'template':
            import cgl.plugins.premiere.premiere_tools as pt
            reload(pt)
            dir_ = os.path.dirname(path_object.path_root)
            pt.launch_fcp_xml(folder_path=dir_, file=path_object.filename)
            return
    except AttributeError:
        pass
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
    # this command will only ever be run locally, it does not need render farm support
    cgl_execute(command, methodology='local')


# TODO - this seems more like a "utils" than a "Path"
def start_url(url):
    import webbrowser
    webbrowser.open(url)


def replace_illegal_filename_characters(filename):
    return re.sub(r'[^A-Za-z0-9\.#]+', '_', filename)


def get_folder_size(folder):
    """
    returns size of the given folder, including all children.
    :return:
    """
    total_bytes = 0
    if os.path.isdir(folder):
        for root, dirs, files in os.walk(folder):
            try:
                total_bytes += sum(os.path.getsize(os.path.join(root, name).replace('\\', '/')) for name in files)
            except:
                logging.debug('ERROR: likely a problem with a file in %s' % root)
    elif os.path.isfile(folder):
        logging.debug('this is a file numskull')
        return 0
    return total_bytes


def print_file_size(total_bytes, do_print=True):
    total_mb = float(total_bytes) / 1024 / 1024
    # total_gb = total_mb / 1024
    size_string = '%s Mb(%s bytes)' % (format(total_mb, ".2f"), '{:,}'.format(total_bytes))
    if do_print:
        logging.debug(size_string)
    return size_string


def find_latest_publish_objects(folder, source=True, render=False):
    """
    returns all the latest published versions of the "folder"
    :param folder:
    :return:
    """
    path_object = PathObject(folder)
    path_object.set_attr(task='*', user='publish')
    folders = glob.glob(path_object.path_root)
    total_size = 0
    sync_objects = []
    for each in folders:
        f_object = PathObject(each)
        # TODO - latest version should work without providing a base version.
        f_object.set_attr(version='000.000')
        if source:
            f_object.set_attr(version='000.000', context='source')
            l_object = f_object.copy(latest=True)
            sync_objects.append(l_object)
            size = get_folder_size(l_object.path_root)
            total_size += size
        if render:
            f_object.set_attr(version='000.000', context='render')
            l_object = f_object.copy(latest=True)
            sync_objects.append(l_object)
            size = get_folder_size(l_object.path_root)
            total_size += size
    logging.debug('%s %s Total Size of Latest Publishes\n\t%s' % (path_object.seq, path_object.shot,
                                                          print_file_size(total_size, do_print=False)))
    return sync_objects


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
    logging.debug("running command: %s" % command)
    # this command will only ever be run locally, it does not need render management support
    cgl_execute(command, methodology='local')


def show_in_project_management(path_object):
    """
    This shows the url of the path_object in the chose project management software.
    :param path_object:
    :return:
    """
    if PROJ_MANAGEMENT != 'lumbermill':
        module = "plugins.project_management.%s.main" % PROJ_MANAGEMENT
        # noinspection PyTypeChecker
        try:
            loaded_module = __import__(module, globals(), locals(), 'main', -1)
        except ValueError:
            import importlib
            # Python 3.0
            loaded_module = importlib.import_module(module, 'main')
        start_url(loaded_module.ProjectManagementData(path_object).get_url())


def seq_from_file(basename):
    """
    checks to see if a filename can be displayed as a hash_sequence
    :param basename:
    :return:
    """
    numbers = re.search(SEQ_REGEX, basename)
    name_, ext_ = os.path.splitext(basename)
    if ext_ in EXT_MAP.keys():
        if EXT_MAP[ext_] == 'image':
            if numbers:
                numbers = numbers.group(0).replace('.', '')
                string = '#' * int(len(numbers))
                string = '%s.' % string
                this = re.sub(SEQ_REGEX, string, basename)
                return this
            else:
                return basename
        else:
            return basename
    else:
        logging.debug('%s not found in extension map in in globals, please add it' % ext_)
        return basename


def test_string_against_path_rules(variable, string):
    regex = CONFIG['rules']['path_variables'][variable]['regex']
    example = CONFIG['rules']['path_variables'][variable]['example']
    compiled_regex = re.compile(r'%s' % regex)
    if re.match(compiled_regex, string):
        return ''
    else:
        message_string = '%s is not a valid %s: \n\n%s' % (string, variable, example)
        return message_string


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
    list_ = os.listdir(directory)
    if not list_:
        return
    list_ = clean_file_list(list_)
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
            sequence = Sequence(os.path.join(directory, each))
            frange = sequence.frame_range
            if frange:
                index = output_.index(each)
                output_[index] = '%s %s' % (each, frange)
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


def hd_proxy_exists(hd_proxy_path, frame_range):
    print(hd_proxy_path)
    if '#' in hd_proxy_path:
        files = glob.glob('{}*'.format(hd_proxy_path.split('##')[0]))
        if files:
            sframe, eframe = frame_range.split('-')
            length = int(eframe) - int(sframe) + 1
            if len(files) != length:
                print('Full HD Proxy Files not found at: {}, '
                      'Proxy Must Exist before Creating mov'.format(hd_proxy_path))
                return False
            else:
                print("HD Proxy Sequence Found at: {}, Creating Web Preview".format(hd_proxy_path))
                return True
        else:
            print('HD Proxy Path not found at: {}, Proxy Must Exist before Creating mov'.format(hd_proxy_path))
            return False


def get_file_type(filepath):
    ft = 'file'
    if "." not in filepath:
        ft = 'folder'
    if '###' in filepath:
        ft = 'sequence'
    if '%0' in filepath:
        ft = 'sequence'
    return ft


@click.command()
@click.option('--path_string', '-p', help='path string to be passed as a PATH_OBJECT')
@click.option('--upload_review', '-r', default=False, help='uploads review media for given path')
def main(path_string, upload_review):
    if path_string:
        if upload_review:
            path_object = PathObject(path_string)
            print(1)
            path_object.upload_review()
            print(2)
            path_object.go_to_dailies()
            print(3)
    else:
        click.echo('No Path Provided, aborting cgl.core.path command line operation')






