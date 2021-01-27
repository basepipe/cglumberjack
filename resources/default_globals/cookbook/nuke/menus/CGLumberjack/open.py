from cgl.plugins.nuke import gui


def run():
	dialog = gui.CGLNukeWidget()
	dialog.exec_()
