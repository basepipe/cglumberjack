import os
import json
from cgl.core.path import PathObject
from cgl.core.project import get_cgl_tools, get_cgl_config


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
        self.path_object = None
        self.software = software
        self.type = type_
        self.scene_path = self.get_scene_path()
        self.menu_parent = self.set_menu_parent()
        self.set_path_object()
        if self.scene_path:
            self.path_object = PathObject(str(self.scene_path))
        else:
            print('No Valid Scene Path')
        self.company_config = os.path.dirname(get_cgl_config())
        print('Company Config is: %s' % self.company_config)
        if not os.path.exists(self.company_config):
            print('Company Config %s: does no exist' % self.company_config)
            return

        self.menus_file = os.path.join(get_cgl_tools(), software, '%s.cgl' % self.type)
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
        returns all the shelves, menus, or preflights from the json file
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
                self.delete_menu(menu)

    def delete_menu(self, menu_name):
        pass

    def remove_inactive_menus(self):
        menus = self.menus
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

    def get_icon_path(self, shelf, button):
        """
        returns the icon path within the current menu of the cgl_tools directory of the corresponding icon
        :param shelf:
        :param button:
        :return: icon path string
        """
        icon_path = os.path.join(self.company_config, 'cgl_tools')
        if self.menus[shelf][button]['icon']:
            icon_file = os.path.join(icon_path, self.menus[shelf][button]['icon'])
            return icon_file
        else:
            return ''

    def add_menu_buttons(self, menu, buttons):
        for button in buttons:
            label = self.menus[menu][button]['label']
            if 'icon' in self.menus[menu][button].keys():
                icon_file = self.menus[menu][button]['icon']
                if icon_file:
                    label = ''
            else:
                icon_file = ''

            if 'annotation' in self.menus[menu][button].keys():
                annotation = self.menus[menu][button]['annotation']
            else:
                annotation = ''
            print(icon_file)
            self.add_button(menu, label=self.menus[menu][button]['label'],
                            annotation=annotation,
                            command=self.menus[menu][button]['module'],
                            icon=icon_file,
                            image_overlay_label=label)

    def load_menus(self):
        self.delete_menus()
        try:
            menus = self.remove_inactive_menus()
        except KeyError:
            menus = self.menus
            pass

        software_menus = self.order_menus(menus)
        for menu in software_menus:
            _menu = self.create_menu(menu)
            self.menu_dict[menu] = _menu
            buttons = self.order_buttons(menu)
            self.add_menu_buttons(menu, buttons)

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





