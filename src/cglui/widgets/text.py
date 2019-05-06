from Qt import QtGui, QtCore


class Highlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)

        keywordFormat = QtGui.QTextCharFormat()
        keywordFormat.setForeground(QtGui.QColor('#CB772F'))
        #keywordFormat.setFontWeight(QtGui.QFont.Bold)

        keywordPatterns = ['\\bprint\\b', '\\bFalse\\b', '\\bNone\\b', '\\bTrue\\b', '\\band\\b', '\\bas\\b',
                           '\\bbreak\\b', '\\bclass\\b', '\\bcontinue\\b', '\\bdef\\b', '\\bdel\\b', '\\belif\\b',
                           '\\belse\\b', '\\bexcept\\b', '\\bfinally\\b', '\\bassert\\b',
                           '\\bfor\\b', '\\bfrom\\b', '\\bglobal\\b', '\\bif\\b', '\\bimport\\b', '\\bin\\b',
                           '\\bis\\b', '\\blambda\\b', '\\bnonlocal\\b', '\\bnot\\b', '\\bor\\b', '\\bpass\\b',
                           '\\braise\\b', '\\breturn\\b', '\\btry\\b', '\\bwhile\\b', '\\bwith\\b', '\\byield']

        default = QtGui.QTextCharFormat()
        default.setForeground(QtGui.QColor('#A9B7C6'))
        self.highlightingRules = [(QtCore.QRegExp(".+"), default)]

        for pattern in keywordPatterns:
            self.highlightingRules.append((QtCore.QRegExp(pattern), keywordFormat))

        classFormat = QtGui.QTextCharFormat()
        classFormat.setFontWeight(QtGui.QFont.Bold)
        classFormat.setForeground(QtCore.Qt.darkMagenta)
        self.highlightingRules.append((QtCore.QRegExp("\\bQ[A-Za-z]+\\b"),
                classFormat))

        singleLineCommentFormat = QtGui.QTextCharFormat()
        singleLineCommentFormat.setForeground(QtCore.Qt.red)
        self.highlightingRules.append((QtCore.QRegExp("//[^\n]*"),
                singleLineCommentFormat))

        self.multiLineCommentFormat = QtGui.QTextCharFormat()
        self.multiLineCommentFormat.setForeground(QtCore.Qt.red)

        numberformat = QtGui.QTextCharFormat()
        numberformat.setForeground(QtGui.QColor('#6897BB'))
        self.highlightingRules.append((QtCore.QRegExp("[0-9]+"), numberformat))

        quotationFormat = QtGui.QTextCharFormat()
        quotationFormat.setForeground(QtGui.QColor('#A5C25C'))
        self.highlightingRules.append((QtCore.QRegExp("\".*\""),quotationFormat))
        self.highlightingRules.append((QtCore.QRegExp("\'.*\'"),quotationFormat))

        self_format = QtGui.QTextCharFormat()
        self_format.setForeground(QtGui.QColor('#9876AA'))
        self.highlightingRules.append((QtCore.QRegExp("\\bself\\b"), self_format))

        functionFormat = QtGui.QTextCharFormat()
        functionFormat.setFontItalic(True)
        functionFormat.setForeground(QtGui.QColor('#FFC66D'))
        self.highlightingRules.append((QtCore.QRegExp("\\b[A-Za-z0-9_]+(?=\\()"),
                functionFormat))

        self.commentStartExpression = QtCore.QRegExp("/\\*")
        self.commentEndExpression = QtCore.QRegExp("\\*/")

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QtCore.QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = self.commentStartExpression.indexIn(text)

        while startIndex >= 0:
            endIndex = self.commentEndExpression.indexIn(text, startIndex)

            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + self.commentEndExpression.matchedLength()

            self.setFormat(startIndex, commentLength,
                    self.multiLineCommentFormat)
            startIndex = self.commentStartExpression.indexIn(text,
                    startIndex + commentLength);