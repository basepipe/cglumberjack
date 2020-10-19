import re
import pymel.core as pm
import maya.mel as mel
from cgl.ui.widgets.dialog import InputDialog


def get_namespace(filepath):
    from lumbermill import MayaPathObject
    po = MayaPathObject(filepath)
    if po.task == 'cam':
        namespace = 'cam'
    elif po.scope == 'assets':
        namespace = po.shot
    elif po.scope == 'shots':
        namespace = 'tempNS'
    return get_next_namespace(namespace)


def get_next_namespace(ns):
    pattern = '[0-9]+'
    next = False
    sel = pm.listReferences(namespaces=True)
    latest = 0
    for ref in sel:
        if ns in ref[0]:
            num = re.findall(pattern, ref[0])
            if num:
                if int(num[-1]) > latest:
                    latest = int(num[-1])
                    next = True
    if next:
        return '%s%s' % (ns, latest + 1)
    else:
        return ns


def get_shape_name(geo):
    if 'shape' in pm.general.nodeType(geo, i=True):
        return str(geo)
    else:
        shapes = pm.listRelatives(geo, shapes=True)
        return shapes[0]


def create_tt(length, tt_object):
    """
    Creates a turntable with frame range of 0-length, around the selected object.
    :param length: 
    :param tt_object: 
    :return: 
    """
    if not pm.objExists('turntable'):
        if pm.objExists(tt_object):
            cam = pm.camera(n='turntable_camera')[0]
            cam_shape = get_shape_name(cam)
            pm.setAttr('%s.focalLength' % cam_shape, 90)
            pm.select(d=True)
            pm.group(n='turntable')
            pm.parent(tt_object, 'turntable')
            center = pm.objectCenter('turntable', gl=True)
            pm.move('turntable_camera1', center)

            pm.playbackOptions(maxTime=length, animationEndTime=length)
            pm.animation.setKeyframe('turntable', v=0, t=-1, itt='linear', ott='linear', at='rotateY')
            pm.animation.setKeyframe('turntable', v=360, t=length, itt='linear', ott='linear', at='rotateY')

            mel.eval('lookThru turntable_camera1 perspView;')
            pm.viewFit(tt_object)
            # correction
            transform = cam.getTranslation()
            transform[2] = transform[2] * 1.5
            pm.move('turntable_camera1', transform)
            pm.grid(toggle=False)
            # attach a blin shader
    else:
        confirm_prompt(title='Turntable Exists',
                       message='Turntable already exists, \ntry the "Clean TT" button before running it again')


def clean_tt(task=None):
    if not task:
        task = 'mdl'
    check_group = pm.objExists('turntable')
    check_cam = pm.objExists('turntable_cam*')
    if check_group or check_cam:
        if check_cam:
            pm.delete('turntable_camera1')
        if check_group:
            children = pm.listRelatives('turntable')
            for child in children:
                pm.parent(child, w=True)
            pm.delete('turntable')
        mel.eval('lookThru persp perspView;')
        if pm.objExists(task):
            pm.viewFit(task)
        pm.grid(toggle=True)


def get_current_camera():
    panel = pm.getPanel(wf=True)
    if panel in pm.getPanel(type='modelPanel'):
        cam = pm.modelPanel(panel, q=True, camera=True)
        return cam
    else:
        confirm_prompt(title='Playblast', message='Please select window of the camera you want to playblast',
                       button='Ok')
        return None


def confirm_prompt(title='title', message='message', button='Ok'):
    """
    standard confirm prompt, this is an easy wrapper that allows us to do
    confirm prompts in the native language of the application while keeping conventions
    :param title:
    :param message:
    :param button: single button is created with a string, multiple buttons created with array
    :return:
    """
    pm.confirmDialog(title=title, message=message, button=button)


def load_plugin(plugin_name):
    if not pm.system.pluginInfo(plugin_name, query=True, loaded=True):
        pm.system.loadPlugin(plugin_name)


def basic_playblast(path_object, appearance='smoothShaded', cam=None, audio=False):
    scene = pm.sceneName()
    pm.select(cl=True)
    playblast_file = path_object.copy(context='render', filename='playblast', ext='').path_root
    if not cam:
        cam = get_current_camera()
    editor = pm.getPanel(wf=True)
    pm.modelEditor(editor, edit=True, displayAppearance=appearance, camera=cam)
    # TODO - make this source something from globals for the resolution
    w, h = path_object.proxy_resolution.split('x')
    w = int(w)
    h = int(h)

    # set proper attributes
    pm.setAttr('defaultRenderGlobals.imageFormat', 8)
    # run the playblast
    if not audio:
        pm.refresh(su=True)
        pm.playblast(filename=playblast_file, forceOverwrite=True, framePadding=4, p=100, w=w, h=h,
                     format='image', os=True)
        pm.refresh(su=False)
    else:
        print('Playblast not set up for audio yet')

