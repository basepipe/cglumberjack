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
        self.raw_text_area = QtWidgets.QPlainTextEdit()
        self.width = 600
        self.script_text_area.setMaximumWidth(self.width)
        self.script_layout.addWidget(self.title_line_edit)
        self.script_layout.addWidget(self.script_text_area)

        trifecta_layout.addLayout(self.script_layout)
        trifecta_layout.addWidget(self.raw_text_area)
        self.load_transcript()

    def load_transcript(self):
        transcript_file = r'B:\Users\tmiko\Downloads\tom_ahmed_conversation_12_10_2019.json'
        transcript = load_json(transcript_file)
        # for now assumes 1 transcript
        words = transcript['results']['items']
        raw_text = transcript['results']['transcripts'][0]['transcript']
        speaker_labels = transcript['results']['speaker_labels']
        self.raw_text_area.setPlainText(raw_text)
        formatted_text = ""
        num_speakers = speaker_labels['speakers']
        previous_speaker = ''
        for segment in speaker_labels['segments']:
            # find out if we're doing the same speaker or a new one:
            speaker = segment['speaker_label']
            if speaker != previous_speaker:
                if previous_speaker:
                    formatted_text = '%s\n\n%s\n%s' % (formatted_text, previous_speaker.upper().center(self.width/7),
                                                       string_from_segment_list(previous_list))
                segment_list = []
            else:
                segment_list = previous_list
            start_time = segment['start_time']
            end_time = segment['end_time']
            segment_name = '%s_%s_%s' % (speaker, start_time, end_time)
            for w in words:
                # find the start and end index for the 'segment'
                if 'start_time' in w.keys():
                    if w['start_time'] >= segment['start_time']:
                        in_segment = True
                        if w['start_time'] < segment['end_time']:
                            segment_list.append(w['alternatives'][0]['content'])
                        if w['start_time'] > segment['end_time']:
                            in_segment = False
                else:
                    if in_segment:
                        segment_list.append(w['alternatives'][0]['content'])

            previous_speaker = speaker
            previous_list = segment_list
        self.script_text_area.setPlainText(formatted_text)


def string_from_segment_list(segment_list):
    seg_string = ''
    for s in segment_list:
        if s == ',':
            seg_string = '%s%s' % (seg_string, s)
        elif s == '.':
            seg_string = '%s%s  ' % (seg_string, s)
        else:
            seg_string = '%s %s' % (seg_string, s)
    return seg_string


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