import bpy
import sys
import os
import logging
from PySide2 import QtWidgets, QtCore
from cgl.plugins.preflight.main import Preflight
from cgl.ui.widgets.combo import AdvComboBox
from .alchemy import scene_object

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
        print('--------------------')
        print(self._args)
        print(self._kwargs)
        print('--------------------')
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
        super().__init__(Preflight, parent=None, software='blender', preflight=scene_object().task,
                         path_object=scene_object())


class InputDialogOperator(QtWindowEventLoop):
    bl_idname = 'screen.input_dialog'
    bl_label = 'InputDialog'
    title = 'Title'
    message = 'Message'
    buttons = ['Ok'],
    line_edit = False,
    line_edit_text = False,
    combo_box_items = None,
    combo_box2_items = None,
    regex = None,
    name_example = None

    def __init__(self):
        super().__init__(InputDialog, title=self.title, message=self.message,
                         buttons=self.buttons, line_edit=self.line_edit,
                         line_edit_text=self.line_edit_text,
                         combo_box_items=self.combo_box_items,
                         combo_box2_items=self.combo_box2_items,
                         regex=self.regex,
                         name_example=self.name_example)


def launch_example_widget_operator():
    bpy.utils.register_class(ExampleWidgetOperator)
    bpy.ops.screen.custom_window()


def launch_preflight():
    bpy.utils.register_class(PreflightOperator)
    bpy.ops.screen.preflight()


def launch_input_dialog(title='Attention:',
                        message='You just kicked ass',
                        buttons=['Ok'],
                        line_edit=False,
                        line_edit_text=False,
                        combo_box_items=None,
                        combo_box2_items=None,
                        regex=None,
                        name_example=None):

    bpy.utils.register_class(InputDialogOperator)
    InputDialogOperator.title = title
    InputDialogOperator.message = message
    InputDialogOperator.buttons = buttons
    InputDialogOperator.line_edit = line_edit
    InputDialogOperator.line_edit_text = line_edit_text
    InputDialogOperator.combo_box_items = combo_box_items
    InputDialogOperator.combo_box2_items = combo_box2_items
    InputDialogOperator.regex = regex
    InputDialogOperator.name_example = name_example
    bpy.ops.screen.input_dialog()


class InputDialog(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)

    def __init__(self, parent=None, title='Attention:', message="This is a kick ass message!",
                 buttons=None, line_edit=False, line_edit_text=False, combo_box_items=None,
                 combo_box2_items=None, regex=None, name_example=None):
        """

        :param parent:
        :param title: Title of the window
        :param message: Message
        :param buttons: list: you can put any number of buttons ['Button one', 'Button Two'] in this.
        :param line_edit: Boolean - True to show the lineEdit, False to Hide it.
        :param line_edit_text: Default text for the Line Edit.
        :param combo_box_items: List of items to include in a "drop down" menu
        :param combo_box2_items: List of items to include in a second "drop down menu"
        :param regex: This allows you to define a regex to be used to evaluate contents of the line edit or the first
        combo box.
        :param name_example: This message shows up if the regex fails.  We use this often for things like users
        entering names for things.
        """
        QtWidgets.QWidget.__init__(self, parent)
        self.original_message = message
        if buttons is None:
            buttons = ['Cancel', 'Ok', '']
        layout = QtWidgets.QFormLayout()
        button_box = QtWidgets.QHBoxLayout()
        self.name_example = name_example
        self.regex = regex
        self.values = ''
        self.button = ''
        self.input_text = ''
        self.message = QtWidgets.QLabel(message)
        self.combo_box = AdvComboBox(self)
        self.combo_box2 = AdvComboBox(self)
        self.line_edit = QtWidgets.QLineEdit()
        if line_edit_text:
            self.line_edit.setText(line_edit_text)
        layout.addRow(self.message)
        layout.addRow(self.combo_box)
        self.combo_box.hide()
        layout.addRow(self.combo_box2)
        self.combo_box2.hide()
        if combo_box_items:
            self.combo_box.addItems(combo_box_items)
            self.combo_box.show()
        if combo_box2_items:
            self.combo_box2.addItems(combo_box2_items)
            self.combo_box2.show()
        if line_edit:
            layout.addRow(self.line_edit)
        if buttons:
            i = len(buttons)
            while i < 3:
                buttons.append('')
                i += 1
            self.btn1 = QtWidgets.QPushButton(buttons[0])
            self.btn2 = QtWidgets.QPushButton(buttons[1])
            self.btn3 = QtWidgets.QPushButton(buttons[2])
            button_box.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                     QtWidgets.QSizePolicy.Minimum))

            button_box.addWidget(self.btn1)
            if buttons[1]:
                button_box.addWidget(self.btn2)
            if buttons[2]:
                button_box.addWidget(self.btn3)
            layout.addRow(button_box)
        self.setLayout(layout)
        self.setWindowTitle(title)

        self.btn1.clicked.connect(self.on_button_clicked)
        self.btn1.clicked.connect(self.close)
        self.btn2.clicked.connect(self.on_button_clicked)
        self.btn2.clicked.connect(self.close)
        self.btn3.clicked.connect(self.on_button_clicked)
        self.btn3.clicked.connect(self.close)
        if regex:
            self.line_edit.textChanged.connect(self.on_text_changed_regex)
            try:
                self.combo_box.textChanged.connect(self.on_text_changed_regex)
            except AttributeError:
                self.combo_box.editTextChanged.connect(self.on_text_changed_regex)
        self.show()

    def on_button_clicked(self):
        self.button = self.sender().text()
        self.input_text = self.line_edit.text()

    def on_text_changed_regex(self):
        message = ''
        text = ''
        if self.sender() == self.line_edit:
            text = self.line_edit.text()
        elif self.sender() == self.combo_box:
            text = self.combo_box.currentText()
        if re.match(self.regex, text):
            message = '%s\n%s Passes!' % (self.original_message, text)
            self.btn1.setEnabled(True)
            self.btn2.setEnabled(True)
            self.btn3.setEnabled(True)
        else:
            bad_name = '%s\n%s does not pass' % (self.original_message, text)
            message = '%s\n%s' % (bad_name, self.name_example)
            self.btn1.setEnabled(False)
            self.btn2.setEnabled(False)
            self.btn3.setEnabled(False)
        self.message.setText(message)
