import glob
import logging
import os
import hou
import getpass
import json
from cgl.core.path import PathObject
from cgl.core.config import app_config, UserConfig
from cgl.apps.lumbermill.main import CGLumberjack, CGLumberjackWidget
from cgl.plugins.Qt import QtCore, QtWidgets

CONFIG = app_config()
PROJ_MANAGEMENT = CONFIG['account_info']['project_management']
PADDING = CONFIG['default']['padding']
PROCESSING_METHOD = UserConfig().d['methodology']
SOFTWARE = os.path.basename(os.path.dirname(__file__))




class LumberObject(PathObject):

    def __init__(self, path_object=None):
        if not path_object:
            path_object = get_scene_name()
        self.data = {}
        self.root = CONFIG['paths']['root'].replace('\\', '/')
        self.company = None
        self.project = None
        self.scope = None
        self.context = None
        self.seq = None
        self.shot = None
        self.type = None
        self.asset = None
        self.variant = None
        self.user = None
        self.version = None
        self.major_version = None
        self.minor_version = None
        self.ext = None
        self.filename = None
        self.filename_base = None
        self.resolution = None
        self.frame = None
        self.aov = None
        self.render_pass = None
        self.shotname = None
        self.assetname = None
        self.task = None
        self.camera = None
        self.file_type = None
        self.frame_padding = CONFIG['default']['padding']
        self.scope_list = CONFIG['rules']['scope_list']
        self.context_list = CONFIG['rules']['context_list']
        self.path = None  # string of the properly formatted path
        self.path_root = None  # this gives the full path with the root
        self.thumb_path = None
        self.playblast_path = None
        self.render_path = None
        self.preview_path = None
        self.preview_seq = None
        self.hd_proxy_path = None
        self.start_frame = None
        self.end_frame = None
        self.frame_rate = None
        self.frame_range = None
        self.template = []
        self.filename_template = []
        self.actual_resolution = None
        self.date_created = None
        self.date_modified = None
        self.project_config = None
        self.company_config = None
        self.software_config = None
        self.asset_json = None
        self.shot_json = None
        self.task_json = None
        self.command_base = ''
        self.project_json = None
        self.status = None
        self.due = None
        self.assigned = None
        self.priority = None
        self.ingest_source = '*'
        self.processing_method = PROCESSING_METHOD
        self.proxy_resolution = '1920x1080'
        self.path_template = []
        self.version_template = []

        try:
            if isinstance(path_object, unicode):
                path_object = str(path_object)
        except NameError:
            pass
        if isinstance(path_object, dict):
            self.process_dict(path_object)
        elif isinstance(path_object, str):
            self.process_string(path_object)
        elif isinstance(path_object, PathObject):
            self.process_dict(path_object.data)
        else:
            logging.error('type: %s not expected' % type(path_object))
        self.set_render_paths()

    def set_render_paths(self):
        padding = '#' * self.frame_padding
        previewRenderTypes = ['anim', 'rig', 'mdl', 'lay', 'remsh', 'grmnt']

        if self.task in previewRenderTypes:
            render_path = self.copy(context='render', ext='jpg', set_proper_filename=True).path_root
            self.render_path = render_path.replace('.jpg', '.{}.jpg'.format(padding))
        else:
            render_path = self.copy(context='render', ext='exr', set_proper_filename=True).path_root
            self.render_path = render_path.replace('.exr', '.{}.exr'.format(padding))

def get_scene_name():
    """
    get current scene name
    :return:
    """

    return hou.hipFile.path()



def scene_object():
    """
    returns LumberObject of curent scene
    :return:
    """
    return LumberObject(get_scene_name())


def open_file(filepath):
    """
    Open File: filepath
    :param filepath:
    :return:
    """
    hou.hipFile.load(filepath)
    return filepath


def import_file(filepath='', namespace=None):
    """
    imports file into a scene.
    :param filepath:
    :return:
    """

    if filepath.endswith('fbx'):
        hou.hipFile.importFBX(filepath)
    elif filepath.endswith('hip') or filepath.endswith('hiplc'):
        hou.hipFile.merge(filepath)


def import_alembic(filepath='', namespace=None):
    """
    creates a "reference" of a file, this is a convenience function to be used in various software plugins
    to promote continuity accross plugins
    :param namespace:
    :param filepath:
    :return:
    """

    path_object = LumberObject(filepath)
    objects = hou.node('obj')

    alembic = objects.createNode('alembicarchive', path_object.asset)
    alembic.parm('alembicarchive').set(filepath)
    alembic.parm('buildHierarchy').pressButton()


