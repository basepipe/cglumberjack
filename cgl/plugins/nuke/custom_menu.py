from plugins.CustomMenu import CustomMenu
import nuke


class NukeCustomMenu(CustomMenu):
    def __init__(self, software='nuke', type_='menus'):
        CustomMenu.__init__(self, software, type_)
        self.scene_path = self.get_scene_path()
        self.path_object = self.set_path_object()

    @staticmethod
    def get_scene_path():
        return nuke.root().name()

    def create_menu(self, name):
        return self.menu_parent.addMenu("%s" % name)

    def set_menu_parent(self):
        if self.type == 'menus':
            return nuke.menu("Nuke")

    def add_button(self, menu, label='', annotation='', command='', icon='', image_overlay_label='', hot_key=''):
        menu_ = self.menu_dict[menu]
        print('menu_command', command)
        if not hot_key:
            menu_.addCommand(label, str(command))
        else:
            menu_.addCommand(label, command, hot_key)

    @staticmethod
    def find_menu_by_name(parent, menu_name):
        return menu_name

    def delete_menu(self, menu_name):
        menu_ = self.find_menu_by_name(self.menu_parent, menu_name)
        if menu_:
            print('deleting nuke menu %s' % menu_name)



