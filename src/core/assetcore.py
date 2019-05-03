import json
import logging
from enum import Enum
logging.getLogger().setLevel(logging.INFO)


class MetaObject(object):
    def __init__(self, jsonfile=None, _type=None, **kwargs):
        self._metaItems = []
        self._type = _type
        # if 'name' not in kwargs:
        #     raise AttributeError('no name defined for MetaItem %s' % self)

        if jsonfile:
            print jsonfile
            # read and parse json if its given
            data = readJson(jsonfile)
            if data:
                for item, attr in data.iteritems():
                    print item, attr
                    self._metaItems.append(BaseItem(_type=attr['type'], uid=item, **attr))
        else:
            if kwargs:
                self._metaItems.append(BaseItem(_type=_type, **kwargs))

    def add(self, _type, uid, **attr):
        '''
        adds
        :param context: Layout, project or asset
        :param uid: unique id that groups each asset
        :param attr: all attributes you wish to add to the meta
        :return:
        '''

        self._type = _type
        self.uid = uid

        #if not self._type:
        #    raise AttributeError('no type given for MetaItem %s, type: %s' % (self, type(self)))
        #if not 'uid' in attr:
        #    raise AttributeError('no uid given for MetaItem %s, type: %s' % (self, type(self)))
        for item in self._metaItems:
            if item.uid == uid:
                self._metaItems.remove(item)
        self._metaItems.append(BaseItem(_type=self._type, uid=uid, **attr))
        return BaseItem(_type=self._type, uid=uid, **attr)

    def find(self, value=False, **attributes):
        '''
        finds all meta items that match attributes by default
        :value: switches what find will return
        :param attributes: which attributes and values to find
        :return: list of found MetaNodes, if Value will return dict of uid:value pairs
        '''
        if value:
            data = {}
        else:
            data = list()
        for item in self._metaItems:
            if value:
                found = self.search(item.data.uid, uid=item.uid, **attributes)
            else:
                found = self.search(item.data.uid, **attributes)
            if value:
                for attr, val in found.iteritems():
                    data[attr] = val
            else:
                data.append(item)
        if data:
            return data

    def search(self, item, uid=None, **attributes):
        if uid:
            data = {}
        else:
            data = []
        for attr, val in attributes.iteritems():
            if hasattr(item, attr):
                if isinstance(val, MetaNode):
                    data.append(self.search(val, **attributes))
                if getattr(item, attr) == val:
                    if uid:
                        data[uid] = val
                    else:
                        data.append(item)
        return data

    def save(self, path):
        data = {}
        for metaitem in self._metaItems:
            data[metaitem.uid] = self.itemtojson(metaitem.data.uid)
        print data
        writeJson(path, data)

    def itemtojson(self, obj):
        # excluded = ['structure', 'uidref']
        d = {}
        if isinstance(obj, MetaNode):
            for attr, val in obj.__dict__.iteritems():
                if isinstance(val, MetaNode):
                    d[attr] = self.itemtojson(val)
                else:
                    d[attr] = val
        return d

    def __len__(self):
        return len(self._metaItems)

    def __iter__(self):
        x = 0
        while x < len(self._metaItems):
            yield self._metaItems[x]
            x += 1

    def __getitem__(self, index):
        return self._metaItems[index]


