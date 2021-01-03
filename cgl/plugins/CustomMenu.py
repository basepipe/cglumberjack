import os
import json
from cgl.core.path import PathObject
from cgl.core.config.config import ProjectConfig


class CustomMenu(object):
    """
    A Base Class to be used in conjunction with the "Menu Designer".

    A user simply has to fill in the following functions:
    get_scene_path()
    set_menu_parent()
    create_menu()
    add_button()
    delete_menu()
    find_menu_by_name()

    examples can be found here:
    plugins/nuke/custom_menu.py
    plugins/maya/custom_menu.py

    """

    def __init__(self, software, type_):
        print(1)
        self.path_object = None
        self.software = software
        self.type = type_
        self.scene_path = self.get_scene_path()
        self.menu_parent = self.set_menu_parent()
        self.shelf_set_name = None
        self.shelf_path = None
        self.shelf_set = None
        self.set_path_object()
        if self.scene_path:
            self.path_object = PathObject(str(self.scene_path))
        else:
            print('No Valid Scene Path')
        self.cfg = ProjectConfig(self.path_object)
        self.project_config = self.cfg.project_config_file
        print('Company Config is: %s' % self.project_config)
        if not os.path.exists(self.project_config):
            print('Project Config %s: does no exist' % self.project_config)
            return

        self.menus_file = os.path.join(self.cfg.cookbook_folder, software, '%s.cgl' % self.type)
        self.menus = self.load_cgl()
        self.menus_folder = os.path.join(os.path.dirname(self.menus_file), type_)
        self.menu_dict = {}

    def set_path_object(self):
        if self.scene_path:
            print('Setting PathObject with %s' % self.scene_path)
            print(self.scene_path)
            self.path_object = PathObject(str(self.scene_path))

    def load_cgl(self):
        """
        returns all the shelves, menus, or pre_publish from the json file
        :return:
        """
        if os.path.exists(self.menus_file):
            with open(self.menus_file, 'r') as stream:
                    result = json.load(stream)
                    if result:
                        return result[self.software]
                    else:
                        return
        else:
            print('No menu file found!')

    @staticmethod
    def order_menus(menus):
        """
        Orders the Menus from the json file correctly.  This is necessary for the menus to show up in the correct
        order within the interface.
        :return:
        """
        for menu in menus:
            menus[menu]['order'] = menus[menu].get('order', 10)
        if menus:
            return sorted(menus, key=lambda key: menus[key]['order'])
        
    def order_buttons(self, menu):
        """
        orders the buttons correctly within a menu.
        :param menu:
        :return:
        """
        buttons = self.menus[menu]
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

    @staticmethod
    def remove_inactive_buttons(menus):
        to_pop = []
        for menu in menus:
            if menus[menu]['active'] == 0:
                to_pop.append(menu)
        for each in to_pop:
            menus.pop(each)
        if menus:
            return menus
        else:
            return {}

    def delete_menus(self):
        if self.menus:
            for menu in self.menus:
                if isinstance(menu, dict):
                    menu = menu['name']
                print('deleting %s' % menu)
                self.delete_menu(menu)
        self.delete_after_menus()

    def delete_menu(self, menu_name):
        pass

    def remove_inactive_menus(self):
        menus = self.menus
        to_pop = []
        for menu in menus:
            print(menu['name'])

            # if menus[menu]['active'] == 0:
            #    to_pop.append(menu)
        for each in to_pop:
            menus.pop(each)
        if menus:
            return menus
        else:
            return {}

    def get_icon_path(self, shelf, button):
        """
        returns the icon path within the current menu of the cgl_tools directory of the corresponding icon
        :param shelf:
        :param button:
        :return: icon path string
        """
        icon_path = os.path.join(self.project_config, 'cgl_tools')
        if self.menus[shelf][button]['icon']:
            icon_file = os.path.join(icon_path, self.menus[shelf][button]['icon'])
            return icon_file
        else:
            return ''

    def add_menu_buttons(self, menu, buttons):
        for button in buttons:
            label = button['label']
            if 'icon' in button.keys():
                icon_file = button['icon']
                if icon_file:
                    label = ''
            else:
                icon_file = ''

            if 'annotation' in button.keys():
                annotation = button['annotation']
            else:
                annotation = ''
            print(icon_file)
            self.add_button(menu, label=button['name'],
                            annotation=annotation,
                            command=button['module'],
                            icon=icon_file,
                            image_overlay_label=label)

    def load_menus(self, test=False):
        """
        loads all menus
        :param test:
        :return:
        """
        # if test:
        #     self.delete_menus()
        try:
            menus = self.remove_inactive_menus()
        except KeyError:
            menus = self.menus
            pass

        software_menus = menus
        print('menus: %s', software_menus)
        for menu in software_menus:
            menu_name = menu['name']
            print('menu')
            print('\t', menu_name)
            if test:
                print('menu: ', menu_name)
                print('buttons:', menu['buttons'])
            else:
                _menu = self.create_menu(menu_name)
                self.menu_dict[menu_name] = _menu
                buttons = menu['buttons']
                self.add_menu_buttons(menu_name, buttons)

    # When Starting a new shelf, simply copy all of the functions below and fill them in with softwarespecific functions
    # See Nuke and Maya examples: plugins/nuke/custom_menu.py & plugins/maya/custom_menu.py

    def get_scene_path(self):
        pass

    def set_menu_parent(self):
        return False

    def create_menu(self, name):
        pass

    def add_button(self, menu, label='', annotation='', command='', icon='', image_overlay_label='', hot_key=''):
        pass

    @staticmethod
    def find_menu_by_name(**kwargs):
        pass

    def delete_after_menus(self):
        pass





