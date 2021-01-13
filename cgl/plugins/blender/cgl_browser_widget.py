import os
from cgl.apps.lumbermill.main import CGLumberjackWidget


class BrowserWidget(CGLumberjackWidget):
    def __init__(self, parent=None,
                 project_management=None,
                 user_email=None,
                 company=None,
                 path=None,
                 radio_filter=None,
                 show_import=True,
                 show_reference=True):
        super(BrowserWidget, self).__init__(parent=parent,
                                            project_management=project_management,
                                            user_email=user_email,
                                            company=company,
                                            path=path,
                                            radio_filter=radio_filter,
                                            show_import=True,
                                            show_reference=True)


    def open_clicked(self):
        """
        Re-implementation of the open_clicked function in alchemy.  This allows us to customize it to
        this app's specific needs
        :return:
        """
        from cgl.plugins.blender.alchemy import open_file
        selection = self.path_widget.path_line_edit.text()
        if os.path.exists(selection):
            open_file(selection)
        else:
            logging.info('{0} does not exist!'.format(selection))

    def import_clicked(self):
        """
        Re-implemenation of the import_clicked function in alchemy.  This allows us to customize it to
        this app's specific needs.  Typically the default will work if you've defined the import_file() function
        in this plugin.
        :return:
        """
        from cgl.plugins.blender.alchemy import import_file, PathObject
        from cgl.core.path import PathObject
        selection = self.path_widget.path_line_edit.text()
        path_object = PathObject(selection)
        if os.path.exists(selection):
            import_file(selection, namespace=path_object.asset)
        else:
            logging.info('{0} does not exist!'.format(selection))
        # close alchemy.
        # self.parent().parent().accept()

    def reference_clicked(self):
        """
        Re-implemenation of the reference_clicked function in alchemy.  This allows us to customize it to
        this app's specific needs.  Typically the default will work if you've defined the reference_file() function
        in this plugin.
        :return:
        """
        print('reference clicked! Referencing not yet implemented in Blender.')
        from cgl.plugins.blender.alchemy import reference_file
        from cgl.core.path import PathObject
        selection = self.path_widget.path_line_edit.text()
        path_object = PathObject(selection)
        if os.path.exists(selection):
            reference_file(selection, namespace=path_object.asset)
        else:
            logging.info('{0} does not exist!'.format(selection))
        # selection = self.path_widget.path_line_edit.text()
        # if os.path.exists(selection)::
        #     reference_file(selection, namespace=None)
        # else:
        #     logging.info('{0} does not exist!'.format(selection))
        ## close alchemy
        # self.parent().parent().accept()