class BaseItem(object):
    EXCLUSIONS = ['context', 'kwargs', 'uid']
    def __init__(self, _type=None, **kwargs):
        '''
        :parm name:
            Required to initialize meta item
        :parm uid:
            not required but recommended
        :parm jsonfile:
            can read json file directly and convert to MetaItem
        :param kwargs:
        '''

        # Declaration of Types NEW TYPES GO HERE
        if _type == 'asset':
            self.__class__ = AssetItem
        elif _type == 'layout':
            self.__class__ = LayoutItem
        elif _type == 'project':
            self.__class__ = ProjectItem
        elif _type == 'bundle':
            self.__class__ = BundleItem
        elif _type == 'anim':
            self.__class__ = AnimItem
        elif _type == 'mdl':
            self.__class__ = ModelItem
        elif _type == 'tex':
            self.__class__ = TextureItem
        elif _type == 'package':
            self.__class__ = AssetPackage
        elif _type == 'rig':
            self.__class__ = RigItem
        elif _type == 'cam':
            self.__class__ = CameraItem
        elif _type == 'shd':
            self.__class__ = ShaderItem
        elif _type == 'link':
            self.__class__ = LinkItem
        elif _type == 'init':
            self.__class__ = InitialItem

        self.data = []
        if kwargs:
            if 'uid' in kwargs:
                self.uid = kwargs['uid']
            else:
                logging.error('No uid set for object %s' % self)

            self.set_structure()
            self.processdict(**kwargs)
        else:
            logging.info('Initialized Empty Base Item')

    def set_structure(self):
        pass

    def build_structure(self, dct, structure):
        '''
        recursive function for building the class structure of the BaseItem
        :param dct:
        :param structure:
        :return:
        '''
        for key, val in dct.iteritems():
            if isinstance(val, dict):
                new_group = MetaNode()
                structure.__setattr__(key, new_group)
                self.build_structure(val, structure=new_group)
            else:
                structure.__setattr__(key, val)
        return

    def processdict(self, **kwargs):
        '''
        how input structure is processed
        :param dct:
        :return:
        '''
        for arg, val in kwargs.iteritems():
            self.set_attribute(self.data, arg, val)

    def set_attribute(self, node, attr, val):
        if attr not in node.__dict__.keys():
            for a, v in node.__dict__.iteritems():
                if isinstance(v, MetaNode):
                    # with nested dictionaries this isn't working.
                    self.set_attribute(v, attr, val)
        else:
            if hasattr(node, attr):
                if not isinstance(node.__getattribute__(attr), MetaNode):
                    node.__setattr__(attr, val)

    def __get__(self, obj, objtype=None):
        if obj not in self.blueprint.__dict__.keys():
            for a, v in self.blueprint.__dict__.iteritems():
                if isinstance(v, MetaNode):
                    self.__get__(v)

    def writejson(self, writedata):
        pass

    def add(self, **kwargs):
        self.processdict(kwargs)


    @property
    def attributes(self):
        d = self.__dict__.keys()
        d.remove('kwargs')
        return d


class LayoutItem(BaseItem):
    '''
    writes out the layout json in the proper format
    '''
    def __init__(self, **kwargs):
        super(LayoutItem, self).__init__(**kwargs)

    def set_structure(self):
        '''
        uid should always be the parent structure
        :return:
        '''

        self.structure = {'uid':
                          {'name': IVals.REQUIRED,
                           'task': IVals.REQUIRED,
                           'id': True,
                           'type': 'layout',
                           'attributes':
                              {'source_path': IVals.REQUIRED,
                               'maya_path': False,
                               'transform': True,
                               'meta_path': True,
                               'unity_path': False,
                               'children': False}
                           }
                          }
        self.data = MetaNode()
        self.build_structure(self.structure, structure=self.data)


class BundleItem(BaseItem):
    '''
    writes out the layout json in the proper format
    '''
    def __init__(self, **kwargs):
        super(BundleItem, self).__init__(**kwargs)

    def set_structure(self):
        '''
        uid should always be the parent structure
        :return:
        '''

        self.structure = {'uid':
                          {'name': IVals.REQUIRED,
                           'task': IVals.REQUIRED,
                           'id': True,
                           'type': 'bundle',
                           'attributes':
                              {'source_path': IVals.REQUIRED,
                               'bundle_path': False,
                               'transform': True,
                               'children': False,
                               'unity_path': False}
                           }
                          }
        self.data = MetaNode()
        self.build_structure(self.structure, structure=self.data)


class LinkItem(BaseItem):
    '''
    Link Items are to be links to published version of json files.  Essentially
    they should be the only thing in a "layout".
    '''
    def __init__(self, **kwargs):
        super(LinkItem, self).__init__(**kwargs)

    def set_structure(self):
        '''
        uid should always be the parent structure
        :return:
        '''
        self.structure = {'uid':
                          {'name': IVals.REQUIRED,
                           'task': True,
                           'type': IVals.REQUIRED,
                           'added_from': True,
                           'json': True,
                           'transform': None,
                           'scope': IVals.REQUIRED
                           }
                          }
        self.data = MetaNode()
        self.build_structure(self.structure, structure=self.data)


