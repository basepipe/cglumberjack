import plugins.nuke.bin.preflight as preflight
import nuke
from cgl.ui.widgets.dialog import InputDialog

def run():
	if nuke.selectedNodes():
		print 'found selected'
		if nuke.selectedNodes()[0].Class() == 'Write':
			print 'launching preflight'
			preflight.launch_('render')
			return
	print 'seinding dialog'
	dialog = InputDialog(message='Please Select a Valid Write Node to Render')
	dialog.exec_()




