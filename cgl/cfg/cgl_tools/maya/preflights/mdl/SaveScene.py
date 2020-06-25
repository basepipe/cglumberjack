from plugins.preflight.preflight_check import PreflightCheck
from cgl.plugins.maya import lumbermill


class SaveScene(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        lumbermill.save_file()
        self.pass_check('Current Version Saved, Check Passed')