class AssetItem(BaseItem):
    '''
    writes out the asset json in the proper format
    '''
    def __init__(self, **kwargs):
        super(AssetItem, self).__init__(**kwargs)

    def set_structure(self):
        '''
        uid should always be the parent structure
        :return:
        '''
        self.structure = {'uid':
                          {'name': IVals.REQUIRED,
                           'task': IVals.REQUIRED,
                           'type': 'asset',
                           'source_path': IVals.REQUIRED,
                           'fbx_path': False,
                           'obj_path': False,
                           'mb_path': False,
                           'abc_path': False,
                           'transform': IVals.REQUIRED,
                           'unity_path': True
                           }
                          }
        self.data = MetaNode()
        self.build_structure(self.structure, structure=self.data)


class CameraItem(BaseItem):
    '''
    writes out the asset json in the proper format
    '''
    def __init__(self, **kwargs):
        super(CameraItem, self).__init__(**kwargs)

    def set_structure(self):
        '''
        uid should always be the parent structure
        :return:
        '''

        self.structure = {'uid':
                          {'name': IVals.REQUIRED,
                           'task': IVals.REQUIRED,
                           'type': 'cam',
                           'source_path': IVals.REQUIRED,
                           'transform': IVals.REQUIRED,
                           'fbx_path': IVals.REQUIRED,
                           'mb_path': IVals.REQUIRED,
                           'abc_path': False,
                           'json_path': IVals.REQUIRED,
                           'unity_path': True,
                           'film_back': None,
                           'lens': None
                           }
                          }
        self.data = MetaNode()
        self.build_structure(self.structure, structure=self.data)


class RigItem(BaseItem):
    '''
    writes out the asset json in the proper format
    '''
    def __init__(self, **kwargs):
        super(RigItem, self).__init__(**kwargs)

    def set_structure(self):
        '''
        uid should always be the parent structure
        :return:
        '''

        self.structure = {'uid':
                          {'name': IVals.REQUIRED,
                           'task': 'rig',
                           'type': 'rig',
                           'source_path': IVals.REQUIRED,
                           'mb_path': IVals.REQUIRED
                           }
                          }
        self.data = MetaNode()
        self.build_structure(self.structure, structure=self.data)


class AssetPackage(BaseItem):
    '''
    writes out the asset json in the proper format
    '''
    def __init__(self, **kwargs):
        super(AssetPackage, self).__init__(**kwargs)

    def set_structure(self):
        '''
        uid should always be the parent structure
        :return:
        '''

        self.structure = {'uid':
                          {'name': IVals.REQUIRED,
                           'type': 'package',
                           'attributes':
                               {'model': False,
                                'texture': False,
                                'shader': False,
                                'transform': IVals.REQUIRED,
                                'unity_path': True}
                           }
                          }
        self.data = MetaNode()
        self.build_structure(self.structure, structure=self.data)


class ModelItem(BaseItem):
    '''
    writes out the asset json in the proper format
    '''
    def __init__(self, **kwargs):
        super(ModelItem, self).__init__(**kwargs)

    def set_structure(self):
        '''
        uid should always be the parent structure
        :return:
        '''
        print 'modelItem'
        self.structure = {'uid':
                          {'name': IVals.REQUIRED,
                           'task': IVals.REQUIRED,
                           'type': 'mdl',
                           'source_path': IVals.REQUIRED,
                           'fbx_path': None,
                           'obj_path': None,
                           'mb_path': None,
                           'unity_path': None,
                           'materials': [],
                           'udim': []
                           }
                          }
        self.data = MetaNode()
        self.build_structure(self.structure, structure=self.data)

