# noinspection PyUnresolvedReferences
import os
import re
from cgl.plugins.Qt.QtCore import QAbstractTableModel, Qt, QAbstractItemModel
from cgl.plugins.Qt.QtGui import QIcon, QColor
from cgl.core.config.config import ProjectConfig


# noinspection PyUnusedLocal
class LJItemModel(QAbstractTableModel):
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]

    def rowCount(self, index):
        if self.data_:
            return len(self.data_)
        else:
            return None

    def columnCount(self, index):
        return len(self.headers)


class LGListDictionaryItemModel(LJItemModel):
    def __init__(self, data):
        LJItemModel.__init__(self)
        self.headers = []
        self.data_ = []
        if data:
            self.data_ = data
            self.keys = data[0].keys()

    def data(self, index, role):
        row = index.row()
        key = self.keys[index.column()]
        if role == Qt.DisplayRole:
            return str(self.data_[row][key])


class LGShotgunListDictionaryItemModel(LGListDictionaryItemModel):
    def __init__(self, data, display_filter=None):
        LJItemModel.__init__(self)
        self.headers = []
        self.data_ = []
        self.keys = []
        self.data_filter = False
        if data:
            self.data_ = data
            self.data_filter = True
            if display_filter:
                for key in display_filter:
                    self.keys = display_filter.keys()
                    self.headers.append(display_filter[key])
            else:
                self.keys = data[0].keys()
                for key in self.keys:
                    self.headers.append(key.replace("sg_", "").replace("_", " ").title())

    def data(self, index, role):
        row = index.row()
        key = self.keys[index.column()]
        if role == Qt.DisplayRole:
            try:
                data = self.data_[row][key]
                if data is None:
                    return ""
                if isinstance(data, dict):
                    if 'name' in data:
                        return data['name']
                    elif 'code' in data:
                        return data['code']
                return str(data)
            except KeyError:
                return ''


class DictionaryItemModel(LJItemModel):
    def __init__(self, dict_, header_titles=None):
        LJItemModel.__init__(self)
        self.data_ = dict_
        if header_titles is None:
            header_titles = ['key', 'value']
        self.headers = header_titles

    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            if col == 0:
                return self.data_.keys()[row]
            elif col == 1:
                return self.data_.values()[row]
            return


class ListItemModel(LJItemModel):
    def __init__(self, data_list, header_titles=None, data_filter=False):
        LJItemModel.__init__(self)
        # self.setHeaderData(Qt.Horizontal, Qt.AlignLeft, Qt.TextAlignmentRole)
        self.data_ = data_list
        self.headers = header_titles
        self.data_filter = data_filter

    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            try:
                data = self.data_[row][col]
                if data is None:
                    return ""
                if isinstance(data, dict):
                    if 'name' in data:
                        return data['name']
                    elif 'code' in data:
                        return data['code']
                return str(data)
            except KeyError:
                return ''


class TreeItemModel(LJItemModel):
    def __init__(self, data_list, header_titles=None, data_filter=False):
        self.data_ = data_list
        self.headers = header_titles
        self.data_filter = data_filter

    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            try:
                data = self.data_[row][col]
                if data is None:
                    return ""
                if isinstance(data, dict):
                    if 'name' in data:
                        return data['name']
                    elif 'code' in data:
                        return data['code']
                return str(data)
            except KeyError:
                return ''


class FileTableModel(ListItemModel):
    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return self.data_[row][col]
        # if role == Qt.DecorationRole:
        #    print("Decoration Role", self.data_[row][col])
            # keeping this here for reference
            # data = self.data_[row][col]


class FilesModel(QAbstractTableModel):
    def __init__(self, data_list, header_titles=None, data_filter=False, path_object=None, cfg=None):
        QAbstractTableModel.__init__(self)
        # self.setHeaderData(Qt.Horizontal, Qt.AlignLeft, Qt.TextAlignmentRole)
        # self.setHeaderData(Qt.Horizontal, Qt.AlignLeft, Qt.TextAlignmentRole)

        self.path_object = path_object
        if not cfg:
            print(FilesModel)
            self.cfg = ProjectConfig(self.path_object)
        else:
            self.cfg = cfg
        self.data_ = data_list
        self.headers = header_titles
        self.data_filter = data_filter

    def data(self, index, role):
        try:
            data = self.data_[index.row()][index.column()]
            if role == Qt.DisplayRole:
                if data is None:
                    return ""
                elif isinstance(data, dict):
                    if 'name' in data:
                        return data['name']
                    elif 'code' in data:
                        return data['code']
                return data
            if role == Qt.DecorationRole:
                if "." not in data:
                    icon_path_ = self.cfg.icon_path('folder24px.png')
                    return QIcon(icon_path_)
            if role == Qt.ForegroundRole:
                padding_difference = self.has_approved_frame_padding(data)
                if padding_difference:
                    print(data)
                    print('Padding {} does not match studio padding {}'.format(padding_difference[0], padding_difference[1]))
                    return QColor('red')
        except KeyError:
            return ''

    def has_approved_frame_padding(self, filename):
        from cgl.core.config.config import ProjectConfig
        hashes = re.compile("#+")
        m = re.search(hashes, filename)
        if m:
            this_padding = int(len(m.group()))
            config = ProjectConfig(self.path_object)
            studio_padding = int(config.project_config['default']['padding'])
            if this_padding == studio_padding:
                return 0
            else:
                return [this_padding, studio_padding]

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]

    def rowCount(self, index):
        if self.data_:
            return len(self.data_)
        else:
            return None

    def columnCount(self, index):
        return len(self.headers)
