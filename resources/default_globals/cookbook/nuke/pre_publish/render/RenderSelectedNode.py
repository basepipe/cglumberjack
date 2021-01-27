from plugins.preflight.preflight_check import PreflightCheck
import plugins.nuke.cgl_nuke as cgl_nuke


class RenderSelectedNode(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        path_object = cgl_nuke.NukePathObject()
        process_info_list = path_object.render(selected=True)
        self.shared_data['job_id'] = process_info_list[0]['job_id']
        self.shared_data['render_path_object'] = cgl_nuke.NukePathObject(process_info_list[0]['file_out'])
        self.pass_check('Check Passed')