def reference_file(filepath='', namespace=None):
    """
    creates a "reference" of a file, this is a convenience function to be used in various software plugins
    to promote continuity accross plugins
    :param namespace:
    :param filepath:
    :return:
    """
    print(filepath)

    path_object = LumberObject(filepath)
    objects = hou.node('obj')

    geometry = objects.createNode('geo', path_object.asset)
    fileParm = geometry.createNode('file')
    fileParm.parm('file').set(filepath)



def save_file(filepath=''):
    """
    Save Current File
    :param filepath:
    :return:
    """
    return hou.hipFile.save()


def save_file_as(filepath):
    """
    save current file as
    :param filepath:
    :return:
    """
    hou.hipFile.save(filepath)
    return filepath


def version_up(vtype='minor'):
    """
    versions up the current scene
    :param vtype: minor or major
    :return:
    """
    path_object = LumberObject(get_scene_name())
    if vtype == 'minor':
        new_version = path_object.new_minor_version_object()
    elif vtype == 'major':
        new_version = path_object.next_major_version()
    create_file_dirs(new_version.path_root)
    return save_file_as(new_version.path_root)

def create_file_dirs(file_path):
    """
    given file_path checks to see if directories exist and creates them if they don't.
    :param file_path: path to file you're about to create.
    :return:
    """
    dirname = os.path.dirname(file_path)
    if os.path.isdir(file_path):
        dirname = file_path
    print(dirname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def current_user():
    """
    find the currently logged in user
    Returns:
        str: username

    """
    return getpass.getuser().lower()

def review():
    from cgl.core.project import do_review
    playblast_seq = scene_object().copy(context='render', filename='playblast.####.jpg')
    if glob.glob(playblast_seq.path_root.replace('####', '*')):
        print('exists - reviewing')
        do_review(progress_bar=None, path_object=playblast_seq)



class BrowserWidget(CGLumberjackWidget):
    def __init__(self, parent=None, path=None,
                 show_import=False):
        super(BrowserWidget, self).__init__(parent=parent, path=path, show_import=show_import)

    def open_clicked(self):
        for selection in self.source_selection:
            base_, ext = os.path.splitext(selection)
            open_file(selection)
        print('Opening: %s' % self.path_object.path_root)

    def import_clicked(self):
        for selection in self.source_selection:
            base_, ext = os.path.splitext(selection)
            import_file(selection, namespace=None)
        self.parent().parent().accept()

    def reference_clicked(self):
        for selection in self.source_selection:
            base_, ext = os.path.splitext(selection)
            reference_file(selection, namespace=None)
        self.parent().parent().accept()


class AppMainWindow(CGLumberjack):
    def __init__(self, parent=None, path=None, user_info=None):
        CGLumberjack.__init__(self, parent, user_info=user_info, previous_path=path, sync_enabled=False)
        print('Application Path path is %s' % path)
        self.setCentralWidget(BrowserWidget(self, show_import=True, path=path))
        # self.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Window)


def launch():
    import hou
    main_window = AppMainWindow()
    main_window.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
    main_window.setWindowTitle('Magic Browser : Houdini')
    main_window.resize(1100, 1400)
    main_window.show()


def create_cam_constraint():
    if locals().get("hou_parent") is None:
        hou_parent = hou.node("/obj/turntable")

    # Code for /obj/turntable/constraints
    hou_node = hou_parent.createNode("chopnet", "constraints",
                                     run_init_scripts=False,
                                     load_contents=True,
                                     exact_type_name=True)
    hou_node.move(hou.Vector2(0.18, 1.5))
    hou_node.hide(False)
    hou_node.setSelected(True)

    hou_parm_template_group = hou.ParmTemplateGroup()
    # Code for parameter template
    hou_parm_template = hou.FloatParmTemplate("chopnet_rate",
                                              "CHOP Rate", 1,
                                              default_value=([24]),
                                              min=1, max=100,
                                              min_is_strict=True,
                                              max_is_strict=False,
                                              look=hou.parmLook.Regular,
                                              naming_scheme=hou.parmNamingScheme.Base1)
    hou_parm_template_group.append(hou_parm_template)

    # Code for parameter template
    hou_parm_template = hou.FloatParmTemplate("motionsamples", "CHOP Motion Samples", 1,
                                              default_value=([1]),
                                              min=1, max=20,
                                              min_is_strict=True, max_is_strict=False,
                                              look=hou.parmLook.Regular,
                                              naming_scheme=hou.parmNamingScheme.Base1)
    hou_parm_template_group.append(hou_parm_template)
    hou_node.setParmTemplateGroup(hou_parm_template_group)
    # Code for /obj/turntable/constraints/chopnet_rate parm
    if locals().get("hou_node") is None:
        hou_node = hou.node("/obj/turntable/constraints")
    hou_parm = hou_node.parm("chopnet_rate")
    hou_parm.deleteAllKeyframes()
    hou_parm.set(240)

    # Code for first keyframe.
    # Code for keyframe.
    hou_keyframe = hou.Keyframe()
    hou_keyframe.setTime(0)
    hou_keyframe.interpretAccelAsRatio(False)
    hou_keyframe.setExpression("$FEND", hou.exprLanguage.Hscript)
    hou_parm.setKeyframe(hou_keyframe)

    # Code for /obj/turntable/constraints/motionsamples parm
    if locals().get("hou_node") is None:
        hou_node = hou.node("/obj/turntable/constraints")
    hou_parm = hou_node.parm("motionsamples")
    hou_parm.deleteAllKeyframes()
    hou_parm.set(10)

    # Code for keyframe.
    hou_keyframe = hou.Keyframe()
    hou_keyframe.setTime(0)
    hou_keyframe.interpretAccelAsRatio(False)
    hou_keyframe.setExpression("$CHOPMOTIONSAMPLES", hou.exprLanguage.Hscript)
    hou_parm.setKeyframe(hou_keyframe)

    hou_node.setExpressionLanguage(hou.exprLanguage.Hscript)

    if hasattr(hou_node, "syncNodeVersionIfNeeded"):
        hou_node.syncNodeVersionIfNeeded("18.5.351")


def create_turntable(lenght=180):
    clean_turntable()
    selected_objects = hou.selectedNodes()

    if not selected_objects:
        hou.ui.displayMessage('please select an object')
        return

    selection = selected_objects[0]

    objs = hou.node('obj')
    turntable_null = objs.createNode('null', 'TurnTableNull')
    turntable_null.setPosition((selection.position()[0],
                                selection.position()[1] + 2))
    ry = turntable_null.parm('ry')
    ry.setExpression('fit($FF,1,{},0,360)'.format(lenght))
    hou.playbar.setPlaybackRange(1, lenght)

    selection.setInput(0, turntable_null)

    camera = objs.createNode('cam', 'TurnTableCam')
    camera.parm('tz').set(10)
    camera.setPosition((5, 0))


def create_turntable_around_object():
    import hou
    clean_turntable()

    selection = hou.selectedNodes()
    if not selection:
        hou.ui.displayMessage('please select an object')
        return

    objects = hou.node('obj/')

    cam = objects.createNode('cam', 'turntable')
    guide = objects.createNode('geo', 'turntable_guide')

    guide.setPosition((2, 0))
    circle = guide.createNode('circle')

    circle.parm('type').set(2)
    circle.parm('orient').set(2)
    circle.parm('arc').set(1)

    create_cam_constraint()

    cam.parm('constraints_on').set(True)
    cam.parm('constraints_path').set('constraints')

    constraints = cam.node('constraints')
    world_space = constraints.createNode('constraintgetworldspace')

    object_to_constraint = constraints.createNode('constraintobject')
    object_to_constraint.parm('obj_path').set('../../../{}'.format(selection[0].name()))

    follow_path = constraints.createNode('constraintpath', 'Follow_Path')
    follow_path.parm('pos').setExpression('$FF/$RFEND')
    follow_path.parm('soppath').set('/obj/turntable_guide')
    follow_path.setInput(0, world_space)
    follow_path.setInput(1, object_to_constraint)
    follow_path.setGenericFlag(hou.nodeFlag.Audio, 1)




def clean_turntable():
    import hou
    turntable_objects = ['turntable', 'turntable_guide','TurnTableCam','TurnTableNull']

    for obj in turntable_objects:
        node = hou.node('obj/{}'.format(obj))
        if node:
            node.destroy()

""""

publish()
render()
export_selected()
launch_preflight()
"""
