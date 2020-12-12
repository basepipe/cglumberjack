from .smart_task import SmartTask
import cgl.plugins.maya.lumbermill as lm
import cgl.plugins.maya.msd as msd
reload(msd)
import pymel.core as pm
import maya.mel


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.maya.lumbermill import scene_object
            self.path_object = scene_object()

    def build(self):
        """
        1. Reference the latest model for this asset
        2. Import latest textures for this asset (and assemble a shader network)
        :return:
        """
        lm.import_task(task='lay')
        lm.import_task(task='cam')

    def _import(self, filepath):
        if filepath.endswith('.msd'):
            print('parsing .msd {}'.format(filepath))
            msd.load_msd(filepath)

    def import_latest(self):
        """
        imports everything from latest animation publish as described in the .msd file.
        :return:
        """
        this_obj = lm.scene_object().copy(task='anim', context='render', user='publish', latest=True,
                                          set_proper_filename=True, ext='msd')
        self._import(this_obj.path_root)


def export_abc(file_out, geo, command_line=False):
    sframe = int(pm.playbackOptions(query=True, animationStartTime=True))
    eframe = int(pm.playbackOptions(query=True, animationEndTime=True))
    if command_line:
        command = [r'C:\Program Files\Autodesk\Maya2017\bin\mayapy.exe',
                   r'C:\Users\tmikota\PycharmProjects\core_tools\src\tools\maya\bakeGEO.py',
                   str(pm.sceneName()), file_out, str(geo)]
        print 'command line not yet implemented'
        # subprocess.Popen(command)
    else:
        command = 'AbcExport -j "-frameRange %s %s -step 0.5 -uvWrite -wholeFrameGeo -worldSpace -writeVisibility ' \
                  '-eulerFilter -writeUVSets -dataFormat ogawa -root %s -file %s"' % (sframe, eframe, geo, file_out)
        print command
        maya.mel.eval(command)


def copy_animation(from_object, to_object):
    copy_animated_attr(from_object, to_object, 'translateX')
    copy_animated_attr(from_object, to_object, 'translateY')
    copy_animated_attr(from_object, to_object, 'translateZ')
    copy_animated_attr(from_object, to_object, 'rotateX')
    copy_animated_attr(from_object, to_object, 'rotateY')
    copy_animated_attr(from_object, to_object, 'rotateZ')
    copy_animated_attr(from_object, to_object, 'scaleX')
    copy_animated_attr(from_object, to_object, 'scaleY')
    copy_animated_attr(from_object, to_object, 'scaleZ')


def copy_animated_attr(from_object, to_object, attr):
    if pm.copyKey(from_object, attribute=attr, option='curve'):
        pm.pasteKey(to_object, attribute=attr)
    else:
        aa = pm.getAttr('{}.{}'.format(from_object, attr))
        pm.setAttr('{}.{}'.format(to_object, attr), aa)
