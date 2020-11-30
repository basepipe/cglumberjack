from cgl.plugins.houdini.tasks.smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
import hou


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.houdini.lumbermill import scene_object
            self.path_object = scene_object()

    def build(self):
        task = 'mdl'

        if object_exists(task):
            pass
        else:
            create_material_groups()


def object_exists(object, path=None):
    if not path:
        path = 'obj/'

    object = hou.node('{}/{}'.format(path, object))
    if object:
        return True

    else:
        return False


def create_high_group(materials, node=None):
    if not node:
        node = hou.node('obj')
    for m in materials:
        print('selecting material : {}'.format(m))
        mtrl_group = node.createNode('group', m)
        null = node.createNode('null', m.replace('_mtl', '_null'))
        mtrl_group.setInput(0, null)

    node.layoutChildren()

    print('creating group High')


def create_object(name, path=None):
    if not path:
        path = 'obj/'
    object = hou.node('obj/').createNode('geo', name)
    return object


def create_mdl_group(res='high', path=None):
    if not path:
        path = 'obj/'
    hou.node('obj/').createNode('geo', 'mdl')


def create_material_groups(do_high=True, do_mdl=True, asset_name=None):
    """TODO: what is the purpose of do high vs do mdl"""
    from cgl.plugins.houdini.lumbermill import scene_object
    asset_name = scene_object().asset
    dialog_ = hou.ui.readInput(title='Create Material Groups',
                               message='list materials needed in this object (comma seperated)',
                               buttons=('Create Materials', 'Cancel'),
                               help='ex: wood, metal')

    if dialog_[0] == 0:
        list_ = dialog_[1].split(',')
        cleaned_list = []
        for each in list_:
            each = each.replace(' ', '')
            each = '%s_mtl' % each
            cleaned_list.append(each)

        for c in cleaned_list:
            print('creating group {}'.format(c))

        object = create_object(asset_name)

        if do_high:
            create_high_group(cleaned_list, node=object)

            hou.ui.displayMessage(title='Success!', text='Your model hierarchy has been created\n'
                                                         'please move all objects into their proper *_mtl '
                                                         'groups')
