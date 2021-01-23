from plugins.preflight.preflight_check import PreflightCheck


class cgl_tools.ingest.pre_publish.default.MarkAsPublished(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        print 'cgl_tools.ingest.pre_publish.default.MarkAsPublished'
        # self.pass_check('Check Passed')
        # self.fail_check('Check Failed')

