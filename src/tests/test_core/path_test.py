import pytest
from core.path import PathObject

path = r'D:\cgl-cglumberjack\source\Library\assets\Library\cement\tex\publish\001.000\high\cement_material.sbsar'


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










