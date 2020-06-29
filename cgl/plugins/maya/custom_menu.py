from plugins.CustomMenu import CustomMenu
import pymel.core as pm
import maya.mel


class MayaCustomMenu(CustomMenu):
    def __init__(self, software='maya', type_='shelves'):
        CustomMenu.__init__(self, software, type_)

    def create_menu(self, name):
        """
        creates a menu with title of 'name'
        :param name:
        :return:
        """
        shelf = pm.shelfLayout(name, parent=self.menu_parent)
        return shelf

    def set_menu_parent(self):
        """
        set the parent of a menu
        :return:
        """
        name = maya.mel.eval('$tmpVar=$gShelfTopLevel')
        return pm.tabLayout(name, query=True, fullPathName=True)

    def add_button(self, shelf, label='', annotation='', command='', icon='', image_overlay_label=''):
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
        button_name = pm.shelfButton(image1=icon,
                                     parent=shelf,
                                     label=label,
                                     annotation=annotation,
                                     command=command,
                                     imageOverlayLabel=image_overlay_label)
        return button_name

    @staticmethod
    def find_menu_by_name(parent, menu_name):
        """
        finds menu in software package given its string name
        :param parent:
        :param menu_name:
        :return:
        """
        shelf_exists = pm.shelfLayout(menu_name, exists=True, parent=parent)
        shelf = None
        if shelf_exists:
            shelf = pm.shelfLayout(menu_name,
                                   query=True,
                                   fullPathName=True)
        return shelf

    def delete_menu(self, shelf_name):
        """
        deletes menu by "menu_name"
        :param shelf_name:
        :return:
        """
        shelf_ = self.find_menu_by_name(self.menu_parent, shelf_name)
        if shelf_:
            pm.deleteUI(shelf_)



