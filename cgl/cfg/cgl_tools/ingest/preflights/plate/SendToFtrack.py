from plugins.preflight.preflight_check import PreflightCheck
from cgl.core.config import UserConfig


PROCESSING_METHOD = UserConfig().d['methodology']


class SendToFtrack(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        if PROCESSING_METHOD == 'smedge':
            self.shared_data['publish_path_object'].upload_review(job_id=self.shared_data['job_id'])
            self.pass_check('Check Passed: Movie Upload Submitted!')
        elif PROCESSING_METHOD == 'local':
            self.shared_data['publish_path_object'].upload_review()
            self.pass_check('Skipping push to ftrack with local publish!')
        # self.pass_check('Check Passed')
        # self.fail_check('Check Failed')

