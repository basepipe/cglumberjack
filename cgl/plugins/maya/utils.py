import re
import os
from cgl.core.config import app_config
from cgl.core.utils.read_write import load_json
from cgl.ui.widgets.dialog import MagicList

try:
    import pymel.core as pm
    import maya.mel as mel
    import mtoa.core as aicore
    import maya.cmds as cmds
except ModuleNotFoundError:
    print('Skipping pymel.core - outside of maya')


CONFIG = app_config()


def get_namespace(filepath):
    from lumbermill import LumberObject
    namespace = ''
    path_object = LumberObject(filepath)
    if path_object.task == 'cam':
        namespace = 'cam'
    elif path_object.scope == 'assets':
        namespace = path_object.shot
    elif path_object.scope == 'shots':
        namespace = 'tempNS'
    return get_next_namespace(namespace)


def get_selected_namespace():
    """
    returns namespace of selected object.
    :return:
    """
    namespace = pm.ls(sl=True)[0]
    if namespace:
        return namespace.split(':')[0]


def select_reference(ref_node):
    # This assumes we're talking about a published reference
    object_ = pm.ls(regex='%s:[a-z]{3}|%s:CAMERAS' % (ref_node.namespace, ref_node.namespace))[0]
    pm.select(object_)
    return object_


def get_next_namespace(ns):
    pattern = '[0-9]+'
    exists = False
    namespaces = pm.namespaceInfo(listNamespace=True)
    latest = 0
    for ref in namespaces:
        if ns in ref:
            exists = True
            num = re.findall(pattern, ref)
            if num:
                if int(num[-1]) > latest:
                    latest = int(num[-1])
    if exists:
        return '%s%s' % (ns, latest + 1)
    else:
        return '%s' % ns


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


def get_hdri_json_path():
    hdri_json = CONFIG['paths']['resources']
    return os.path.join(hdri_json, 'hdri', 'settings.json')


def hdri_widget():
    d = load_json(get_hdri_json_path())
    window = pm.window()
    pm.columnLayout()
    pm.optionMenu(label='Colors', changeCommand=create_env_light)
    for each in d.keys():
        pm.menuItem(label=each)
    pm.showWindow(window)


def create_env_light(tex_name):
    d = load_json(get_hdri_json_path())
    rotation = 0
    delete_existing = True
    rotate_set = False
    rotate_ = None

    for key in d:
        if key in tex_name:
            rotate_ = d[key]
            rotate_set = True
    if rotate_set:
        rotation = rotate_
    if delete_existing:
        env_lights = pm.ls('env_light*', type='transform')
        pm.delete(env_lights)
    tex_path = r'Z:\Projects\VFX\PLUGINS\substance_painter\ibl\%s.tx' % tex_name
    tex_path2 = r'Z:\Projects\VFX\PLUGINS\substance_painter\ibl\%s.exr' % tex_name
    if not os.path.exists(tex_path):
        if os.path.exists(tex_path2):
            command = '%s %s -v -u -oiio -o %s' % (CONFIG['paths']['maketx'], tex_path2, tex_path)
            # should probably run the txmake command here and make the .tx file.
            p = subprocess.Popen(command, shell=True)
            p.communicate()
        else:
            print('Can not find file: %s' % tex_path2)
            return
    skydome = aicore.createArnoldNode('aiSkyDomeLight', name='env_lightShape')
    file_node = pm.shadingNode('file', asTexture=True, isColorManaged=True)
    place_tex = pm.shadingNode('place2dTexture', asUtility=True)
    pm.connectAttr(place_tex.coverage, file_node.coverage, force=True)
    pm.connectAttr(place_tex.translateFrame, file_node.translateFrame, force=True)
    pm.connectAttr(place_tex.rotateFrame, file_node.rotateFrame, force=True)
    pm.connectAttr(place_tex.mirrorV, file_node.mirrorV, force=True)
    pm.connectAttr(place_tex.stagger, file_node.stagger, force=True)
    pm.connectAttr(place_tex.wrapU, file_node.wrapU, force=True)
    pm.connectAttr(place_tex.wrapV, file_node.wrapV, force=True)
    pm.connectAttr(place_tex.repeatUV, file_node.repeatUV, force=True)
    pm.connectAttr(place_tex.offset, file_node.offset, force=True)
    pm.connectAttr(place_tex.rotateUV, file_node.rotateUV, force=True)
    pm.connectAttr(place_tex.noiseUV, file_node.noiseUV, force=True)
    pm.connectAttr(place_tex.vertexUvOne, file_node.vertexUvOne, force=True)
    pm.connectAttr(place_tex.vertexUvTwo, file_node.vertexUvTwo, force=True)
    pm.connectAttr(place_tex.vertexUvThree, file_node.vertexUvThree, force=True)
    pm.connectAttr(place_tex.vertexCameraOne, file_node.vertexCameraOne, force=True)
    pm.connectAttr(place_tex.outUV, file_node.uv)
    pm.connectAttr(place_tex.outUvFilterSize, file_node.uvFilterSize)
    pm.setAttr(file_node.fileTextureName, tex_path)
    pm.connectAttr(file_node.outColor, '%s.%s' % (skydome, 'color'), force=True)
    pm.setAttr('%s.rotateY' % skydome, rotation)
    print('rotation = %s' % rotation)


