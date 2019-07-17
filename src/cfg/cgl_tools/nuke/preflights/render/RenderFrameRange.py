from plugins.preflight.preflight_check import PreflightCheck
import plugins.nuke.gui as gui


class RenderFrameRange(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        self.shared_data["render_paths"] = gui.render_all_write_nodes()
        print 'THIS:', self.shared_data["render_paths"]
        self.pass_check('Check Passed')

