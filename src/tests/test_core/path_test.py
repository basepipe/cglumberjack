import pytest
from core.path import PathObject


path = r'D:\cgl-cglumberjack\source\Library\assets\Library\cement\tex\publish\001.000\high\cement_material.sbsar'
path_dict = {'shot': 'cement', 'seq': 'Library', 'frame': None, 'minor_version': '000',
             'filename_base': 'cement_material',
             'filename': 'cement_material.sbsar', 'version': '001.000', 'asset': 'cement', 'scope': 'assets',
             'render_pass': None, 'type': 'Library', 'cam': None, 'company': 'cgl-cglumberjack', 'aov': None,
             'user': 'publish', 'task': 'tex', 'shotname': None, 'major_version': '001', 'project': 'Library',
             'ext': 'sbsar', 'context': 'source', 'resolution': 'high'}

asset_path = r'D:\cgl-cglumberjack\source\Library\assets\Library\cement\tex\publish\001.000\high\cement_material.sbsar'
asset_path_dict = {'shot': 'cement', 'seq': 'Library', 'frame': None, 'minor_version': '000',
                   'filename_base': 'cement_material',
                   'filename': 'cement_material.sbsar', 'version': '001.000', 'asset': 'cement', 'scope': 'assets',
                   'render_pass': None, 'type': 'Library', 'cam': None, 'company': 'cgl-cglumberjack', 'aov': None,
                   'user': 'publish', 'task': 'tex', 'shotname': None, 'major_version': '001', 'project': 'Library',
                   'ext': 'sbsar', 'context': 'source', 'resolution': 'high'}

asset_path2 = r'D:\cgl-cglumberjack\source\Library\assets\Library\cement\tex\publish\001.000\high'
asset_path2_dict = {'shot': 'cement', 'seq': 'Library', 'frame': None, 'minor_version': '000',
                    'version': '001.000', 'asset': 'cement', 'scope': 'assets', 'filename': None,
                    'filename_base': None, 'ext': None,
                    'render_pass': None, 'type': 'Library', 'cam': None, 'company': 'cgl-cglumberjack', 'aov': None,
                    'user': 'publish', 'task': 'tex', 'shotname': None, 'major_version': '001', 'project': 'Library',
                    'context': 'source', 'resolution': 'high'}

asset_path3 = r'D:\cgl-cglumberjack\source\Library\assets\Library\cement\tex\publish\001.000'
asset_path3_dict = {'shot': 'cement', 'seq': 'Library', 'frame': None, 'minor_version': '000',
                    'version': '001.000', 'asset': 'cement', 'scope': 'assets', 'filename_base': None,
                    'filename': None, 'ext': None,
                    'render_pass': None, 'type': 'Library', 'cam': None, 'company': 'cgl-cglumberjack', 'aov': None,
                    'user': 'publish', 'task': 'tex', 'shotname': None, 'major_version': '001', 'project': 'Library',
                    'context': 'source', 'resolution': None}

asset_path4 = r'D:\cgl-cglumberjack\source\Library\assets\Library\cement\tex\publish'
asset_path4_dict = {'shot': 'cement', 'seq': 'Library', 'frame': None, 'minor_version': None,
                    'version': None, 'asset': 'cement', 'scope': 'assets', 'filename_base': None,
                    'filename': None, 'ext': None, 'render_pass': None, 'type': 'Library', 'cam': None,
                    'company': 'cgl-cglumberjack', 'aov': None, 'user': 'publish', 'task': 'tex', 'resolution': None,
                    'shotname': None, 'major_version': None, 'project': 'Library', 'context': 'source'}

asset_path5 = r'D:\cgl-cglumberjack\source\Library\assets\Library\cement\tex'
asset_path5_dict = {'shot': 'cement', 'seq': 'Library', 'frame': None, 'minor_version': None,
                    'version': None, 'asset': 'cement', 'scope': 'assets', 'filename_base': None,
                    'filename': None, 'ext': None, 'render_pass': None, 'type': 'Library', 'cam': None,
                    'company': 'cgl-cglumberjack', 'aov': None, 'user': None, 'task': 'tex', 'resolution': None,
                    'shotname': None, 'major_version': None, 'project': 'Library', 'context': 'source'}

asset_path6 = r'D:\cgl-cglumberjack\source\Library\assets\Library\cement'
asset_path6_dict = {'shot': 'cement', 'seq': 'Library', 'frame': None, 'minor_version': None,
                    'version': None, 'asset': 'cement', 'scope': 'assets', 'filename_base': None,
                    'filename': None, 'ext': None, 'render_pass': None, 'type': 'Library', 'cam': None,
                    'company': 'cgl-cglumberjack', 'aov': None, 'user': None, 'task': None, 'resolution': None,
                    'shotname': None, 'major_version': None, 'project': 'Library', 'context': 'source'}

