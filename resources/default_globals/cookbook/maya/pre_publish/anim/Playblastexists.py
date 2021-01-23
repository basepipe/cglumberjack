from cgl.plugins.preflight.preflight_check import PreflightCheck
import cgl.plugins.maya.lumbermill as lm
import cgl.plugins.maya.utils as utils


class Playblastexists(PreflightCheck):

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
        if utils.playblast_exists(lm.scene_object()):
            self.pass_check('Playblast Exists!')
            return
        else:
            utils.basic_playblast(lm.scene_object())
            self.pass_check('Created new Playblast!')
            return
        self.fail_check('No Playblast exists')