class TextureItem(BaseItem):
    '''
    writes out the asset json in the proper format
    '''
    def __init__(self, **kwargs):
        super(TextureItem, self).__init__(**kwargs)

    def set_structure(self):
        '''
        uid should always be the parent structure
        :return:
        '''
        self.structure = {'uid':
                          {'name': IVals.REQUIRED,
                           'task': 'tex',
                           'type': 'tex',
                           'source_path': None,
                           'tex_path': IVals.REQUIRED,
                           'materials': {},
                           'channels': [],
                           'unity_path': None
                           }
                          }
        self.data = MetaNode()
        self.build_structure(self.structure, structure=self.data)


class ShaderItem(BaseItem):
    '''
    writes out the asset json in the proper format
    '''
    def __init__(self, **kwargs):
        super(ShaderItem, self).__init__(**kwargs)

    def set_structure(self):
        '''
        uid should always be the parent structure
        :return:
        '''

        self.structure = {'uid':
                          {'name': IVals.REQUIRED,
                           'task': 'shd',
                           'type': 'shd',
                           'source_path': IVals.REQUIRED,
                           'mb_path': IVals.REQUIRED,
                           'shaded_model': True,
                           'materials': {}
                           }
                          }
        self.data = MetaNode()
        self.build_structure(self.structure, structure=self.data)


class InitialItem(BaseItem):
    """
    this is the initial .json file that's created before we do any kind of internal "task publish", this allows us to
    create the minimum required information for the json file.
    """
    def __init__(self, **kwargs):
        super(InitialItem, self).__init__(**kwargs)

    def set_structure(self):
        '''
        uid should always be the parent structure
        :return:
        '''
        self.structure = {'uid':
                          {'name': IVals.REQUIRED,
                           'task': IVals.REQUIRED,
                           'type': IVals.REQUIRED,
                           'source_path': IVals.REQUIRED,
                           'status': True,
                           'due': True,
                           'assigned': True,
                           'priority': True
                           }
                          }
        self.data = MetaNode()
        self.build_structure(self.structure, structure=self.data)


class AnimItem(BaseItem):
    '''
    writes out the asset json in the proper format
    '''
    def __init__(self, **kwargs):
        super(AnimItem, self).__init__(**kwargs)

    def set_structure(self):
        '''
        uid should always be the parent structure
        :return:
        '''
        self.structure = {'uid':
                          {'name': IVals.REQUIRED,
                           'task': IVals.REQUIRED,
                           'type': 'anim',
                           'source_path': IVals.REQUIRED,
                           'transform': True,
                           'mb_path': True,
                           'abc_path': IVals.REQUIRED,
                           'unity_path': True,
                           'status': True,
                           'due': True,
                           'assigned': True,
                           'priority': True
                           }
                          }
        self.data = MetaNode()
        self.build_structure(self.structure, structure=self.data)


class ProjectItem(BaseItem):
    '''
    writes out the project item in the proper format
    '''
    def __init__(self, **kwargs):
        super(ProjectItem, self).__init__(**kwargs)

    def set_structure(self):
        self.structure = {'uid':
                          {'name': IVals.REQUIRED,
                           'task': IVals.REQUIRED,
                           'path': IVals.REQUIRED,
                           'type': 'project',
                           'versions':
                               {
                                'publish': IVals.LIST_OPT,
                               }
                           }
                          }
        self.data = MetaNode()
        self.build_structure(self.structure, structure=self.data)


class MetaNode(object):
    '''
    Nested attributes found in a Meta Object
    '''
    def __init__(self, dct=None, **kwargs):
        if dct:
            self.add(dct=dct)
        if kwargs:
            self.add(**kwargs)

    def add(self, dct=None, **attr):
        if dct:
            for attr, data in dct.iteritems():
                self.__setattr__(attr, data)
        else:
            for atr, val in attr.iteritems():
                self.__setattr__(atr, val)

    def search(self, **attr):
        for attr, data in self.__dict__.iteritems():

            if isinstance(data, MetaNode):
                pass


class IVals(Enum):
    OPTIONAL = 0
    REQUIRED = 1
    LIST_OPT = 2
    LIST_REQ = 3


def writeJson(f, assetlist):
    with open(f, 'w') as outfile:
        json.dump(assetlist, outfile, indent=4, sort_keys=True)
    print 'writing json path %s' % f


def readJson(f):
    with open(f) as jsonfile:
        assets = json.load(jsonfile)
    return assets

