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
from core.util import split_all

from core.config import app_config
#from cglcore.exceptions import LumberJackException
from cglui.widgets.dialog import InputDialog

PROJ_MANAGEMENT = app_config()['account_info']['project_management']
EXT_MAP = app_config()['ext_map']
ROOT = app_config()['paths']['root']


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
        self.file_type = None
        self.scope_list = app_config()['rules']['scope_list']
        self.context_list = app_config()['rules']['context_list']
        self.path = None  # string of the properly formatted path
        self.path_root = None # this gives the full path with the root
        self.split_point = None  # point at which to split the path when formatting.
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

        if type(path_object) is dict:
            self.process_dict(path_object)
        elif type(path_object) is str:
            self.process_string(path_object)
        else:
            logging.error('type: %s not expected' % type(path_object))
        self.set_project_config()

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
            self.data[key] = path_object[key]
            self.set_attr(attr=key, value=path_object[key])

    def get_template(self):
        self.template = []
        if self.context:
            if self.scope:
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
        temp_ = path_string.split(self.root)[-1]
        c = split_all(temp_)[1]
        self.new_set_attr(company=c)
        #companies = app_config()['account_info']['companies']
        #for c in companies:
        #    if c in path_string:
        #        self.new_set_attr(company=c)
        #if not self.company:
        #    logging.error("No Valid Company defined in path provided - invalid path: %s" % path_string)
        #    return

    def unpack_path(self, path_string):
        path_string = os.path.normpath(path_string.split(self.company)[-1])
        path_ = os.path.normpath(path_string)
        path_parts = path_.split(os.sep)
        if path_parts[0] == '':
            path_parts.pop(0)
        path_parts.insert(0, self.company)
        self.set_attr('context', path_parts[1].lower())
        if len(path_parts) > 3:
            self.set_attr('scope', path_parts[3].lower())
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
                        self.set_attr('filename', path_parts[i])
                        filename_base, ext = os.path.splitext(path_parts[i])
                        self.set_attr('filename_base', filename_base)
                        self.set_attr('ext', ext.replace('.', ''))
                    else:
                        self.set_attr(attr, path_parts[i])
                except IndexError:
                    pass
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
        # if windows
        
        if sys.platform == 'win32':
            self.path_root = '%s\\%s' % (self.root, path_string)
            path_, file_ = os.path.split(self.path_root)
        else:
            self.path_root = os.path.join(self.root, path_string)
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

    def new_set_attr(self, **kwargs):
        for attr in kwargs:
            value = kwargs[attr]

            try:
                regex = app_config()['rules']['path_variables'][attr]['regex']
            except KeyError:
                logging.info('Could not find regex for %s in config, skipping' % attr)
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
                            try:
                                if not re.match(regex, value):
                                    logging.error('%s does not follow regex for %s: %s' % (value, attr, regex))
                                    # return
                            except TypeError:
                                pass
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
            elif attr == 'filename':
                self.__dict__['filename'] = value
                self.data['filename'] = value
                self.set_proper_filename()
        self.set_path()

    def set_attr(self, attr, value, regex=True):
        """
        Sets Attr attr, at value, regex requirement can be turned on or off.
        :param attr:
        :param value:
        :param regex:
        :return:
        """
        if attr != 'root':
            if regex:
                try:
                    regex = app_config()['rules']['path_variables'][attr]['regex']
                except KeyError:
                    logging.info('Could not find regex for %s in config, skipping' % attr)
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
                        try:
                            if not re.match(regex, value):
                                pass
                                #logging.error('%s does not follow regex for %s: %s' % (value, attr, regex))
                                #return
                        except TypeError:
                            pass
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
        elif attr == 'filename':
            self.__dict__['filename'] = value
            self.data['filename'] = value
            self.set_proper_filename()
        self.set_path()

    def glob_project_element(self, attr, full_path=False):
        """
        Simple Glob Function.  "I want to return all "projects"" for instance would be written this way:
        glob_project_element(self, 'project')
        this would return a list of project names.  Use the full_path flag to return a list of paths.
        :param self: self
        :param attr: attribute name: 'project', 'scope', 'version', filename, etc...
        :param full_path: if True returns full paths for everything globbed
        :return: returns list of items, or paths.
        """
        # this does not account for duplicate values - need a system that does.

        value = self.data[attr]
        glob_path = self.path_root.split(value)[0]
        list_ = []
        if not full_path:
            for each in glob.glob(os.path.join(glob_path, '*')):
                list_.append(os.path.split(each)[-1])
        else:
            list_ = glob.glob(os.path.join(glob_path, '*'))
        return list_

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


    def copy(self, **kwargs):
        new_obj = copy.deepcopy(self)
        for attr in kwargs:
            new_obj.set_attr(attr, kwargs[attr])
        return new_obj

    def next_minor_version_number(self):
        if not self.minor_version:
            next_minor = '001'
        else:
            next_minor = '%03d' % (int(self.minor_version)+1)
        return '%s.%s' % (self.major_version, next_minor)

    def next_major_version_number(self):
        if not self.major_version:
            next_major = '001'
        else:
            next_major = '%03d' % (int(self.major_version)+1)
        return '%s.%s' % (next_major, '000')

    def new_major_version_object(self):
        next_major = self.next_major_version_number()
        new_obj = copy.deepcopy(self)
        new_obj.new_set_attr(version=next_major)
        return new_obj

    def new_minor_version_object(self):
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
        if self.filename:
            self.filename_base, self.ext = os.path.splitext(self.filename)
        else:
            self.filename_base = ''
            self.ext = ''
        pass

    def set_shotname(self):
        if self.context == 'shots':
            self.set_attr('shotname', '%s_%s' % (self.seq, self.shot))
        if self.context == 'assets':
            self.set_attr('assetname', '%s_%s' % (self.seq, self.shot))
            pass
        pass

    def set_project_config(self):
        user_dir = os.path.expanduser("~")
        cg_lumberjack_dir = os.path.join(user_dir, 'cglumberjack', 'companies')
        if self.company:
            self.company_config = os.path.join(cg_lumberjack_dir, self.company, 'global.yaml')
        if self.project:
            self.project_config = os.path.join(os.path.dirname(self.company_config), self.project, 'global.yaml')