asset_path7 = r'D:\cgl-cglumberjack\source\Library\assets\Library'
asset_path7_dict = {'shot': None, 'seq': 'Library', 'frame': None, 'minor_version': None,
                    'version': None, 'asset': None, 'scope': 'assets', 'filename_base': None,
                    'filename': None, 'ext': None, 'render_pass': None, 'type': 'Library', 'cam': None,
                    'company': 'cgl-cglumberjack', 'aov': None, 'user': None, 'task': None, 'resolution': None,
                    'shotname': None, 'major_version': None, 'project': 'Library', 'context': 'source'}

asset_path8 = r'D:\cgl-cglumberjack\source\Library\assets'
asset_path8_dict = {'shot': None, 'seq': None, 'frame': None, 'minor_version': None,
                    'version': None, 'asset': None, 'scope': 'assets', 'filename_base': None,
                    'filename': None, 'ext': None, 'render_pass': None, 'type': None, 'cam': None,
                    'company': 'cgl-cglumberjack', 'aov': None, 'user': None, 'task': None, 'resolution': None,
                    'shotname': None, 'major_version': None, 'project': 'Library', 'context': 'source'}

asset_path9 = r'D:\cgl-cglumberjack\source\Library'
asset_path9_dict = {'shot': None, 'seq': None, 'frame': None, 'minor_version': None,
                    'version': None, 'asset': None, 'scope': None, 'filename_base': None,
                    'filename': None, 'ext': None, 'render_pass': None, 'type': None, 'cam': None,
                    'company': 'cgl-cglumberjack', 'aov': None, 'user': None, 'task': None, 'resolution': None,
                    'shotname': None, 'major_version': None, 'project': 'Library', 'context': 'source'}

asset_path10 = r'D:\cgl-cglumberjack\source'
asset_path10_dict = {'shot': None, 'seq': None, 'frame': None, 'minor_version': None,
                     'version': None, 'asset': None, 'scope': None, 'filename_base': None,
                     'filename': None, 'ext': None, 'render_pass': None, 'type': None, 'cam': None,
                     'company': 'cgl-cglumberjack', 'aov': None, 'user': None, 'task': None, 'resolution': None,
                     'shotname': None, 'major_version': None, 'project': None, 'context': 'source'}

asset_path11 = r'D:\cgl-cglumberjack'
asset_path11_dict = {'shot': None, 'seq': None, 'frame': None, 'minor_version': None,
                     'version': None, 'asset': None, 'scope': None, 'filename_base': None,
                     'filename': None, 'ext': None, 'render_pass': None, 'type': None, 'cam': None,
                     'company': 'cgl-cglumberjack', 'aov': None, 'user': None, 'task': None, 'resolution': None,
                     'shotname': None, 'major_version': None, 'project': None, 'context': None}

asset_path12 = r'D:'
asset_path12_dict = {'shot': None, 'seq': None, 'frame': None, 'minor_version': None,
                     'version': None, 'asset': None, 'scope': None, 'filename_base': None,
                     'filename': None, 'ext': None, 'render_pass': None, 'type': None, 'cam': None,
                     'company': None, 'aov': None, 'user': None, 'task': None, 'resolution': None,
                     'shotname': None, 'major_version': None, 'project': None, 'context': None}

# TODO - derive tests that will test the POOP out of this code on a ton of different file paths and dictionaries.


def test_can_call_PathObject():
    PathObject(path)
    assert True


def test_valid_project():
    obj_ = PathObject(path)
    assert obj_.project


def test_get_attrs_from_config():
    #
    # need a way of grabbing all possible path variables
    obj_ = PathObject(path)
    obj_.get_attrs_from_config()
    assert True


def test_compare_config_to_obj_attrs():
    obj_ = PathObject(path)
    for config_attr in obj_.get_attrs_from_config():
        if config_attr in obj_.__dict__:
            assert True
        else:
            print config_attr
            assert False


def test_major_version_number():
    obj_ = PathObject(path)
    assert obj_.major_version


def test_all_attrs_in_data():
    obj_ = PathObject(path)
    for config_attr in obj_.get_attrs_from_config():
        if config_attr in obj_.data.keys():
            assert True
        else:
            print config_attr, ' Not Found in obj.data'
            assert False