def get_maya_window():
    from maya import OpenMayaUI as omui
    from shiboken2 import wrapInstance
    from cgl.plugins.Qt import QtWidgets

    ptr = omui.MQtUtil.mainWindow()
    main_maya_window = None
    if ptr is not None:
        main_maya_window = wrapInstance(long(ptr), QtWidgets.QWidget)
    return main_maya_window


def update_reference(reference):
    from cgl.plugins.maya.lumbermill import LumberObject
    path = reference[1].path
    if '{' in path:
        path = path.split('{')[0]
    filename = os.path.basename(path)
    lobj = LumberObject(path).copy(context='render', user='publish', latest=True)
    latest_version = lobj.path_root
    path = path.replace('\\', '/')
    latest_version = latest_version.replace('\\', '/')
    if os.path.exists(latest_version):
        if path != latest_version:
            print('REPLACING REFERENCE: %s ---- %s' % (reference[0], latest_version))
            try:
                reference[1].replaceWith(latest_version)
                return 1
            except RuntimeError:
                return 0
                print('cannot load latest version %s ' % latest_version)
        else:
            return 0
    else:
        print('file: {} does not exist'.format(latest_version))
        return 0


def update_all_references():
    refs = pm.listReferences(refNodes=True)
    total_count = 0
    for ref in refs:
        updated = update_reference(ref)
        total_count += updated
    print('{} References updated'.format(total_count))
    return total_count


def get_selected_reference():
    """
    Returns a list of references representing the currently selected items.
    :return:
    """
    ns = None
    references = pm.listReferences(refNodes=True)
    selected = pm.ls(sl=True)
    if selected:
        reference_nodes = []
        for s in selected:
            if ':' in s:
                ns = s.split(':')[0]
                for r in references:
                    namespace_ = str(r[0].replace('RN', ''))
                    if ns == namespace_:
                        reference_nodes.append(r)
        if not reference_nodes:
            print("Could not find Namespace %s in references.  It's not in the scene, or there's a namespace error" % ns)
        return reference_nodes
    else:
        print('No Reference Selected, Select a Reference and Try again')
        return None


def remove_namespace(ns):
    try:
        children = pm.namespaceInfo(ns, listOnlyNamespaces=1)
        if children:
            for child in children:
                remove_namespace(child)
        pm.namespace(moveNamespace=(ns, ":"), f=1)
        pm.namespace(removeNamespace=ns)
    except RuntimeError:
        print('No namespace "{}" found'.format(ns))


def remove_all_namespaces():
    namespaces = get_namespaces()
    for ns in namespaces:
        remove_namespace(ns)


def get_namespaces():
    namespaces = pm.namespaceInfo(listOnlyNamespaces=1)
    if len(namespaces) == 2:
        return None
    else:
        pm.namespace(set=":")
        ns = []
        for name in namespaces:
            if name not in ('UI', 'shared'):
                ns.append(name)
        return ns


def is_reference(mesh=None, return_namespaces=False):
    refs = pm.listReferences(namespaces=True)
    scene_namespaces = ['PROP']
    for ref in refs:
        scene_namespaces.append(ref[0])
    if return_namespaces:
        return scene_namespaces
    ns = str(mesh).split(':')[0]
    if ns in scene_namespaces:
        return True
    else:
        return False









