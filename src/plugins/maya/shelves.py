import os, sys
import yaml
import pymel.core as pm
from core.config import app_config
from core.path import PathObject
import maya.mel


def get_shelves():
    scene_name = str(pm.sceneName())
    path_object = PathObject(scene_name)
    maya_shelf_path = '%s%s' % (os.path.dirname(path_object.company_config.replace('/', '\\')), '\\cgl_maya\\shelves.yaml')
    with open(maya_shelf_path, 'r') as stream:
        try:
            result = yaml.load(stream)
            if result:
                return result['cgl_maya']
            else:
                return {}
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(99)


def shelf_base():
    name = maya.mel.eval('$tmpVar=$gShelfTopLevel')
    tab = pm.tabLayout(name, query=True, fullPathName=True)
    return tab


def create_shelf(name='test', parent_name=shelf_base()):
    shelf = pm.shelfLayout(name, parent=parent_name)
    return shelf


def add_button(shelf, label='', annotation='', command='', icon='', image_overlay_label=''):
    button_name = pm.shelfButton(image1=icon,
                                 parent=shelf,
                                 label=label,
                                 annotation=annotation,
                                 command=command,
                                 imageOverlayLabel=image_overlay_label)
    return button_name


def order_shelves(shelves):
    for shelf in shelves:
        shelves[shelf]['order'] = shelves[shelf].get('order', 10)
    if shelves:
        return sorted(shelves, key=lambda key: shelves[key]['order'])
    else:
        return {}


def remove_inactive(shelves):
    to_pop = []
    for shelf in shelves:
        print shelves[shelf]['active']
        if shelves[shelf]['active'] == 0:
            to_pop.append(shelf)
    for each in to_pop:
        shelves.pop(each)
    if shelves:
        return shelves
    else:
        return {}


def order_buttons(shelf_name):
    shelves = get_shelves()
    buttons = shelves[shelf_name]
    buttons.pop('order')
    try:
        # there is something weird about this - as soon as these are removed "shelves" never reinitializes
        buttons.pop('active')
    except KeyError:
        pass
    for button in buttons:
        if button:
            buttons[button]['order'] = buttons[button].get('order', 10)
    if buttons:
        return sorted(buttons, key=lambda key: buttons[key]['order'])
    else:
        return {}


def find_shelf_by_name(parent, shelf_name):
    shelf_exists = pm.shelfLayout(shelf_name, exists=True, parent=parent)
    shelf = None
    if shelf_exists:
        shelf = pm.shelfLayout(shelf_name,
                               query=True,
                               fullPathName=True)
    return shelf


def delete_shelf(shelf_name):
    shelf_ = find_shelf_by_name(shelf_base(), shelf_name)
    if shelf_:
        pm.deleteUI(shelf_)


def delete_shelves():
    for shelf in get_shelves():
        delete_shelf(shelf)


def load_shelves():
    delete_shelves()
    shelves = get_shelves()
    for each in shelves:
        print shelves[each]
    try:
        shelves = remove_inactive(shelves)
    except KeyError:
        pass

    maya_shelves = order_shelves(shelves)
    for shelf in maya_shelves:
        # basically popup shows what shelves are there, we let them choose, we store that somewhere
        # we only load the shelves that are in those preferences (probably a .yaml file)
        _shelf = create_shelf(shelf)
        buttons = order_buttons(shelf)
        for button in buttons:
            #try:
            label = shelves[shelf][button]['button name']
            add_button(_shelf, label=shelves[shelf][button]['button name'],
                       annotation=shelves[shelf][button]['annotation'],
                       command=shelves[shelf][button]['command'],
                       icon=get_icon_path(shelves, shelf, button),
                       image_overlay_label=label)
            #except KeyError:
            #    print '%s is not loading properly' % button
            #   print shelves[shelf][button]


def get_icon_path(maya_shelves, shelf, button):
    icon_path = os.path.join(app_config()['paths']['code_root'], 'resources', 'images')
    icon_file = os.path.join(icon_path, maya_shelves[shelf][button]['icon'])
    print icon_file
    return icon_file
