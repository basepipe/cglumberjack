from PySide import QtCore, QtGui
from cgl.ui.widgets.base import LJDialog
from cgl.core.util import load_json
from cgl.core.path import icon_path
import os


class ScreenPlayTextEdit(QtGui.QTextEdit):
    def __init__(self, parent=None):
        QtGui.QTextEdit.__init__(self, parent)
        self.setViewportMargins(144, 0, 144, 0)
        self.setProperty('class', 'screen_play')


class RoboGary(LJDialog):
    def __init__(self, parent=None):
        LJDialog.__init__(self, parent)
        self.setWindowTitle('RoboGary')
        trifecta_layout = QtGui.QHBoxLayout(self)
        trifecta_layout.setContentsMargins(0, 96, 0, 96)
        highlight_icon = os.path.join(icon_path(), 'highlight_24px.png')
        # self.transcript_file = r'B:\Users\tmiko\Downloads\tom_ahmed_conversation_12_10_2019.json'
        self.transcript_file = r'\\Mac\Home\Downloads\tom_ahmed_conversation_12_10_2019.json'
        self.transcript = load_json(self.transcript_file)
        self.words = self.transcript['results']['items']
        self.next_words_length = 5
        self.cgl_word_dict = self.create_cgl_word_dict()
        self.tools_layout = QtGui.QVBoxLayout()
        self.script_layout = QtGui.QVBoxLayout()
        self.title_line_edit = QtGui.QLineEdit()
        self.gridA = QtGui.QGridLayout()
        self.gridA.setContentsMargins(96, 0, 0, 12)
        self.grid = QtGui.QGridLayout()
        self.grid.setContentsMargins(96, 0, 0, 0)

        # Screenplay stuff
        self.title_label = QtGui.QLabel('TITLE:')
        self.title_line_edit.setProperty('class', 'screen_play_edit')
        self.title_line_edit.setText('TYPE TITLE HERE')
        self.screenplay_text_edit = ScreenPlayTextEdit()
        self.screenplay_text_edit.setProperty('class', 'screen_play')
        self.width = 816
        self.screenplay_text_edit.setMinimumWidth(self.width)
        self.screenplay_text_edit.setMaximumWidth(self.width)
        self.punctuation = [',', '.', '?']

        # Details stuff
        self.description_label = QtGui.QLabel("DESCRIPTION:")
        self.description_line_edit = QtGui.QLineEdit('TYPE DESCRIPTION HERE')
        self.description_line_edit.setProperty('class', 'screen_play_edit')
        self.location_label = QtGui.QLabel("LOCATION: ")
        self.location_line_edit = QtGui.QLineEdit('TYPE LOCATION HERE')
        self.location_line_edit.setProperty('class', 'screen_play_edit')
        self.date_label = QtGui.QLabel("DATE: ")
        self.date_line_edit = QtGui.QLineEdit('TYPE DATE HERE')
        self.date_line_edit.setProperty('class', 'screen_play_edit')
        self.selection_start_label = QtGui.QLabel("Start:")
        self.selection_start_line_edit = QtGui.QLineEdit()
        self.selection_end_label = QtGui.QLabel("End:")
        self.selection_end_line_edit = QtGui.QLineEdit()



        # grid
        self.gridA.addWidget(self.title_label, 10, 0)
        self.gridA.addWidget(self.title_line_edit, 10, 1)
        self.grid.addWidget(self.description_label, 11, 0)
        self.grid.addWidget(self.description_line_edit, 11, 1)
        self.grid.addWidget(self.location_label, 12, 0)
        self.grid.addWidget(self.location_line_edit, 12, 1)
        self.grid.addWidget(self.date_label, 13, 0)
        self.grid.addWidget(self.date_line_edit, 13, 1)
        self.grid.addWidget(self.selection_start_label, 14, 0)
        self.grid.addWidget(self.selection_start_line_edit, 14, 1)
        self.grid.addWidget(self.selection_end_label, 15, 0)
        self.grid.addWidget(self.selection_end_line_edit, 15, 1)

        # Toolbar
        toolbar = QtGui.QHBoxLayout()
        toolbar.setContentsMargins(96, 0, 0, 0)

        self.script_layout.addLayout(self.gridA)
        self.script_layout.addLayout(toolbar)
        self.script_layout.addWidget(self.screenplay_text_edit)

        self.tools_layout.addLayout(self.grid)

        self.highlight_button = QtGui.QToolButton()
        self.highlight_button.setIcon(QtGui.QIcon(highlight_icon))
        toolbar.addWidget(self.highlight_button)
        toolbar.addStretch(1)

        trifecta_layout.addLayout(self.script_layout)
        trifecta_layout.addLayout(self.tools_layout)
        self.tools_layout.addStretch(1)

        self.highlight_button.clicked.connect(self.on_highlight_clicked)
        self.screenplay_text_edit.selectionChanged.connect(self.on_selected)
        self.load_transcript()

    def create_cgl_word_dict(self):
        """
        this parses all words in the dictionary, and gives us key information about the words that allows us to do fast
        searches.
        :return:
        """
        word_dict = {}
        for i, w in enumerate(self.words):
            word_string = w['alternatives'][0]['content']
            d_ = {'position': i,
                  'string': word_string,
                  'next_words': self.find_next_words_in_list(index=i+1, num=self.next_words_length)}
            if 'start_time' in w.keys():
                d_['start_time'] = w['start_time']
                d_['end_time'] = w['end_time']
            if word_string in word_dict.keys():
                word_dict[word_string].append(d_)
            else:
                word_dict[word_string] = [d_]
        return word_dict

    def find_next_words_in_list(self, index, num=5):
        words = []
        for i in range(num):
            try:
                words.append(self.words[index+i]['alternatives'][0]['content'])
            except IndexError:
                pass
        return words

    def on_selected(self):
        text = self.screenplay_text_edit.textCursor().selectedText()
        word = ''
        if text:
            words = text.split()
            if len(words) > 1:
                self.find_phrase()
            else:
                if words:
                    word = self.find_word(words[0])
                if word:
                    self.selection_end_line_edit.setText(word['end_time'])
                    self.selection_start_line_edit.setText(word['start_time'])

    def find_phrase(self):
        phrase = self.screenplay_text_edit.textCursor().selectedText().split(' ')
        while '' in phrase:
            phrase.remove('')
        start_word = self.find_word(phrase[0], multi_word=True)
        end_word = self.find_word(phrase[-1])
        if start_word:
            # print 'start word "%s", %s' % (phrase[0], start_word)
            self.selection_start_line_edit.setText(start_word['start_time'])
        if end_word:
            # print 'end word %s, %s' % (phrase[-1], end_word)
            self.selection_end_line_edit.setText(end_word['end_time'])

    def find_word(self, word, multi_word=False):
        word = word.replace(' ', '')
        word = word.replace(',', '')
        word = word.replace('.', '')
        word = word.replace('?', '')
        word = word.replace(';', '')
        if word:
            if word in self.cgl_word_dict.keys():
                matches = self.cgl_word_dict[word]
                final_matches = []
                if len(matches) > 1:
                    next_words = self.find_next_words_in_text(multi_word=multi_word)
                    for m in matches:
                        if m['next_words'] == next_words:
                            final_matches.append(m)
                else:
                    m = matches[0]
                    final_matches.append(m)
                    self.selection_end_line_edit.setText(m['end_time'])
                    self.selection_start_line_edit.setText(m['start_time'])
                if len(final_matches) == 1:
                    return final_matches[0]
                elif len(final_matches) > 1:
                    print '%s Matches, try adjusting self.next_words_length' % len(final_matches)
                    for each in final_matches:
                        print each
                else:
                    # print 'No Match Found for %s' % word
                    pass

    def find_next_words_in_text(self, multi_word=False):
        new_list = []
        cursor = self.screenplay_text_edit.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        new_end = end + 50
        if multi_word:
            cursor.setPosition(start, QtGui.QTextCursor.MoveAnchor)
        else:
            cursor.setPosition(end, QtGui.QTextCursor.MoveAnchor)
        cursor.setPosition(new_end, QtGui.QTextCursor.KeepAnchor)
        self.screenplay_text_edit.setTextCursor(cursor)
        splited = self.screenplay_text_edit.textCursor().selectedText().split(' ')
        cursor.setPosition(start, QtGui.QTextCursor.MoveAnchor)
        cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
        self.screenplay_text_edit.setTextCursor(cursor)
        if multi_word:
            splited.pop(0)
        for i, s in enumerate(splited):
            if len(new_list) < self.next_words_length:
                new_list = self.fix_punctuation(self.punctuation, s, i, splited, new_list)
        return new_list

    @staticmethod
    def fix_punctuation(punctuation, word, i, splitted, new_list):
        appended = False
        if word:
            for p in punctuation:
                if p in splitted[i]:
                    if len(splitted[i]) > 1:
                        new_list.append(word.replace(p, ''))
                        if len(new_list) < 5:
                            new_list.append(unicode(p))
                        appended = True
            if not appended:
                new_list.append(word)
        return new_list

    def find_next_words(self, start_of_phrase=False):
        """
        returns next word of the selection.
        :param word:
        :return:
        """
        if start_of_phrase:
            splited = self.screenplay_text_edit.textCursor().selectedText().split(' ')
            while '' in splited:
                splited.remove('')
            next_ = splited[1]
            return next_
        else:
            # keep expanding selection until i find a full word or punctuation.
            cursor = self.screenplay_text_edit.textCursor()
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            new_end = end+20
            cursor.setPosition(end, QtGui.QTextCursor.MoveAnchor)
            cursor.setPosition(new_end, QtGui.QTextCursor.KeepAnchor)
            self.screenplay_text_edit.setTextCursor(cursor)
            splited = self.screenplay_text_edit.textCursor().selectedText().split(' ')
            cursor.setPosition(start, QtGui.QTextCursor.MoveAnchor)
            cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
            self.screenplay_text_edit.setTextCursor(cursor)
            while '' in splited:
                splited.remove('')
            next_ = splited[0]
        return next_

    def on_highlight_clicked(self):
        print 'highlight clicked'
        print self.screenplay_text_edit.textCursor().selectedText()
        print 'now i just have to get the start time of the first word, and the end time of the last word'

    def load_transcript(self):
        speaker_labels = self.transcript['results']['speaker_labels']
        previous_speaker = ''
        speakers = []
        row = -1
        for segment in speaker_labels['segments']:
            # find out if we're doing the same speaker or a new one:
            segment_list = []
            speaker = segment['speaker_label'].upper()
            start_time = float(segment['start_time'])
            end_time = float(segment['end_time'])
            for w in self.words:
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
                    speaker_label = QtGui.QLabel('%s NAME:' % speaker.upper())
                    speaker_line_edit = QtGui.QLineEdit('TYPE SPEAKER HERE')
                    speaker_line_edit.setProperty('class', 'screen_play_edit')
                    self.grid.addWidget(speaker_label, row, 0)
                    self.grid.addWidget(speaker_line_edit, row, 1)
                    speakers.append(speaker)

                self.screenplay_text_edit.append('\n\n%s' % speaker)
                self.screenplay_text_edit.setAlignment(QtCore.Qt.AlignCenter)
                # TODO is there any way for me to capture the correlation between the cursro position of the word i'm adding
                # and its index within the json file?
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
