from .smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
import pymel.core as pm
import maya.cmds as cmds


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.maya.alchemy import scene_object
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


def snap_to_origin(sel=None):
    if not sel:
        sel = pm.ls(sl=True)[0]
    loc = pm.spaceLocator()
    snap_to(sel, loc)
    pm.delete(loc)


def snap_to(a=None, b=None, pretransform=None, prerotation=None):
    """
    snaps object a to object b
    :return:
    """
    if not b:
        sel = pm.ls(sl=True)
        if len(sel) != 2:
            pm.windows.confirmDialog(title='Select Error',
                                     message='Please select 2 asset',
                                     button=['Ok'])
        else:
            b = sel[1]
            a = sel[0]
    point = pm.pointConstraint(b, a)
    orient = pm.orientConstraint(b, a)
    pm.delete(point)
    pm.delete(orient)

    if prerotation:
        axi = ['X', 'Y', 'Z']
        for rval, axis in enumerate(axi):
            rcurrent = pm.getAttr('%s.rotate%s' % (a, axis))
            pm.setAttr('%s.rotate%s' % (a, axis), (rcurrent-prerotation[rval]))
            tcurrent = pm.getAttr('%s.translate%s' % (a, axis))
            pm.setAttr('%s.translate%s' % (a, axis), (tcurrent - pretransform[rval]))


def delete_history(name=None):
    if name:
        pm.select(name)
    else:
        name = pm.ls(sl=True)
        if not name:
            print 'Nothing Selected, and no object given, skipping Delete History'
            return
    pm.delete(all=True, constructionHistory=True)


def freeze_transforms(name=None):
    if name:
        pm.select(name)
    else:
        name = pm.ls(sl=True)
        if not name:
            print 'Nothing Selected, and no object given, skipping Delete History'
            return
    pm.runtime.FreezeTransformations()


def create_bounding_box_cube(obj):
    """
    creates a cube int he same proportions as the bounding box of the object.
    :return:
    """
    if ':' in obj:
        name = obj.split(':')[0]
    else:
        name = obj
    name = '{}_proxy_anim'.format(name)
    pm.select(obj)
    sel = pm.ls(sl=True)
    x1, y1, z1, x2, y2, z2 = cmds.exactWorldBoundingBox(sel, calculateExactly=True)
    cube = cmds.polyCube(name=name)[0]
    snap_to(cube, obj)
    cmds.move(x1, '%s.f[5]' % cube, x=True)
    cmds.move(y1, '%s.f[3]' % cube, y=True)
    cmds.move(z1, '%s.f[2]' % cube, z=True)
    cmds.move(x2, '%s.f[4]' % cube, x=True)
    cmds.move(y2, '%s.f[1]' % cube, y=True)
    cmds.move(z2, '%s.f[0]' % cube, z=True)
    pm.select(d=True)
    return cube


def disconnect_attrs(obj, tx=False, ty=False, tz=False, rx=False, ry=False, rz=False, sx=False, sy=False, sz=False):
    """
    if you only give this function the object, it will disconnect ALL attributes. otherwise it will disconnect
    the attrs set to True.
    :param obj:
    :param tx:
    :param ty:
    :param tz:
    :param rx:
    :param ry:
    :param rz:
    :param sx:
    :param sy:
    :param sz:
    :return:
    """
    if not tx and not ty and not tz and not rx and not ry and not rz and not sx and not sy and not sz:
        tx = True
        ty = True
        tz = True
        rx = True
        ry = True
        rz = True
        sx = True
        sy = True
        sz = True
    if tx:
        pm.disconnectAttr('{}.tx'.format(obj))
    if ty:
        pm.disconnectAttr('{}.ty'.format(obj))
    if tz:
        pm.disconnectAttr('{}.tz'.format(obj))
    if rx:
        pm.disconnectAttr('{}.rx'.format(obj))
    if ry:
        pm.disconnectAttr('{}.ry'.format(obj))
    if rz:
        pm.disconnectAttr('{}.rz'.format(obj))
    if sx:
        pm.disconnectAttr('{}.sx'.format(obj))
    if sy:
        pm.disconnectAttr('{}.sy'.format(obj))
    if sz:
        pm.disconnectAttr('{}.sz'.format(obj))
