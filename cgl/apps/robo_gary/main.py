from Qt import QtWidgets, QtCore, QtGui
from cgl.ui.widgets.base import LJDialog
from cgl.core.util import load_json
from cgl.core.path import icon_path
import os


class ScreenPlayTextEdit(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        QtWidgets.QTextEdit.__init__(self, parent)
        self.setViewportMargins(144, 0, 144, 0)
        self.setProperty('class', 'screen_play')


class RoboGary(LJDialog):
    def __init__(self, parent=None):
        LJDialog.__init__(self, parent)
        self.setWindowTitle('RoboGary')
        trifecta_layout = QtWidgets.QHBoxLayout(self)
        trifecta_layout.setContentsMargins(0, 96, 0, 96)
        highlight_icon = os.path.join(icon_path(), 'highlight_24px.png')
        self.tools_layout = QtWidgets.QVBoxLayout()
        self.script_layout = QtWidgets.QVBoxLayout()
        self.title_line_edit = QtWidgets.QLineEdit()
        self.gridA = QtWidgets.QGridLayout()
        self.gridA.setContentsMargins(96, 0, 0, 12)
        self.grid = QtWidgets.QGridLayout()
        self.grid.setContentsMargins(96, 0, 0, 0)
        self.title_label = QtWidgets.QLabel('TITLE:')
        self.title_line_edit.setProperty('class', 'screen_play_edit')
        self.title_line_edit.setText('TYPE TITLE HERE')
        self.description_label = QtWidgets.QLabel("DESCRIPTION:")
        self.description_line_edit = QtWidgets.QLineEdit('TYPE DESCRIPTION HERE')
        self.description_line_edit.setProperty('class', 'screen_play_edit')
        self.location_label = QtWidgets.QLabel("LOCATION: ")
        self.location_line_edit = QtWidgets.QLineEdit('TYPE LOCATION HERE')
        self.location_line_edit.setProperty('class', 'screen_play_edit')
        self.date_label = QtWidgets.QLabel("DATE: ")
        self.date_line_edit = QtWidgets.QLineEdit('TYPE DATE HERE')
        self.date_line_edit.setProperty('class', 'screen_play_edit')
        self.screenplay_text_edit = ScreenPlayTextEdit()
        self.screenplay_text_edit.setProperty('class', 'screen_play')
        self.width = 816
        self.screenplay_text_edit.setMinimumWidth(self.width)
        self.screenplay_text_edit.setMaximumWidth(self.width)

        # grid
        self.gridA.addWidget(self.title_label, 0, 0)
        self.gridA.addWidget(self.title_line_edit, 0, 1)
        self.grid.addWidget(self.description_label, 1, 0)
        self.grid.addWidget(self.description_line_edit, 1, 1)
        self.grid.addWidget(self.location_label, 2, 0)
        self.grid.addWidget(self.location_line_edit, 2, 1)
        self.grid.addWidget(self.date_label, 3, 0)
        self.grid.addWidget(self.date_line_edit, 3, 1)

        # Toolbar
        toolbar = QtWidgets.QHBoxLayout()
        toolbar.setContentsMargins(96, 0, 0, 0)
        self.tools_layout.addLayout(self.grid)
        self.script_layout.addLayout(self.gridA)
        self.script_layout.addLayout(toolbar)
        self.script_layout.addWidget(self.screenplay_text_edit)

        self.highlight_button = QtWidgets.QToolButton()
        self.highlight_button.setIcon(QtGui.QIcon(highlight_icon))
        toolbar.addWidget(self.highlight_button)
        toolbar.addStretch(1)

        trifecta_layout.addLayout(self.script_layout)
        trifecta_layout.addLayout(self.tools_layout)
        self.tools_layout.addStretch(1)

        self.highlight_button.clicked.connect(self.on_highlight_clicked)
        self.load_transcript()

    def on_highlight_clicked(self):
        print 'highlight clicked'
        print self.screenplay_text_edit.textCursor().selectedText()
        print 'now i just have to get the start time of the first word, and the end time of the last word'

    def load_transcript(self):
        transcript_file = r'B:\Users\tmiko\Downloads\tom_ahmed_conversation_12_10_2019.json'
        # transcript_file = r'\\Mac\Home\Downloads\tom_ahmed_conversation_12_10_2019.json'
        transcript = load_json(transcript_file)
        words = transcript['results']['items']
        speaker_labels = transcript['results']['speaker_labels']
        previous_speaker = ''
        speakers = []
        row = 5
        for segment in speaker_labels['segments']:
            # find out if we're doing the same speaker or a new one:
            segment_list = []
            speaker = segment['speaker_label'].upper()
            start_time = float(segment['start_time'])
            end_time = float(segment['end_time'])
            for w in words:
                # find the start and end index for the 'segment'
                if 'start_time' in w.keys():
                    if float(w['start_time']) >= start_time:
                        in_segment = True
                        if float(w['start_time']) < end_time:
                            segment_list.append(w['alternatives'][0]['content'])
                        if float(w['start_time']) > end_time:
                            in_segment = False
                else:
                    if in_segment:
                        segment_list.append(w['alternatives'][0]['content'])
            if speaker != previous_speaker:
                if speaker not in speakers:
                    row += 1
                    speaker_label = QtWidgets.QLabel('%s NAME:' % speaker.upper())
                    speaker_line_edit = QtWidgets.QLineEdit('TYPE SPEAKER HERE')
                    speaker_line_edit.setProperty('class', 'screen_play_edit')
                    self.grid.addWidget(speaker_label, row, 0)
                    self.grid.addWidget(speaker_line_edit, row, 1)
                    speakers.append(speaker)

                self.screenplay_text_edit.append('\n\n%s' % speaker)
                self.screenplay_text_edit.setAlignment(QtCore.Qt.AlignCenter)
                self.screenplay_text_edit.append(string_from_segment_list(segment_list))
                self.screenplay_text_edit.setAlignment(QtCore.Qt.AlignLeft)
            else:
                self.screenplay_text_edit.moveCursor(QtGui.QTextCursor.End)
                self.screenplay_text_edit.insertPlainText(string_from_segment_list(segment_list))
                self.screenplay_text_edit.setAlignment(QtCore.Qt.AlignLeft)
                self.screenplay_text_edit.moveCursor(QtGui.QTextCursor.End)

            previous_speaker = speaker


def string_from_segment_list(segment_list):
    seg_string = ''
    for s in segment_list:
        if s == ',':
            seg_string = '%s%s' % (seg_string, s)
        elif s == '.':
            seg_string = '%s%s  ' % (seg_string, s)
        elif s == '?':
            seg_string = '%s%s  ' % (seg_string, s)
        else:
            seg_string = '%s %s' % (seg_string, s)
    return seg_string.replace('\n', '')


if __name__ == "__main__":
    import cgl.core.startup as startup
    app, splash = startup.app_init(splash_image='robogary_A.jpg')
    mw = RoboGary()
    mw.show()
    mw.raise_()
    mw.setMinimumHeight(1056)
    mw.setMaximumHeight(1056)
    if splash:
        splash.finish(mw)
    # style_sheet = load_style_sheet()
    # app.setStyleSheet(style_sheet)
    if splash:
        splash.finish(mw)
    app.exec_()
