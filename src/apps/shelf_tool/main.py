import os
import re
import yaml
from Qt import QtWidgets, QtGui, QtCore
from cglui.widgets.combo import AdvComboBox
from cglui.widgets.base import LJDialog
import copy
from cglcore.config import app_config
import glob


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
        self.setWindowTitle("LUMBERJACK CONFIG")
        self.setLayout(self.layout)
        self.file = ""
        self.populate_software_combo()
        self.software_combo.currentIndexChanged.connect(self.on_software_selected)

    def reorder_top(self):
        #print("reordering top")
        with open(self.file, 'r') as yaml_file:
            y = yaml.load(yaml_file)

            for x in range(0, self.tabs.tabnum):
                y[self.software + '_shelves'][self.tabs.tabText(x).encode('utf-8')]["order"] = x+1

        with open(self.file, 'w') as yaml_file:
            yaml.dump(y, yaml_file)

    def reorder_bottom(self, newtabs):
        #print("reordering bottom")
        with open(self.file, 'r') as yaml_file:
            y = yaml.load(yaml_file)

            for x in range(0, newtabs.tabnum):
                if newtabs.tabText(x) != "+":
                    y[self.software + '_shelves'][self.tabs.tabText(self.tabs.currentIndex()).encode('utf-8')][newtabs.tabText(x).encode('utf-8')]["order"] = x+1

        with open(self.file, 'w') as yaml_file:
            yaml.dump(y, yaml_file)

    def add_software(self):
        software, result = QtGui.QInputDialog.getText(self, "Add New Software", "New Software Name:")
        if result:
            shelves_yaml = os.path.join(self.root, software, 'shelves.yaml')
            shelves_code_folder = os.path.join(self.root, software, 'shelves')
            print shelves_yaml
            print shelves_code_folder

            if not os.path.exists(shelves_code_folder):
                os.makedirs(shelves_code_folder)

            y = dict()
            y[software.encode('utf-8')+'_shelves'] = {}

            with open(shelves_yaml, 'w') as yaml_file:
                yaml.dump(y, yaml_file)

            self.software = software.encode('utf-8')
            self.software_dict[self.software] = shelves_yaml
            self.populate_software_combo()

    def populate_software_combo(self):
        cfg = os.path.join(self.root, '*', 'shelves.yaml')
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
        #print(self.file)
        #self.parse(self.file)

    def test_exec(self, newtabs, tabname, newname, rows):
        tp = newtabs.currentIndex()
        self.add_page(newtabs, tabname, newname, rows)
        m = re.search("tools\.([a-zA-Z_1-9]*)\.shelves.([a-zA-Z_1-9]*)\.([a-zA-Z_1-9]*)",
                      rows["command"].edit.text().encode('utf-8'))
        if m:
            software = m.group(1)
            shelf_name = m.group(2)
            button = m.group(3)
            root = app_config()['paths']['code_root']
            p = os.path.join(self.company_config_dir, software, "shelves", shelf_name, "%s.py" % button)
            print(p)
            #with open(p, 'w+') as y:
            #    y.write(rows["plaintext"].toPlainText())

        newtabs.setCurrentIndex(tp)

        exec(rows['command'].edit.text())

    def add_shelf(self):
        text, result = QtGui.QInputDialog.getText(self, "Add a New Shelf", "New Shelf Name:")
        if result:
            #print(self.file)
            with open(self.file, 'r') as yaml_file:
                y = yaml.load(yaml_file)

            self.tabs.setTabText(self.tabs.tabnum, text.encode('utf-8'))
            self.tabs.tabnum += 1

            y[self.software + '_shelves'][text.encode('utf-8')] = {"order": self.tabs.tabnum}

            with open(self.file, 'w') as yaml_file:
                yaml.dump(y, yaml_file)

            t = os.path.join(self.root, 'src', 'tools', 'cgl_%s' % self.software)
            #print(t)
            if not os.path.exists(t):
                os.makedirs(t)

            with open(os.path.join(t, '__init__.py'), 'w+') as i:
                i.write("")

            t = os.path.join(self.root, 'src', 'tools', self.software, 'shelves')
            #print(t)
            if not os.path.exists(t):
                os.makedirs(t)

            with open(os.path.join(t, '__init__.py'), 'w+') as i:
                i.write("")

            t = os.path.join(self.root, 'src', 'tools', self.software, 'shelves', text.encode('utf-8'))
            #print(t)

            if not os.path.exists(t):
                os.makedirs(t)

            with open(os.path.join(t, '__init__.py'), 'w+') as i:
                i.write("")

            self.parse(self.file)

    def add_page(self, newtabs, tabname, newname, rows):
        tp = newtabs.currentIndex()
        #print(rows["order"].edit.text())
        #print(newtabs.tabText(int(rows["order"].edit.text())-1))
        oldname = newtabs.tabText(int(rows["order"].edit.text())-1)
        if oldname == "+":
            #print("ok")
            newtabs.setTabText(int(rows["order"].edit.text())-1, newname)
            layout = QtWidgets.QVBoxLayout()
            tab = QtWidgets.QWidget()
            tab.setLayout(layout)
            scroll_area = self.make_new_button(newtabs, tabname)
            scroll_area.setWidgetResizable(True)
            newtabs.addTab(scroll_area, str("+"))
            newtabs.tabnum += 1
            if newtabs.tabnum > self.max_tab:
                self.max_tab = newtabs.tabnum
        else:
            scroll_area = self.make_new_button(newtabs, tabname)
            scroll_area.setWidgetResizable(True)

            #print(rows)

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
            oldcom = y[self.software+"_shelves"][name][oldname]["command"]

            m = re.search("tools\.([a-zA-Z_1-9]*)\.shelves.([a-zA-Z_1-9]*)\.([a-zA-Z_1-9]*)",
                          oldcom.encode('utf-8'))
            if m:
                button_file = os.path.join(self.company_config_dir, m.group(1), "shelves", m.group(2), "%s.py" % m.group(3))
                os.remove(button_file)

            #print(oldname, newname)
            if oldname is not newname:
                y[self.software+"_shelves"][name].pop(oldname, None)

            with open(self.file, 'w') as yaml_file:
                yaml.dump(y, yaml_file)

        newtabs.setTabText(int(rows["order"].edit.text()) - 1, newname)

        button_dict = {}
        path = []
        for x in rows:
            if x is not "plaintext":
                #rows[x].edit.dict_path[3] = rows[x].label.text()
                #print(rows[x].edit.dict_path)
                button_dict[rows[x].label.text().encode('utf-8').lower()] = rows[x].edit.text().encode('utf-8')

        button_dict["order"] = int(button_dict["order"])
        #print(x, button_dict[x])

        m = re.search("tools\.([a-zA-Z_1-9]*)\.shelves.([a-zA-Z_1-9]*)\.([a-zA-Z_1-9]*)", rows["command"].edit.text().encode('utf-8'))
        if m:
            root = app_config()['paths']['code_root']
            button_file = os.path.join(self.company_config_dir, m.group(1), "shelves", m.group(2), "%s.py" % m.group(3))
            if not os.path.exists(os.path.dirname(button_file)):
                os.makedirs(os.path.dirname(button_file))
            with open(button_file, 'w+') as y:
                y.write(rows["plaintext"].toPlainText())

        root = app_config()['paths']['code_root']
        i = os.path.join(root, "src", "apps", "unity", "editor", "Lumbermill", "images",
                         button_dict["icon"])
        if os.path.exists(i):
            ic = QtGui.QIcon(i)
            newtabs.setTabIcon(int(button_dict["order"]) - 1, ic)

        s = self.software + "_shelves"
        t1 = self.tabs.tabText(self.tabs.currentIndex())
        t2 = newtabs.tabText(int(button_dict["order"])-1)

        path = [s.encode('utf-8'), t1.encode('utf-8'), t2.encode('utf-8')]

        self.append_yaml(path, button_dict)
        newtabs.setCurrentIndex(tp)

    def append_yaml(self, path, button_dict):
        #print(path)
        #print(button_dict)
        with open(self.file, 'r') as yaml_file:
            y = yaml.load(yaml_file)

            y[path[0]][path[1]][path[2]] = button_dict

        if y:
            with open(self.file, 'w') as yaml_file:
                yaml.dump(y, yaml_file)

    def make_new_button(self, newtabs, tabname):
        scroll_area = QtWidgets.QScrollArea()
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        buttonname = " "
        path = [self.software+"_shelves", tabname, buttonname]

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

        icon = self.get_label_row("Icon", "", path+["Icon"])
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
            rows["command"].edit.setText(
                "import tools." + str(self.software_combo.currentText()) + ".shelves." + tabname + "."
                + rows["bname"].edit.text() + " as " + rows["bname"].edit.text() + "; "
                + rows["bname"].edit.text() + ".run()")

    def parse(self, filename):
        for x in range(0, self.tabs.tabnum):
            self.tabs.removeTab(0)

        self.tabs.tabnum = 0

        with open(filename, 'r') as stream:
            f = yaml.load(stream)

            #print(len(f))
            if len(f) == 0:
                return

            for tools in f:
                order = 1
                while order <= len(f[tools]):
                    for tabs_dict in f[tools]:
                        if f[tools][tabs_dict]["order"] == order:
                            order += 1
                            tab = QtWidgets.QWidget()
                            tab.setLayout(self.tab_level(f[tools][tabs_dict], tabs_dict))
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
                #print(x)
                if str(x) != "order" and str(x) != "active":
                    if tabs_dict[x]["order"] == i:
                        #print(x, tabs_dict[x]["order"], i, olen)
                        #order += 1
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

        scroll_area = self.make_new_button(newtabs, tabname)
        scroll_area.setWidgetResizable(True)
        newtabs.addTab(scroll_area, str("+"))
        newtabs.tabnum += 1
        if newtabs.tabnum > self.max_tab:
            self.max_tab = newtabs.tabnum

        # TODO - it'd be nice to have this number derived from how many tabs in the shelf with the most tabs.
        self.tabs.setMinimumWidth(1300)
        self.tabs.setMinimumHeight(800)

        return layout

    def generate_tab(self, newtabs, tabs_dict, tabname):
        layout = QtWidgets.QVBoxLayout()
        self.tn = tabname

        r = {}

        if type(tabs_dict) is dict:
            for x in tabs_dict:
                #print(str(x))
                if type(tabs_dict[x]) is unicode:
                    # print(x, tabs_dict[x].encode('utf-8'))
                    if str(x) != "order":
                        layout.addLayout(self.get_label_row(x, tabs_dict[x].encode('utf-8'), [x]))
                elif type(tabs_dict[x]) is not dict:
                    # print(x, str(tabs_dict[x]))
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
        m = re.search("tools\.([a-zA-Z_1-9]*)\.shelves.([a-zA-Z_1-9]*)\.([a-zA-Z_1-9]*)", command)
        if m:
            root = app_config()['paths']['code_root']
            p = os.path.join(self.company_config_dir, m.group(1), "shelves", m.group(2), "%s.py" % m.group(3))
            try:
                return open(p).read()
            except IOError:
                with open(p, 'w+') as y:
                    y.write("")

        return m

    def iterate_over_dict(self, x, layout, p):
        for y in x:
            #print(y)
            if type(x[y]) is dict:
                widget = QtWidgets.QWidget()
                new_layout = QtWidgets.QVBoxLayout()
                layout.addWidget(QtWidgets.QLabel("<b>  %s<b>" % y))
                layout.addWidget(widget)
                p.append(y)
                widget.setLayout(self.iterate_over_dict(x[y], new_layout, p))
            else:
                p.append(y)
                #print(self.tn)
                #print(p)
                layout.addLayout(self.get_label_row("\t"+y, str(x[y]), p))
            p.pop()
        return layout

    def save_change(self, edit):
        #print(edit.dict_path, edit.text())
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
        #edit.textChanged[str].connect(lambda: self.save_change(edit))
        row.addWidget(label)
        row.addWidget(edit)
        row.label = label
        row.edit = edit
        #print(edit.dict_path)
        return row

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