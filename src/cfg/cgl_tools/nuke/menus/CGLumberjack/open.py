import sys
import os
import yaml


def run():
	source_dir = r"C:\Users\tmiko\PycharmProjects\cglumberjack\src"
	sys.path.insert(0, source_dir)
	import plugins.nuke.gui as gui

	gui.launch()
	print 'test'
