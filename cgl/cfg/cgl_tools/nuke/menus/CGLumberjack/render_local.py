import plugins.nuke.bin.preflight as preflight
import nuke
from cgl.ui.widgets.dialog import InputDialog


def run():
	if nuke.selectedNodes():
		if nuke.selectedNodes()[0].Class() == 'Write':
			preflight.launch_('render')
			return
	dialog = InputDialog(message='Please Select a Valid Write Node to Render')
	dialog.exec_()



