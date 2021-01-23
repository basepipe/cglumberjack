from plugins.preflight.preflight_check import PreflightCheck


class MarkAsPublished(PreflightCheck):

    def getName(self):
        pass

    def run(self):
        if self.shared_data['selected_rows']:
            self.selected_row = self.shared_data['selected_rows'][0]
            self.shared_data['file_tree'].set_text(self.selected_row, 12, 'Published')
            self.pass_check('Check Passed')
        else:
            self.fail_check('Selection Not Readable in Preflight, Setting Text to Publish failed')

