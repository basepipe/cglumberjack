import json
from Qt import QtWidgets
from cgl.ui.widgets.base import LJDialog
from cgl.core.util import load_style_sheet, load_json


class RoboGary(LJDialog):
    def __init__(self, parent=None):
        LJDialog.__init__(self, parent)
        self.setWindowTitle('Robo Gary')
        trifecta_layout = QtWidgets.QHBoxLayout(self)
        self.script_layout = QtWidgets.QVBoxLayout()

        # script layout stuff
        self.title_line_edit = QtWidgets.QLineEdit()
        self.title_line_edit.setText('TitleOfInterview')
        self.script_text_area = QtWidgets.QPlainTextEdit()
        self.script_layout.addWidget(self.title_line_edit)
        self.script_layout.addWidget(self.script_text_area)

        trifecta_layout.addLayout(self.script_layout)
        self.load_transcript()

    def load_transcript(self):
        transcript_file = r'B:\Users\tmiko\Downloads\tom_ahmed_conversation_12_10_2019.json'
        transcript = load_json(transcript_file)
        # for now assumes 1 transcript
        raw_text = transcript['results']['transcripts'][0]['transcript']
        speaker_labels = transcript['results']['speaker_labels']
        self.script_text_area.setPlainText(raw_text)
        num_speakers = speaker_labels['speakers']
        print len(speaker_labels['segments']), 'speech segments'
        for segment in speaker_labels['segments']:
            print segment





if __name__ == "__main__":
    from cgl.ui.startup import do_gui_init
    app = do_gui_init()
    mw = RoboGary()
    # mw = Designer(type_='menus')
    mw.setWindowTitle('Preflight Designer')
    mw.setMinimumWidth(1200)
    mw.setMinimumHeight(500)
    mw.show()
    mw.raise_()
    style_sheet = load_style_sheet()
    app.setStyleSheet(style_sheet)
    app.exec_()