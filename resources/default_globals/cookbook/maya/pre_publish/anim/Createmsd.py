from cgl.plugins.preflight.preflight_check import PreflightCheck
import cgl.plugins.maya.msd as msd
import pymel.core as pm


class Createmsd(PreflightCheck):

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
        pm.select(d=True)
        msd.MagicSceneDescription().export()
        self.pass_check('Animation msd created')
