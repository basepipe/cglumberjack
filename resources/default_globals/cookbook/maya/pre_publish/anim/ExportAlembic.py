import os
from cgl.plugins.preflight.preflight_check import PreflightCheck
from cgl.plugins.maya.utils import load_plugin
from cgl.plugins.maya.lumbermill import LumberObject, scene_object
from cgl.ui.widgets.dialog import InputDialog
import cgl.plugins.maya.tasks.anim as anim_task
import pymel.core as pm
import maya.mel

load_plugin('AbcImport')


class ExportAlembic(PreflightCheck):

    sframe = int(pm.playbackOptions(query=True, animationStartTime=True))
    eframe = int(pm.playbackOptions(query=True, animationEndTime=True))

    def getName(self):
        pass

    def run(self):
        pass_check = False
        if pm.objExists('ANIM'):
            relatives = pm.listRelatives('ANIM', children=True)
            if not relatives:
                self.pass_check('No Animation In Scene')
                return
            else:
                for each in relatives:
                    asset_name = each.split(':')[0]
                    try:
                        path = pm.referenceQuery(each, filename=True, wcn=True)
                    except RuntimeError:
                        # are we dealing with a bundle?
                        try:
                            # this is an exception made for animated bundles on the 2020 senior thesis.
                            path = pm.getAttr(pm.PyNode(each).BundlePath)
                        except AttributeError:
                            print('{} is not a reference or a bundle, exiting'.format(each))
                    asset_object = LumberObject(path)
                    asset_name = asset_object.shot
                    cat_name = asset_object.seq
                    name_ = '%s_%s.abc' % (cat_name, asset_name)
                    abc_export_path = scene_object().copy(context='render', filename=name_).path_root
                    if os.path.exists(abc_export_path):
                        abc_export_path.replace(name_, '%sa')
                    print "Exporting : %s" % abc_export_path
                    # with rigs, i only want the mdl, so i'm setting that here.
                    if pm.objExists(each.replace(':rig', ':mdl')):
                        anim_task.export_abc(abc_export_path, each.replace(':rig', ':mdl'))
                    else:
                        self.fail_check('Cant find %s>%s>%s' % (each,
                                                                each.replace(':rig', ':geo'),
                                                                each.replace(':rig', ':mdl')))
                        return
                    pass_check = True
                if pass_check:
                    self.pass_check('Passed Exporting Animation')
                else:
                    dialog = InputDialog(title='No Animation Found', message="No Animation Found, only cameras and layouts "
                                                                             "will be updated.  Correct?",
                                         buttons=['No', 'Yes Publish it!'])
                    dialog.exec_()
                    if dialog.button == 'Yes Publish it!':
                        self.pass_check('Animation Publish Successful, publishing no animation.')
                    else:
                        self.fail_check('No animation exported')
        else:
            self.fail_check('No ANIM Group was found')



if __name__ == "__main__":
    pass
