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
        self.cam = None
        self.scope_list = app_config()['rules']['scope_list']
        self.context_list = app_config()['rules']['context_list']
        self.path = None  # string of the properly formatted path
        self.split_point = None  # point at which to split the path when formatting.
        self.template = []

        if type(path_object) == dict:
            self.process_dict()
        elif type(path_object) == str:
            self.process_string(path_object)

    def get_attrs_from_config(self):
        attrs = []
        for key in app_config()['rules']['path_variables']:
            attrs.append(key)
        return attrs

    def get_template(self):
        if self.scope:
            if self.context:
                try:
                    path_template = app_config()['templates'][self.context][self.scope]['path'].split('/')
                    if path_template[-1] == '':
                        path_template.pop(-1)
                    version_template = app_config()['templates'][self.context][self.scope]['version'].split('/')
                    self.template = path_template + version_template
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

    def process_string(self, path_object):
        self.get_company(path_object)
        self.unpack_path(path_object)
        self.set_data_from_attrs()
        #self.path_from_attrs()

    def get_company(self, path_string):
        companies = app_config()['defaults']['companies']
        for c in companies:
            if c in path_string:
                self.safe_attr_set('company', c)
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
        self.safe_attr_set('context', path_parts[1].lower())
        self.safe_attr_set('scope', path_parts[3].lower())

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
                        self.safe_attr_set('filename', path_parts[i])
                        filename_base, ext = os.path.splitext(path_parts[i])
                        self.safe_attr_set('filename_base', filename_base)
                        self.safe_attr_set('ext', ext.replace('.', ''))
                    else:
                        self.safe_attr_set(attr, path_parts[i])
                except IndexError:
                    logging.info(attr, None)
        if not self.seq:
            self.safe_attr_set('seq', self.type)
        if not self.shot:
            self.safe_attr_set('shot', self.asset)
        if not self.asset:
            self.safe_attr_set('asset', self.shot)
        if not self.type:
            self.safe_attr_set('type', self.seq)
        if self.version:
            major_version, minor_version = self.version.split('.')
            self.safe_attr_set('major_version', major_version.replace('.', ''))
            self.safe_attr_set('minor_version', minor_version.replace('.', ''))

    def path_from_attrs(self):
        template = self.get_template()
        for i, attr in enumerate(template):
            if attr:
                attr = attr.replace('{', '').replace('}', '')

    def safe_attr_set(self, attr, value):
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
                regex = app_config()['rules']['path_variables'][attr]['regex']
                if not re.match(regex, value):
                    logging.error('%s does not follow regex for %s: %s' % (value, attr, regex))
                    return
                else:
                    self.__dict__[attr] = value
                    self.data[attr] = value


