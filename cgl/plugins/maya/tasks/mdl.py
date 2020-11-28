from .smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
import pymel.core as pm


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.maya.lumbermill import scene_object
            self.path_object = scene_object()

    def build(self):
        task = 'mdl'
        pm.select(cl=True)
        if pm.objExists(task):
            print('mdl already exists')
            pass
        else:
            create_material_groups()


def create_high_group(materials):
    pm.select(cl=True)
    for m in materials:
        pm.select(m, tgl=True)
    pm.group(name='high')


def create_mdl_group(res='high'):
    pm.select(cl=True)
    pm.select(res)
    pm.group(name='mdl')


def create_material_groups(do_high=True, do_mdl=True):
    dialog_ = InputDialog(title='Create Material Groups',
                          message='list materials needed in this object (comma seperated)', line_edit=True,
                          regex='^([a-z]{3,}, *)*[a-z]{3,}', name_example='ex: wood, metal')
    dialog_.exec_()

    if dialog_.button == 'Ok':
        list_ = dialog_.line_edit.text().split(',')
        cleaned_list = []
        for each in list_:
            each = each.replace(' ', '')
            each = '%s_mtl' % each
            cleaned_list.append(each)
        for c in cleaned_list:
            pm.select(cl=True)
            pm.group(name=c)
        if do_high:
            create_high_group(cleaned_list)
            if do_mdl:
                create_mdl_group()
                pm.select(cl=True)
                dialog2 = InputDialog(title='Success!', message='Your model hierarchy has been created\n'
                                                                'please move all objects into their proper *_mtl groups')
                dialog2.exec_()

