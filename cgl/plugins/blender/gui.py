import bpy
import sys
import os
import logging
from PySide2 import QtWidgets, QtCore
from cgl.plugins.preflight.main import Preflight
from .lumbermill import scene_object

logger = logging.getLogger('qtutils')

# Special thanks to this website for providing this methodology:
# https://github.com/vincentgires/blender-scripts/tree/master/scripts/addons/qtutils


class QtWindowEventLoop(bpy.types.Operator):
    """Allows PyQt or PySide to run inside Blender"""

    bl_idname = 'screen.qt_event_loop'
    bl_label = 'Qt Event Loop'

    def __init__(self, widget, *args, **kwargs):
        self._widget = widget
        self._args = args
        self._kwargs = kwargs

    def modal(self, context, event):
        wm = context.window_manager
        try:
            if not self.widget.isVisible():
                # if widget is closed
                logger.debug('finish modal operator')
                wm.event_timer_remove(self._timer)
                return {'FINISHED'}
            else:
                logger.debug('process the events for Qt window')
                self.event_loop.processEvents()
                self.app.sendPostedEvents(None, 0)
        except RuntimeError:
            print('widget.isVisible() crashed, skipping')
            wm.event_timer_remove(self._timer)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        logger.debug('execute operator')

        self.app = QtWidgets.QApplication.instance()
        # instance() gives the possibility to have multiple windows
        # and close it one by one

        if not self.app:
            # create the first instance
            self.app = QtWidgets.QApplication(sys.argv)

        if 'stylesheet' in self._kwargs:
            stylesheet = self._kwargs['stylesheet']
            self.set_stylesheet(self.app, stylesheet)

        self.event_loop = QtCore.QEventLoop()
        self.widget = self._widget(*self._args, **self._kwargs)

        logger.debug(self.app)
        logger.debug(self.widget)

        # run modal
        wm = context.window_manager
        self._timer = wm.event_timer_add(1 / 120, window=context.window)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def set_stylesheet(self, app, filepath):
        file_qss = QtCore.QFile(filepath)
        if file_qss.exists():
            file_qss.open(QtCore.QFile.ReadOnly)
            stylesheet = QtCore.QTextStream(file_qss).readAll()
            app.setStyleSheet(stylesheet)
            file_qss.close()


class ExampleWidget(QtWidgets.QWidget):
    def __init__(self, label_name, text):
        super().__init__()
        self.resize(720, 300)
        self.setWindowTitle('Qt Window')
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.label = QtWidgets.QLabel(label_name)
        self.label2 = QtWidgets.QLabel(text)
        self.label3 = QtWidgets.QLabel()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        layout.addWidget(self.label2)
        layout.addWidget(self.label3)
        self.setLayout(layout)
        self.show()

    def enterEvent(self, event):
        self.label3.setText(bpy.context.object.name)


class ExampleWidgetOperator(QtWindowEventLoop):
    bl_idname = 'screen.custom_window'
    bl_label = 'Custom window'

    def __init__(self):
        super().__init__(ExampleWidget, 'LABEL_NAME', text='a text')


class PreflightOperator(QtWindowEventLoop):
    bl_idname = 'screen.preflight'
    bl_label = 'Preflight'
    task = scene_object().task

    def __init__(self):
        super().__init__(Preflight, parent=None, software='blender', preflight='mdl', path_object=scene_object())


def launch_example_widget_operator():
    bpy.utils.register_class(ExampleWidgetOperator)
    bpy.ops.screen.custom_window()


def launch_preflight():
    bpy.utils.register_class(PreflightOperator)
    bpy.ops.screen.preflight()