class CreateProductionData(object):
    def __init__(self, path_object=None, file_system=True, project_management=PROJ_MANAGEMENT,
                 scene_description=False, do_scope=False, test=False):
        self.test = test
        self.path_object = PathObject(path_object)
        self.do_scope = do_scope
        if file_system:
            self.create_folders()
        print 'Created Folders for %s' % self.path_object.path_root
        if project_management:
            logging.info('Creating Production Management Data for %s: %s' % (project_management, self.path_object.data))
            self.create_project_management_data(self.path_object, project_management)
        if scene_description:
            self.create_scene_description()
        if self.path_object.resolution:
            self.create_default_file()

    def create_folders(self):
        if not self.path_object.root:
            logging.info('No Root Defined')
            return
        if not self.path_object.company:
            logging.info('No Company Defined')
            return
        if not self.path_object.context:
            self.path_object.new_set_attr(context='source')

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
            d = {'assets': 'shots', 'shots': 'assets'}
            if path_object.scope:
                new_obj = path_object.copy(scope=d[path_object.scope])
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
        print 'Creating directories: %s' % path_
        if not test:
            if not os.path.exists(path_):
                os.makedirs(path_)

    def create_scene_description(self):
        print 'CREATING SCENE DESCRIPTION:'
        print self.path_object.path_root
        print 'Json based Scene Descriptions Not Yet Connected'

    @staticmethod
    def create_project_management_data(path_object, project_management):
        # TODO I need to do something that syncs my globals to the cloud in case they get toasted.
        # management software
        # and another studio wants a different kind of project management software by default.
        if project_management != 'lumbermill':
            module = "plugins.project_management.%s.main" % project_management
            loaded_module = __import__(module, globals(), locals(), 'main', -1)
            print path_object
            loaded_module.ProjectManagementData(path_object).create_project_management_data()
        else:
            print 'Using Lumbermill built in proj management'

    def create_default_file(self):
        if self.path_object.task == 'prev':
            self.path_object.new_set_attr(filename='%s_%s_%s.mb' % (self.path_object.seq,
                                                                    self.path_object.shot,
                                                                    self.path_object.task))
            this = __file__.split('src')[0]
            default_file = "%ssrc\%s" % (this, r'plugins\maya\2018\templates\default.mb')
            logging.info('Creating Default Previs file: %s' % self.path_object.path_root)
            shutil.copy2(default_file, self.path_object.path_root)


def icon_path():
    return os.path.join(app_config()['paths']['code_root'], 'resources', 'images')


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
    return re.sub('[^A-Za-z0-9\.#]+', '_', filename)





