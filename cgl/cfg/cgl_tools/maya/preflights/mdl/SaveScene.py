from cgl.plugins.preflight.preflight_check import PreflightCheck
from cgl.plugins.maya import alchemy


class SaveScene(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        alchemy.save_file()
        self.pass_check('Current Version Saved, Check Passed')


