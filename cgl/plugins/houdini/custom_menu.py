import os
import hou
from cgl.plugins.CustomMenu import CustomMenu

shelf_path = os.path.join(os.environ['HOUDINI_USER_PREF_DIR'], 'toolbar', 'cg_lumberjack.shelf')


class HoudiniMenu(CustomMenu):
    def __init__(self, software='houdini', type_='shelves'):
        CustomMenu.__init__(self, software, type_)
        print(self.scene_path)
        print('-------------')

    def get_scene_path(self):
        return hou.hipFile.path()

    def create_menu(self, name):
        """
        Create a Houdini Shelf
        :param name:
        :param label:
        :return:
        """
        all_shelves = list(self.menu_parent.shelves())
        my_shelf = hou.shelves.newShelf(file_path=shelf_path, name=name, label=name)
        all_shelves.append(my_shelf)
        self.menu_parent.setShelves(all_shelves)
        return my_shelf

    def set_menu_parent(self):
        try:
            self.menu_parent = hou.shelves.shelfSets()['cg_lumberjack']
        except KeyError:
            self.menu_parent = hou.shelves.newShelfSet(name='cg_lumberjack', label='CG Lumberjack')
        return self.menu_parent

    def add_button(self, menu_name, label='', annotation='', command='', icon='',
                   image_overlay_label='', name=''):
        shelf = self.find_menu_by_name(menu_name)
        button = hou.shelves.newTool(file_path=shelf_path, name=label, label=label, script=command, icon=icon)
        all_buttons = list(shelf.tools())
        all_buttons.append(button)
        shelf.setTools(all_buttons)
        return button

    def find_menu_by_name(self, menu_name):
        print('finding menu {}'.format(menu_name))
        print(self.menu_parent)
        shelves = list(self.menu_parent.shelves())
        print('shelves:')
        print(shelves)
        for sh in shelves:
            print('\t', sh.name())
            if sh.name() == menu_name:
                return sh

    def delete_menu(self, shelf_name):
        shelf_ = self.find_menu_by_name(shelf_name)
        if shelf_:
            shelf_.destroy()

    def delete_after_menus(self):
        self.menu_parent.destroy()



