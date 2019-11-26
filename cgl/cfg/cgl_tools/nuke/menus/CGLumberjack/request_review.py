from cgl.ui.widgets.dialog import InputDialog
import plugins.nuke.cgl_nuke as cgl_nuke


def run():
    write_nodes = cgl_nuke.write_node_selected()
    if write_nodes:
        write_node = write_nodes[0]
        if write_node:
            print write_node['file'].value()
            render_object = cgl_nuke.NukePathObject(write_node['file'].value())
            render_object.upload_review()
    else:
        dialog = InputDialog(message='Please select a Valid Write Node for Review')
        dialog.exec_()
