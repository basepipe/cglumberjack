import os
import sys
import yaml
import nuke
from cglcore.path import PathObject


PATH_OBJECT = PathObject(str(nuke.root().name()))
# TODO = I need a way of figuring out whether a PATH OBJECT is in compliance with the pipeline
COMPANY_CONFIG = os.path.dirname(PATH_OBJECT.company_config.replace('/', '\\'))
NUKE_SHELVES_PATH = os.path.join(COMPANY_CONFIG, 'cgl_tools', 'nuke', 'shelves.yaml')
NUKE_SHELVES = os.path.join(os.path.dirname(NUKE_SHELVES_PATH), 'shelves')

NUKE_MENUS_PATH = os.path.join(COMPANY_CONFIG, 'cgl_tools', 'nuke', 'menus.yaml')
NUKE_MENUS = os.path.join(os.path.dirname(NUKE_SHELVES_PATH), 'menus')


def get_shelves(path):
    print 0, path
    with open(path, 'r') as stream:
        try:
            result = yaml.load(stream)
            if result:
                return result['nuke']
            else:
                return {}
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(99)


def order_shelves(shelves):
    for shelf in shelves:
        shelves[shelf]['order'] = shelves[shelf].get('order', 10)
    if shelves:
        return sorted(shelves, key=lambda key: shelves[key]['order'])
    else:
        return {}


def order_buttons(shelf_name):
    shelves = get_shelves(NUKE_MENUS_PATH)
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


def create_shelf(name):
    # Create the Top Menu
    menubar = nuke.menu("Nuke")
    return menubar.addMenu("%s" % name)


def find_top_menu(top_menu):
    return nuke.menu('Nuke').findItem(top_menu)


def add_button(shelf, label, command, hotkey=None):
    if not hotkey:
        shelf.addCommand(label, command)
    else:
        shelf.addCommand(label, command, hotkey)


def load_shelves():
    shelves = get_shelves(NUKE_MENUS_PATH)
    for each in shelves:
        shelf_folder = COMPANY_CONFIG
        print each, 'adding this to the PATH', shelf_folder
        if shelf_folder not in sys.path:
            sys.path.insert(0, shelf_folder)

    nuke_shelves = order_shelves(shelves)
    print nuke_shelves
    for shelf in nuke_shelves:
        # basically popup shows what shelves are there, we let them choose, we store that somewhere
        # we only load the shelves that are in those preferences (probably a .yaml file)
        _shelf = create_shelf(shelf.title())
        buttons = order_buttons(shelf)
        for button in buttons:
            # add button to shelf
            print 'Adding %s button to %s shelf' % (button, _shelf)
            add_button(_shelf, button, shelves[shelf][button]['command'])
