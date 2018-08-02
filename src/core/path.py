# -*- coding: utf-8 -*-
import glob
import logging
import os
import sys
import re
import shutil
import copy
import subprocess
import fnmatch
from string import Formatter

from core.config import app_config
from cglcore.exceptions import LumberJackException
from cglui.widgets.dialog import InputDialog


class PathObject(object):
    """
    Representation of a path on disk
    """

    def __init__(self, path_object=None, **kwargs):
        if not path_object:
            logging.error('No Path Object supplied')
            return
        self.data = {}
        self.root = app_config()['paths']['root']
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
        self.filetype = None
        self.scope_list = app_config()['rules']['scope_list']
        self.context_list = app_config()['rules']['context_list']
        self.path = None  # string of the properly formatted path
        self.path_root = None # this gives the full path with the root
        self.split_point = None  # point at which to split the path when formatting.
        self.template = []

        if type(path_object) is dict:
            self.process_dict(path_object)
        elif type(path_object) is str:
            self.process_string(path_object)
        else:
            logging.error('type: %s not expected' % type(path_object))

    def process_string(self, path_object):
        self.get_company(path_object)
        self.unpack_path(path_object)
        self.set_data_from_attrs()
        # self.set_shotname()

    def process_dict(self, path_object):
        self.set_attrs_from_dict(path_object)
        self.set_path()

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
            setattr(self, key, path_object[key])

    def get_template(self):
        self.template = []
        if self.scope:
            if self.context:
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
                    logging.error("No valid scope (assets/shots) or context (source/render) on pathObject")
                    return
            else:
                self.template = ['company', 'scope', 'project']
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
        companies = app_config()['account_info']['companies']
        for c in companies:
            if c in path_string:
                self.set_attr('company', c)
        if not self.company:
            logging.error("No Valid Company defined in path provided - invalid path: %s" % path_string)
            return

    def unpack_path(self, path_string):
        path_string = os.path.normpath(path_string.split(self.company)[-1])
        path_ = os.path.normpath(path_string)
        path_parts = path_.split(os.sep)
        if path_parts[0] == '':
            path_parts.pop(0)
        path_parts.insert(0, self.company)
        self.set_attr('context', path_parts[1].lower())
        self.set_attr('scope', path_parts[3].lower())

        try:
            path_template = app_config()['templates'][self.scope][self.context]['path'].split('/')
            if path_template[-1] == '':
                path_template.pop(-1)
            version_template = app_config()['templates'][self.scope][self.context]['version'].split('/')
            template = path_template + version_template
        except KeyError:
            logging.error("No valid scope (assets/shots) or context (source/render) - invalid production path: %s" %
                          path_)
            return

        self.data = {}
        for i, attr in enumerate(template):
            if attr:
                attr = attr.replace('{', '').replace('}', '')
                try:
                    if attr == self.context:
                        pass
                    elif attr == self.scope:
                        pass
                    elif attr == 'filename.ext':
                        self.set_attr('filename', path_parts[i])
                        filename_base, ext = os.path.splitext(path_parts[i])
                        self.set_attr('filename_base', filename_base)
                        self.set_attr('ext', ext.replace('.', ''))
                    else:
                        self.set_attr(attr, path_parts[i])
                except IndexError:
                    logging.info(attr, None)
        if not self.seq:
            self.set_attr('seq', self.type)
        if not self.shot:
            self.set_attr('shot', self.asset)
        if not self.asset:
            self.set_attr('asset', self.shot)
        if not self.type:
            self.set_attr('type', self.seq)
        if self.version:
            major_version, minor_version = self.version.split('.')
            self.set_attr('major_version', major_version.replace('.', ''))
            self.set_attr('minor_version', minor_version.replace('.', ''))

    def set_path(self, root=False):
        # TODO: this should set, path, source, and render, and probably give a root option for each one for convenience.
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
        self.path_root = '%s\\%s' % (self.root, path_string)
        self.path = path_string
        if root:
            return self.path_root
        else:
            return self.path

    def set_attr(self, attr, value, regex=True):
        if regex:
            regex = app_config()['rules']['path_variables'][attr]['regex']
        if value == '*':
            self.__dict__[attr] = value
            self.data[attr] = value
        else:
            if value:
                if attr == 'scope':
                    if value not in self.scope_list:
                        logging.error('%s not found in %s' % (value, self.scope_list))
                        return
                    else:
                        self.__dict__[attr] = value
                        self.data[attr] = value
                elif attr == 'context':
                    if value not in self.context_list:
                        logging.error('%s not found in %s' % (value, self.context_list))
                        return
                    else:
                        self.__dict__[attr] = value
                        self.data[attr] = value
                else:
                    if regex:
                        if not re.match(regex, value):
                            logging.error('%s does not follow regex for %s: %s' % (value, attr, regex))
                            return
                    self.__dict__[attr] = value
                    self.data[attr] = value
        if attr == 'shot':
            self.__dict__['asset'] = value
            self.data['asset'] = value
        elif attr == 'asset':
            self.__dict__['shot'] = value
            self.data['shot'] = value
        elif attr == 'seq':
            self.__dict__['type'] = value
            self.data['type'] = value
        elif attr == 'type':
            self.__dict__['seq'] = value
            self.data['seq'] = value
        self.set_path()

    def glob_project_element(self, attr, full_path=False, split=True):
        """
        Simple Glob Function.  "I want to return all "projects"" for instance would be written this way:
        glob_project_element(self, 'project')
        this would return a list of project names.  Use the full_path flag to return a list of paths.
        :param self: self
        :param attr: attribute name: 'project', 'scope', 'version', filename, etc...
        :param full_path: if True returns full paths for everything globbed
        :return: returns list of items, or paths.
        """
        value = self.data[attr]
        glob_path = self.path_root.split(value)[0]
        list_ = []
        for each in glob.glob(os.path.join(glob_path, '*')):
            list_.append(os.path.split(each)[-1])
        return list_

    def glob_multiple_project_elements(self, split_at=None, *args):
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
        for attr in args:
            obj_.set_attr(attr, '*', regex=False)
        glob_list = glob.glob(obj_.path_root)
        return glob_list

    def copy(self, **kwargs):
        new_obj = copy.deepcopy(self)
        for attr in kwargs:
            new_obj.set_attr(attr, kwargs[attr])
        return new_obj

    def next_minor_version_number(self):
        next_minor = '%03d' % (int(self.minor_version)+1)
        return '%s.%s' % (self.major_version, next_minor)

    def next_major_version_number(self):
        next_major = '%03d' % (int(self.major_version)+1)
        return '%s.%s' % (next_major, self.minor_version)

    def new_major_version_object(self):
        next_major = self.next_major_version_number()
        new_obj = copy.deepcopy(self)
        new_obj.set_attr('version', next_major)
        return new_obj

    def new_minor_version_object(self):
        next_minor = self.next_minor_version_number()
        new_obj = copy.deepcopy(self)
        new_obj.set_attr('version', next_minor)
        return new_obj

    def set_filetype(self):
        """
        sets attr 'filetype' to reflect the kind of file we're working with, or to let me know if it's a folder
        this is just a convenience attr when working with pathObjects
        :return:
        """
        pass

    def set_preview_path(self):
        pass

    def set_proper_filename(self):
        pass

    def set_shotname(self):
        # TODO - for this to be useful it'll have to be a seperation of shotname and assetname based off context
        if self.context == 'shots':
            self.set_attr('shotname', '%s_%s' % (self.seq, self.shot))
        if self.context == 'assets':
            pass
        pass


dict_ = {'shot': 'cement', 'seq': 'Library', 'frame': None, 'minor_version': '000', 'filename_base': 'cement_material',
        'filename': 'cement_material.sbsar', 'version': '001.000', 'asset': 'cement', 'scope': 'assets',
        'render_pass': None, 'type': 'Library', 'cam': None, 'company': 'cgl-cglumberjack', 'aov': None,
        'user': 'publish', 'task': 'tex', 'shotname': None, 'major_version': '001', 'project': 'Library',
        'ext': 'sbsar', 'context': 'source', 'resolution': 'high'}

path = r'D:\cgl-cglumberjack\source\Library\assets\Library\cement\tex\publish\001.000\high\cement_material.sbsar'

obj = PathObject(dict_)

# TODO - derive tests that will test the SHIT out of this code on a ton of different file paths and dictionaries.

