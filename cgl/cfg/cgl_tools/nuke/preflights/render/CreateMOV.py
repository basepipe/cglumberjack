from plugins.preflight.preflight_check import PreflightCheck
from cgl.core.path import PathObject
from cgl.core.config import UserConfig

PROCESSING_METHOD = UserConfig().d['methodology']


class CreateMOV(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        if PROCESSING_METHOD == 'local' or PROCESSING_METHOD == 'gui':
            process_info = self.shared_data['render_path_object'].make_preview(new_window=True)
        else:
            process_info = self.shared_data['render_path_object'].make_preview(job_id=self.shared_data['job_id'])

        self.shared_data['job_id'] = process_info['job_id']
        self.pass_check('Create MOV passed!')
        
        

