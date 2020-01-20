from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.ui.widgets.base import LJDialog
from cgl.core.path import PathObject, lj_list_dir


class ListWidget(QtWidgets.QListWidget):

    def sizeHint(self):
        s = QtCore.QSize()
        height = self.count()*24
        s.setHeight(height)
        s.setWidth(self.sizeHintForColumn(0))
        return s


class PublishDialog(LJDialog):
    do_publish = QtCore.Signal()

    def __init__(self, parent=None, path_object=None, verbose=False):
        LJDialog.__init__(self, parent)
        if not path_object:
            return
        self.do_review = True
        self.setMinimumWidth(300)
        self.setWindowTitle('Publish %s -->> %s' % (path_object.version, path_object.next_major_version().version))
        layout = QtWidgets.QVBoxLayout()
        if path_object.context == 'render':
            render_files = lj_list_dir(path_object.split_after('resolution'))
            path_object.set_attr(context='source')
            source_files = lj_list_dir(path_object.split_after('resolution'))
        else:
            source_files = lj_list_dir(path_object.split_after('resolution'))
            path_object.set_attr(context='render')
            render_files = lj_list_dir(path_object.split_after('resolution'))
        current_user_label = QtWidgets.QLabel('Current User: <b>%s</b>' % path_object.user)
        current_version_label = QtWidgets.QLabel('Current Version: <b>%s</b>' % path_object.version)
        publish_version_label = QtWidgets.QLabel('<b>Publish to Version: %s?</b>' %
                                                 path_object.next_major_version().version)
        publish_version_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.source_label = QtWidgets.QLabel('My Files')
        self.render_label = QtWidgets.QLabel('Publish Files')
        self.source_files_widget = ListWidget()
        self.source_files_widget.setEnabled(False)
        self.render_files_widget = ListWidget()
        self.source_files_widget.addItems(source_files)
        self.render_files_widget.addItems(render_files)
        cancel_button = QtWidgets.QPushButton()
        cancel_button.setText('Cancel')
        self.publish_button = QtWidgets.QPushButton()
        self.publish_button.setText('Publish')
        self.submit_review_checkbox = QtGui.QCheckBox('Submit Review with Publish')
        if render_files:
            self.render_files_widget.setCurrentItem(self.render_files_widget.item(0))
            self.submit_review_checkbox.setChecked(True)

        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(cancel_button)
        button_row.addWidget(self.publish_button)

        layout.addWidget(current_user_label)
        layout.addWidget(current_version_label)
        layout.addWidget(self.source_label)
        layout.addWidget(self.source_files_widget)
        layout.addWidget(self.render_label)
        layout.addWidget(self.render_files_widget)
        layout.addWidget(self.submit_review_checkbox)
        layout.addWidget(publish_version_label)
        layout.addLayout(button_row)
        self.setLayout(layout)
        self.publish_button.clicked.connect(self.on_publish_clicked)
        self.submit_review_checkbox.clicked.connect(self.on_check_box_clicked)
        cancel_button.clicked.connect(self.accept)

        if not verbose:
            self.hide_details()

    def hide_details(self):
        self.source_files_widget.hide()
        self.source_label.hide()
        self.render_files_widget.hide()
        self.render_label.hide()

    def on_render_selected(self):
        self.submit_review_checkbox.setChecked(True)

    def on_publish_clicked(self):
        self.do_publish.emit()
        self.accept()

    def on_check_box_clicked(self):
        if self.submit_review_checkbox.checkState() == QtCore.Qt.Checked:
            self.do_review = True
        else:
            self.do_review = False


if __name__ == "__main__":
    from cgl.ui.startup import do_gui_init
    test_path = r'D:/VFX/FRIDAY_ROOT/cglumberjack/render/cgl_testProjectH/shots/SJM/010/comp/tmiko/000.006/high/' \
                r'03_2a_#####.exr'
    path_object = PathObject(test_path)
    app = do_gui_init()
    mw = PublishDialog(path_object=path_object)
    mw.setWindowTitle('Publish')
    mw.show()
    mw.raise_()
    #style_sheet = load_style_sheet()
    #app.setStyleSheet(style_sheet)
    app.exec_()
