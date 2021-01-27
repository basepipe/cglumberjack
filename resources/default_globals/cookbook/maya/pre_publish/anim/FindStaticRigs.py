from cgl.plugins.preflight.preflight_check import PreflightCheck
import os
import cgl.plugins.maya.tasks.lay as lay
reload(lay)
import cgl.plugins.maya.lumbermill as lm
import cgl.plugins.maya.utils as utils
import cgl.plugins.maya.tasks.mdl as mdl

import pymel.core as pm


class FindStaticRigs(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        """
        script to be executed when the preflight is run.

        If the preflight is successful:
        self.pass_check('Message about a passed Check')

        if the preflight fails:
        self.fail_check('Message about a failed check')
        :return:
        """
        rigs = lay.find_static_rigs()
        if rigs:
            for each in rigs:
                print(each)
                pm.select(d=True)
                pm.select(each)
                self.fix_static_present()
                pm.hide(each)
        self.pass_check('No Static Rigs in Scene')
        # self.fail_check('Check Failed')

    @staticmethod
    def fix_static_present():
        """
        This is very particular to the 2020 thesis film and a fix for the rigged presents.
        :return:
        """
        this = utils.get_selected_reference()
        print(this, 2)
        scale_node = utils.select_reference(this[-1][-1])
        source_scale = pm.getAttr('{}.s'.format(scale_node))
        transform_node = utils.select_reference(this[-1][-1]).replace('rig', 'high')
        path = this[-1][-1].path

        if 'rig' in str(path):
            mdl_obj = lm.LumberObject(str(path)).copy(task='mdl', context='render', latest=True, user='publish',
                                                      set_proper_filename=True)
            if os.path.exists(mdl_obj.path_root):
                new_ref = lm.reference_file(mdl_obj.path_root)
                new_ref_node = utils.select_reference(new_ref)
                mdl.snap_to(new_ref_node, transform_node)
                pm.setAttr('{}.s'.format(new_ref_node), source_scale)
