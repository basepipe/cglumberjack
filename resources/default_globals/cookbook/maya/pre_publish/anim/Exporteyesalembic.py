from cgl.plugins.preflight.preflight_check import PreflightCheck
import pymel.core as pm
import cgl.plugins.maya.tasks.anim as anim_task
import cgl.plugins.maya.lumbermill as lm
import cgl.plugins.maya.msd as msd
# there is typically a lumbermill.py, and utils.py file in the plugins directory.
# look here for pre-built, useful functions
# from cgl.plugins.SOFTWARE import lumbermill


class Exporteyesalembic(PreflightCheck):

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

        eye_stuff = self.george_eye_stuff() + self.jennifer_eye_stuff()
        for each in eye_stuff:
            pm.select(d=True)
            pm.select(each)
            new_name = each.replace(':', '_').replace('|', '_')
            abc_export_path = lm.scene_object().copy(context='render', filename='{}.abc'.format(new_name)).path_root
            ref_path = pm.referenceQuery(each, filename=True)
            # get the reference of this
            anim_task.export_abc(abc_export_path, each)
            msd.MagicSceneDescription(single_asset=each, single_asset_name=new_name,
                                      single_asset_path=ref_path, single_asset_type='anim').export()
        self.pass_check('Eyes ABC exported!')


    @staticmethod
    def george_eye_stuff():
        eye_stuff = pm.ls('george*:eye*_rig')
        return eye_stuff


    @staticmethod
    def jennifer_eye_stuff():
        jenn_eye_lashes = pm.ls('jenn*:*eyelash')
        jenn_eyes = pm.ls('jenn*:*_eye')
        jenn_eyebrows = pm.ls('jenn*:*_eyebrow')
        jenn_eye_stuff = jenn_eye_lashes + jenn_eyes + jenn_eyebrows
        return jenn_eye_stuff

