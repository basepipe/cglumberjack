from plugins.preflight.preflight_check import PreflightCheck


class CreateHdMovie(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        process_info = self.shared_data['publish_path_object'].make_preview()
        self.shared_data['job_id'] = process_info['job_id']
        self.pass_check('Check Passed: Movie Created!')
        # self.fail_check('Check Failed')