def test_attrs_match_data():
    obj = PathObject(path)
    for config_attr in obj.get_attrs_from_config():
        assert obj.data[config_attr] == obj.__dict__[config_attr]


def test_path_to_dict():
    obj = PathObject(asset_path)
    dict_ = asset_path_dict
    for attr in obj.__dict__:
        if attr in obj.get_attrs_from_config():
            if attr == dict_[attr]:
                assert True

def test_path2_to_dict():
    obj = PathObject(asset_path2)
    dict_ = asset_path2_dict
    for attr in obj.__dict__:
        if attr in obj.get_attrs_from_config():
            if attr == dict_[attr]:
                assert True

def test_path3_to_dict():
    obj = PathObject(asset_path3)
    dict_ = asset_path3_dict
    for attr in obj.__dict__:
        if attr in obj.get_attrs_from_config():
            if attr == dict_[attr]:
                assert True

def test_path4_to_dict():
    obj = PathObject(asset_path4)
    dict_ = asset_path4_dict
    for attr in obj.__dict__:
        if attr in obj.get_attrs_from_config():
            if attr == dict_[attr]:
                assert True


def test_path5_to_dict():
    obj = PathObject(asset_path5)
    dict_ = asset_path5_dict
    for attr in obj.__dict__:
        if attr in obj.get_attrs_from_config():
            if attr == dict_[attr]:
                assert True

def test_path6_to_dict():
    obj = PathObject(asset_path6)
    dict_ = asset_path6_dict
    for attr in obj.__dict__:
        if attr in obj.get_attrs_from_config():
            if attr == dict_[attr]:
                assert True


def test_path7_to_dict():
    obj = PathObject(asset_path7)
    dict_ = asset_path7_dict
    for attr in obj.__dict__:
        if attr in obj.get_attrs_from_config():
            if attr == dict_[attr]:
                assert True


def test_path8_to_dict():
    obj = PathObject(asset_path8)
    dict_ = asset_path8_dict
    for attr in obj.__dict__:
        if attr in obj.get_attrs_from_config():
            if attr == dict_[attr]:
                assert True


def test_path9_to_dict():
    obj = PathObject(asset_path9)
    dict_ = asset_path9_dict
    for attr in obj.__dict__:
        if attr in obj.get_attrs_from_config():
            if attr == dict_[attr]:
                assert True


def test_path10_to_dict():
    obj = PathObject(asset_path10)
    dict_ = asset_path10_dict
    for attr in obj.__dict__:
        if attr in obj.get_attrs_from_config():
            if attr == dict_[attr]:
                assert True


def test_path11_to_dict():
    obj = PathObject(asset_path11)
    dict_ = asset_path11_dict
    for attr in obj.__dict__:
        if attr in obj.get_attrs_from_config():
            if attr == dict_[attr]:
                assert True


def test_path12_to_dict():
    obj = PathObject(asset_path12)
    dict_ = asset_path12_dict
    for attr in obj.__dict__:
        if attr in obj.get_attrs_from_config():
            if attr == dict_[attr]:
                assert True


def test_dict_to_path():
    obj = PathObject(asset_path_dict)
    comp_path = asset_path
    assert comp_path == obj.path_root


def test_dict2_to_path():
    obj = PathObject(asset_path2_dict)
    assert asset_path2 == obj.path_root


def test_dict3_to_path():
    obj = PathObject(asset_path3_dict)
    assert asset_path3 == obj.path_root


def test_dict4_to_path():
    obj = PathObject(asset_path4_dict)
    assert asset_path4 == obj.path_root


def test_dict5_to_path():
    obj = PathObject(asset_path5_dict)
    assert asset_path5 == obj.path_root


def test_dict6_to_path():
    obj = PathObject(asset_path6_dict)
    assert asset_path6 == obj.path_root


def test_dict7_to_path():
    obj = PathObject(asset_path7_dict)
    assert asset_path7 == obj.path_root


def test_dict8_to_path():
    obj = PathObject(asset_path8_dict)
    assert asset_path8 == obj.path_root


def test_dict9_to_path():
    obj = PathObject(asset_path9_dict)
    assert asset_path9 == obj.path_root


def test_dict10_to_path():
    obj = PathObject(asset_path10_dict)
    assert asset_path10 == obj.path_root


def test_dict11_to_path():
    obj = PathObject(asset_path11_dict)
    assert asset_path11 == obj.path_root

def test_dict12_to_path(): 
    obj = PathObject(asset_path12_dict)
    assert asset_path12 == obj.path_root











