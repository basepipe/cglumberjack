import os
import re
import yaml
import copy
import glob
import shutil
from Qt import QtWidgets, QtGui, QtCore
from cglui.widgets.combo import AdvComboBox
from cglui.widgets.base import LJDialog
from core.config import app_config


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


class ShelfTool(LJDialog):
    def __init__(self, parent=None):
        LJDialog.__init__(self, parent)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setMovable(True)
        self.tabs.tabnum = 0
        self.company_config_dir = os.path.dirname(parent.centralWidget().initial_path_object.company_config)
        self.tabs.tabBar().tabMoved.connect(lambda: self.reorder_top())

        self.root = self.company_config_dir
        self.software_dict = {}
        self.max_tab = 0

        self.software = ""

        client_label = QtWidgets.QLabel("%s" % "Software")
        self.software_combo = AdvComboBox()
        add_software_btn = QtWidgets.QPushButton("New Software")
        add_software_btn.clicked.connect(self.add_software)
        self.software_row = QtWidgets.QHBoxLayout()
        self.software_row.addWidget(client_label)
        self.software_row.addWidget(self.software_combo)
        self.software_row.addWidget(add_software_btn)

        self.add_shelf_btn = QtWidgets.QPushButton("Add New Shelf")
        self.add_shelf_btn.clicked.connect(self.add_shelf)

        self.inner = QtWidgets.QVBoxLayout()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.minimumWidth = 1000
        self.layout.minimumHeight = 500
        self.layout.addLayout(self.inner)
        self.layout.addLayout(self.software_row)

        self.layout.addWidget(self.tabs)

        #self.layout.addLayout(button_row2)
        self.setWindowTitle("The Shelf Manager")
        self.setLayout(self.layout)
        self.file = ""
        self.populate_software_combo()
        self.software_combo.currentIndexChanged.connect(self.on_software_selected)

    def reorder_top(self):
        with open(self.file, 'r') as yaml_file:
            y = yaml.load(yaml_file)

            for x in range(0, self.tabs.tabnum):
                y[self.software][self.tabs.tabText(x).encode('utf-8')]["order"] = x+1

        with open(self.file, 'w') as yaml_file:
            yaml.dump(y, yaml_file)

    def reorder_bottom(self, newtabs):
        with open(self.file, 'r') as yaml_file:
            y = yaml.load(yaml_file)

            for x in range(0, newtabs.tabnum):
                if newtabs.tabText(x) != "+":
                    y[self.software][self.tabs.tabText(self.tabs.currentIndex()).encode('utf-8')][newtabs.tabText(x).encode('utf-8')]["order"] = x+1

        with open(self.file, 'w') as yaml_file:
            yaml.dump(y, yaml_file)

    def add_software(self):
        software, result = QtWidgets.QInputDialog.getText(self, "Add New Software", "New Software Name:")
        if result:
            shelves_yaml = os.path.join(self.root, 'cgl_tools', software, 'shelves.yaml')
            shelves_code_folder = os.path.join(self.root, 'cgl_tools', software, 'shelves')
            if not os.path.exists(shelves_code_folder):
                os.makedirs(shelves_code_folder)

            y = dict()
            y[software.encode('utf-8')] = {}

            with open(shelves_yaml, 'w') as yaml_file:
                yaml.dump(y, yaml_file)

            self.software = software.encode('utf-8')
            self.software_dict[self.software] = shelves_yaml
            self.populate_software_combo()

    def populate_software_combo(self):
        cfg = os.path.join(self.root, 'cgl_tools', '*', 'shelves.yaml')
        yamls = glob.glob(cfg)
        shelves = []
        software_list = ['']
        for each in yamls:
            software_root = os.path.split(each)[0]
            software = os.path.split(software_root)[-1]
            shelves.append(software_root)
            self.software_dict[software] = each

        for key in self.software_dict:
            software_list.append(key)

        self.software_combo.clear()
        self.software_combo.addItems(software_list)

    def on_software_selected(self):
        self.software = self.software_combo.currentText().encode('utf-8')
        if self.software:
            self.software_row.addWidget(self.add_shelf_btn)
            self.file = self.software_dict[self.software]
            self.parse(self.file)

    def select_file(self):
        self.file = str(QtWidgets.QFileDialog.getOpenFileName()[0])

    def test_exec(self, newtabs, tabname, newname, rows):
        tp = newtabs.currentIndex()
        self.add_page(newtabs, tabname, newname, rows)
        m = re.search("cgl_tools\.([a-zA-Z_1-9]*)\.shelves.([a-zA-Z_1-9]*)\.([a-zA-Z_1-9]*)",
                      rows["command"].edit.text().encode('utf-8'))
        if m:
            software = m.group(1)
            shelf_name = m.group(2)
            button = m.group(3)
            root = app_config()['paths']['code_root']
            p = os.path.join(self.company_config_dir, 'cgl_tools', software, "shelves", shelf_name, "%s.py" % button)
            with open(p, 'w+') as y:
                y.write(rows["plaintext"].toPlainText())

        newtabs.setCurrentIndex(tp)
        exec(rows['command'].edit.text())

    def make_init(self, folder):
        with open(os.path.join(folder, '__init__.py'), 'w+') as i:
            i.write("")

    def get_software_folder(self, software, shelf_name):
        software_folder = os.path.join(self.root, 'cgl_tools', software)
        shelves_folder = os.path.join(software_folder, 'shelves')
        shelf_name_folder = os.path.join(shelves_folder, shelf_name.encode('utf-8'))
        return [software_folder, shelves_folder, shelf_name_folder]

    def add_shelf(self):
        shelf_name, result = QtWidgets.QInputDialog.getText(self, "Add a New Shelf", "New Shelf Name:")
        if result:
            with open(self.file, 'r') as yaml_file:
                shelf = yaml.load(yaml_file)

            self.tabs.setTabText(self.tabs.tabnum, shelf_name.encode('utf-8'))
            self.tabs.tabnum += 1

            shelf[self.software][shelf_name.encode('utf-8')] = {"order": self.tabs.tabnum}

            with open(self.file, 'w') as yaml_file:
                yaml.dump(shelf, yaml_file)

            software_folder, shelves_folder, shelf_name_folder = self.get_software_folder(self.software, shelf_name)
            if not os.path.exists(shelf_name_folder):
                os.makedirs(shelf_name_folder)

            self.make_init(software_folder)
            self.make_init(shelves_folder)
            self.make_init(shelf_name_folder)

            self.parse(self.file)

    def add_page(self, newtabs, tabname, newname, rows):
        tp = newtabs.currentIndex()
        oldname = newtabs.tabText(int(rows["order"].edit.text())-1)
        if oldname == "+":
            newtabs.setTabText(int(rows["order"].edit.text())-1, newname)
            layout = QtWidgets.QVBoxLayout()
            tab = QtWidgets.QWidget()
            tab.setLayout(layout)
            scroll_area = self.make_new_button(newtabs, tabname, tp)
            scroll_area.setWidgetResizable(True)
            newtabs.addTab(scroll_area, str("+"))
            newtabs.tabnum += 1
            if newtabs.tabnum > self.max_tab:
                self.max_tab = newtabs.tabnum
        else:
            scroll_area = self.make_new_button(newtabs, tabname, tp)
            scroll_area.setWidgetResizable(True)

            scroll_area.bname.edit.setText(rows["bname"].edit.text().encode('utf-8'))
            scroll_area.order.edit.setText(rows["order"].edit.text().encode('utf-8'))
            scroll_area.anno.edit.setText(rows["anno"].edit.text().encode('utf-8'))
            scroll_area.command.edit.setText(rows["command"].edit.text().encode('utf-8'))
            scroll_area.icon.edit.setText(rows["icon"].edit.text().encode('utf-8'))
            scroll_area.syn.setPlainText(rows["plaintext"].toPlainText())

            newtabs.removeTab(int(rows["order"].edit.text())-1)
            newtabs.insertTab(int(rows["order"].edit.text())-1, scroll_area, newname)

            with open(self.file, 'r') as yaml_file:
                y = yaml.load(yaml_file)

            name = self.tabs.tabText(self.tabs.currentIndex())
            oldcom = y[self.software][name][oldname]["command"]

            m = re.search("cgl_tools\.([a-zA-Z_1-9]*)\.shelves.([a-zA-Z_1-9]*)\.([a-zA-Z_1-9]*)",
                          oldcom.encode('utf-8'))
            if m:
                button_file = os.path.join(self.company_config_dir, 'cgl_tools', m.group(1), "shelves", m.group(2), "%s.py" % m.group(3))
                os.remove(button_file)

            if oldname is not newname:
                y[self.software][name].pop(oldname, None)

            with open(self.file, 'w') as yaml_file:
                yaml.dump(y, yaml_file)

        newtabs.setTabText(int(rows["order"].edit.text()) - 1, newname)

        button_dict = {}
        path = []
        for x in rows:
            if x is not "plaintext":
                button_dict[rows[x].label.text().encode('utf-8').lower()] = rows[x].edit.text().encode('utf-8')

        button_dict["order"] = int(button_dict["order"])
        print rows["command"].edit.text()
        cgl_tools, software, shelves, shelf_name, button = rows["command"].edit.text().encode('utf-8').split()[1].split('.')
        button_file = os.path.join(self.company_config_dir, 'cgl_tools', software, "shelves", shelf_name, "%s.py" % button)
        if not os.path.exists(os.path.dirname(button_file)):
            os.makedirs(os.path.dirname(button_file))
        with open(button_file, 'w+') as y:
            y.write(rows["plaintext"].toPlainText())

        icon_path = os.path.join(r'%s' % self.company_config_dir, 'cgl_tools', button_dict["icon"])
        if os.path.exists(icon_path):
            newtabs.setTabIcon(int(button_dict["order"]) - 1, QtGui.QIcon(icon_path))
            newtabs.setIconSize(QtCore.QSize(24, 24))

        s = self.software
        t1 = self.tabs.tabText(self.tabs.currentIndex())
        t2 = newtabs.tabText(int(button_dict["order"])-1)

        path = [s.encode('utf-8'), t1.encode('utf-8'), t2.encode('utf-8')]

        self.append_yaml(path, button_dict)
        newtabs.setCurrentIndex(tp)

    def append_yaml(self, path, button_dict):
        with open(self.file, 'r') as yaml_file:
            y = yaml.load(yaml_file)
            y[path[0]][path[1]][path[2]] = button_dict

        if y:
            with open(self.file, 'w') as yaml_file:
                yaml.dump(y, yaml_file)

    def make_new_button(self, newtabs, tabname, index_):
        scroll_area = QtWidgets.QScrollArea()
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        buttonname = " "
        path = [self.software, tabname, buttonname]

        bname = self.get_label_row("Button Name", "", path+["Button Name"])
        scroll_area.bname = bname

        layout.addLayout(bname)

        anno = self.get_label_row("Annotation", "", path+["Annotation"])
        scroll_area.anno = anno

        layout.addLayout(anno)

        command = self.get_label_row("Command", "", path+["Command"])
        scroll_area.command = command

        layout.addLayout(command)

        order = self.get_label_row("Order", "", path+["Order"])
        scroll_area.order = order

        #layout.addLayout(order)

        icon = self.get_label_row_with_button("Icon", "", path+["Icon"], newtabs, index_)
        scroll_area.icon = icon

        layout.addLayout(icon)

        test_btn = QtWidgets.QPushButton("Test")
        save_btn = QtWidgets.QPushButton("Save")

        syn = QtWidgets.QPlainTextEdit()
        scroll_area.syn = syn
        highlighter = Highlighter(syn.document())
        synrow = QtWidgets.QHBoxLayout()
        synrow.addWidget(syn)
        layout.addLayout(synrow)

        rows = {"bname": bname, "anno": anno, "command": command, "order": order, "icon": icon, "plaintext": syn}
        save_btn.clicked.connect(lambda: self.add_page(newtabs, tabname, bname.edit.text(), rows))
        test_btn.clicked.connect(lambda: self.test_exec(newtabs, tabname, bname.edit.text(), rows))

        rows["plaintext"].insertPlainText("def run():\n    print(\"hello world\")")

        rows["bname"].edit.textChanged[str].connect(lambda: self.set_command(rows, tabname))

        rows["order"].edit.setText(str(newtabs.tabnum+1))

        button_row2 = QtWidgets.QHBoxLayout()
        button_row2.addWidget(test_btn)
        button_row2.addWidget(save_btn)

        layout.addLayout(button_row2)

        tab.setLayout(layout)
        scroll_area.setWidget(tab)

        return scroll_area

    def set_command(self, rows, tabname):
        if " " in rows["bname"].edit.text():
            rows["command"].edit.setText("NO SPACES IN BUTTON NAME")
        else:
            command = "import cgl_tools.%s.shelves.%s.%s as %s; %s.run()" % (str(self.software_combo.currentText()),
                                                                         tabname, rows["bname"].edit.text(),
                                                                         rows["bname"].edit.text(),
                                                                         rows["bname"].edit.text()
                                                                         )
            rows["command"].edit.setText(command)

    def parse(self, filename):
        for x in range(0, self.tabs.tabnum):
            self.tabs.removeTab(0)

        self.tabs.tabnum = 0

        with open(filename, 'r') as stream:
            f = yaml.load(stream)
            if len(f) == 0:
                return

            for cgl_tools in f:
                order = 1
                while order <= len(f[cgl_tools]):
                    for tabs_dict in f[cgl_tools]:
                        if f[cgl_tools][tabs_dict]["order"] == order:
                            order += 1
                            tab = QtWidgets.QWidget()
                            tab.setLayout(self.tab_level(f[cgl_tools][tabs_dict], tabs_dict))
                            scroll_area = QtWidgets.QScrollArea()
                            scroll_area.setWidget(tab)
                            scroll_area.setWidgetResizable(True)
                            self.tabs.tabnum += 1
                            self.tabs.addTab(scroll_area, str(tabs_dict))
        # need a way to auto resize the GUI to expand as far as necessary

    def tab_level(self, tabs_dict, tabname):
        newtabs = QtWidgets.QTabWidget()
        newtabs.setMovable(True)
        newtabs.tabnum = 0
        newtabs.tabBar().tabMoved.connect(lambda: self.reorder_bottom(newtabs))

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(newtabs)

        order = 1
        olen = 1

        for x in tabs_dict:
            if type(tabs_dict[x]) is dict:
                olen += 1
        k = 1

        for i in range(0, olen):
            for x in tabs_dict:
                if str(x) != "order" and str(x) != "active":
                    if tabs_dict[x]["order"] == i:
                        tab = QtWidgets.QWidget()
                        tab.setLayout(self.generate_tab(newtabs, tabs_dict[x], x, newtabs, i))
                        scroll_area = QtWidgets.QScrollArea()
                        scroll_area.setWidget(tab)
                        scroll_area.setWidgetResizable(True)
                        newtabs.addTab(scroll_area, str(x))
                        newtabs.tabnum += 1
                        if newtabs.tabnum > self.max_tab:
                            self.max_tab = newtabs.tabnum
                        root = app_config()['paths']['code_root']
                        icon_path = os.path.join(self.company_config_dir, 'cgl_tools', tabs_dict[x]["icon"])
                        if os.path.exists(icon_path):
                            newtabs.setTabIcon(int(tabs_dict[x]["order"]) - 1, QtGui.QIcon(icon_path))
                            newtabs.setIconSize(QtCore.QSize(24, 24))

        '''
        while order < olen or k == 1:
            k = 0
            for x in tabs_dict:
                if type(tabs_dict[x]) is dict and tabs_dict[x] is not {order}:
                    if tabs_dict[x]["order"] == order:
                        print(tabs_dict[x]["order"], x, order, olen)
                        order += 1
                        tab = QtWidgets.QWidget()
                        tab.setLayout(self.generate_tab(newtabs, tabs_dict[x], x))
                        scroll_area = QtWidgets.QScrollArea()
                        scroll_area.setWidget(tab)
                        scroll_area.setWidgetResizable(True)
                        newtabs.addTab(scroll_area, str(x))
                        newtabs.tabnum += 1
                        if newtabs.tabnum > self.max_tab:
                            self.max_tab = newtabs.tabnum
                        root = app_config()['paths']['code_root']
                        i = os.path.join(root, "src", "apps", "unity", "editor", "Lumbermill", "images",
                                         tabs_dict[x]["icon"])
                        if os.path.exists(i):
                            ic = QtGui.QIcon(i)
                            newtabs.setTabIcon(int(tabs_dict[x]["order"]) - 1, ic)
        '''

        scroll_area = self.make_new_button(newtabs, tabname, newtabs.tabnum)
        scroll_area.setWidgetResizable(True)
        newtabs.addTab(scroll_area, str("+"))
        newtabs.tabnum += 1
        if newtabs.tabnum > self.max_tab:
            self.max_tab = newtabs.tabnum

        # TODO - it'd be nice to have this number derived from how many tabs in the shelf with the most tabs.
        self.tabs.setMinimumWidth(1300)
        self.tabs.setMinimumHeight(800)

        return layout

    def generate_tab(self, newtabs, tabs_dict, tabname, tab_widget, index_):
        layout = QtWidgets.QVBoxLayout()
        self.tn = tabname

        r = {}

        if type(tabs_dict) is dict:
            for x in tabs_dict:
                if type(tabs_dict[x]) is unicode:
                    if str(x) != "order":
                        layout.addLayout(self.get_label_row(x, tabs_dict[x].encode('utf-8'), [x]))
                elif type(tabs_dict[x]) is not dict:
                    if x == 'icon':
                        r[x] = self.get_label_row_with_button(x, str(tabs_dict[x]), [x], tab_widget, index_)
                    else:
                        r[x] = self.get_label_row(x, str(tabs_dict[x]), [x])
                    if str(x) != "order":
                        layout.addLayout(r[x])

            for x in tabs_dict:
                if type(tabs_dict[x]) is dict:
                    layout.addWidget(QtWidgets.QLabel("<b>%s<b>" % x))
                    widget = QtWidgets.QWidget()
                    new_layout = QtWidgets.QVBoxLayout()
                    layout.addWidget(widget)
                    widget.setLayout(self.iterate_over_dict(tabs_dict[x], new_layout, [x]))

        if type(tabs_dict) is dict:
            if self.get_command(tabs_dict["command"]):
                syn = QtWidgets.QPlainTextEdit()
                syn.setPlainText(self.get_command(tabs_dict["command"]))
                highlighter = Highlighter(syn.document())
                synrow = QtWidgets.QHBoxLayout()
                synrow.addWidget(syn)
                layout.addLayout(synrow)

                if "button name" in tabs_dict or "label" in tabs_dict:
                    rows = {}
                    if "button name" in tabs_dict:
                        rows["bname"] = r["button name"]
                    else:
                        rows["bname"] = self.get_label_row("Button Name", tabname, r["order"].edit.dict_path)

                    rows["command"] = r["command"]
                    rows["order"] = r["order"]
                    rows["anno"] = r["annotation"]
                    rows["icon"] = r["icon"]
                    rows["plaintext"] = syn


                    test_btn = QtWidgets.QPushButton("Test")
                    save_btn = QtWidgets.QPushButton("Save")

                    save_btn.clicked.connect(lambda: self.add_page(newtabs, tabname, rows["bname"].edit.text(), rows))
                    test_btn.clicked.connect(lambda: self.test_exec(newtabs, tabname, rows["bname"].edit.text(), rows))

                    button_row2 = QtWidgets.QHBoxLayout()
                    button_row2.addWidget(test_btn)
                    button_row2.addWidget(save_btn)

                    layout.addLayout(button_row2)

            else:
                syn = QtWidgets.QPlainTextEdit()
                syn.setPlainText("Can't Display Module")
                syn.setEnabled(False)
                highlighter = Highlighter(syn.document())
                synrow = QtWidgets.QHBoxLayout()
                synrow.addWidget(syn)
                layout.addLayout(synrow)

                layout.addItem(QtWidgets.QSpacerItem(0, 200, QtWidgets.QSizePolicy.Expanding))

        return layout

    def get_command(self, command):
        cgl_tools, software, shelves, tab, file_ = command.split()[1].split('.')
        python_file = os.path.join(self.company_config_dir, 'cgl_tools', software, "shelves", tab, "%s.py" % file_)
        try:
            return open(python_file).read()
        except IOError:
            with open(python_file, 'w+') as y:
                y.write("")

        return python_file

    def iterate_over_dict(self, x, layout, p):
        for y in x:
            if type(x[y]) is dict:
                widget = QtWidgets.QWidget()
                new_layout = QtWidgets.QVBoxLayout()
                layout.addWidget(QtWidgets.QLabel("<b>  %s<b>" % y))
                layout.addWidget(widget)
                p.append(y)
                widget.setLayout(self.iterate_over_dict(x[y], new_layout, p))
            else:
                p.append(y)
                layout.addLayout(self.get_label_row("\t"+y, str(x[y]), p))
            p.pop()
        return layout

    def save_change(self, edit):
        with open(self.filename, 'r') as stream:
            f = yaml.load(stream)

        self.iter_dict_save(f, edit.dict_path, edit.text())

    def iter_dict_save(self, f, path, text):
        y = f[path[0]]
        for x in path:
            y = f[x]
            f = y
            if type(y) is not dict:
                break


    def get_label_row(self, lab, ed, path):
        label = QtWidgets.QLabel("%s" % lab)
        label.setMinimumWidth(250)
        edit = QtWidgets.QLineEdit()
        edit.setText(ed)
        row = QtWidgets.QHBoxLayout()
        edit.dict_path = copy.copy(path)
        row.addWidget(label)
        row.addWidget(edit)
        row.label = label
        row.edit = edit
        return row

    def get_label_row_with_button(self, lab, ed, path, tab_widget, index_):
        label = QtWidgets.QLabel("%s" % lab)
        label.setMinimumWidth(250)
        edit = QtWidgets.QLineEdit()
        edit.setPlaceholderText('Click the button to choose an icon, or drag it here')
        button = QtWidgets.QToolButton()
        button.line_edit = edit
        if ed:
            icon_path = os.path.join(self.company_config_dir, 'cgl_tools', ed)
        else:
            icon_path = ''
        button.setIcon(QtGui.QIcon(icon_path))
        button.setIconSize(QtCore.QSize(24, 24))
        button.tab_widget = tab_widget
        button.tab_index = index_ - 1
        edit.setText(ed)
        row = QtWidgets.QHBoxLayout()
        edit.dict_path = copy.copy(path)
        # edit.textChanged[str].connect(lambda: self.save_change(edit))
        row.addWidget(label)
        row.addWidget(button)
        row.addWidget(edit)
        row.label = label
        row.edit = edit
        row.button = button
        button.clicked.connect(self.icon_button_clicked)
        return row

    def icon_button_clicked(self):
        # why does this automatically execute?
        file_browser = QtWidgets.QFileDialog(self, 'Choose an Icon for this Button',
                                             str(self.root), '')
        file_browser.exec_()

        file_ = file_browser.selectedFiles()[0]
        icon_folder = os.path.join(self.company_config_dir, 'icons')
        if not os.path.exists(icon_folder):
            os.makedirs(icon_folder)
        filename = os.path.split(file_)[-1]
        if not os.path.exists(os.path.join(icon_folder, filename)):
            shutil.copy2(file_, os.path.join(icon_folder, filename))
        self.sender().setIcon(QtGui.QIcon(os.path.join(icon_folder, filename)))
        self.sender().setIconSize(QtCore.QSize(24, 24))
        self.sender().line_edit.setText(os.path.join('icons', filename))
        #self.sender().tab_widget.setTabIcon(self.sender().tab_index, QtGui.QIcon(os.path.join(icon_folder, filename)))
        #self.sender().tab_widget.setIconSize(QtCore.QSize(24, 24))

    def get_edit_row(self):
        edit = QtWidgets.QLineEdit()
        edit2 = QtWidgets.QLineEdit()
        row = QtWidgets.QHBoxLayout()
        row.addWidget(edit)
        row.addWidget(edit2)
        return row


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    mw = ShelfTool()
    mw.setWindowTitle('Shelf Tool')
    mw.show()
    mw.raise_()
    app.exec_()