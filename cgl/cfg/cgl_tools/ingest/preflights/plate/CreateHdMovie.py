from plugins.preflight.preflight_check import PreflightCheck
from cgl.core.convert import create_mov
from cgl.core.config import UserConfig


METHODOLOGY = UserConfig().d['methodology']


class CreateHdMovie(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        create_mov(self.shared_data['hdProxy']['file_out'], dependent_job=self.shared_data['hdProxy']['job_id'],
                   methodology=METHODOLOGY)
        self.pass_check('Check Passed: Movie Created!')
        # self.fail_check('Check Failed')

