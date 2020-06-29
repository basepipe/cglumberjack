from plugins.CustomMenu import CustomMenu


class LumberMenu(CustomMenu):
    def __init__(self, software='maya', type_='shelves'):
        CustomMenu.__init__(self, software, type_)

    def get_scene_path(self):
        """
        gets the current scene path
        :return:
        """
        pass

    def create_menu(self, name):
        """
        creates a menu with title of 'name'
        :param name:
        :return:
        """
        pass

    def set_menu_parent(self):
        """
        set the parent of a menu
        :return:
        """
        pass

    def add_button(self, menu, label='', annotation='', command='', icon='', image_overlay_label=''):
        """
        add a button to a menu
        :param shelf:
        :param label:
        :param annotation:
        :param command:
        :param icon:
        :param image_overlay_label:
        :return:
        """
        pass

    @staticmethod
    def find_menu_by_name(parent, menu_name):
        """
        finds menu in software package given its string name
        :param parent:
        :param menu_name:
        :return:
        """
        pass

    def delete_menu(self, menu_name):
        """
        deletes menu by "menu_name"
        :param shelf_name:
        :return:
        """
        pass



