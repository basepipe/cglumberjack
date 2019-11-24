from plugins.preflight.preflight_check import PreflightCheck


class SendToFtrack(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        self.shared_data['publish_path_object'].upload_review(job_id=self.shared_data['job_id'])
        self.pass_check('Check Passed: Movie Created!')
        # self.pass_check('Check Passed')
        # self.fail_check('Check Failed')

