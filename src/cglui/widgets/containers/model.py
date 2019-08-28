# noinspection PyUnresolvedReferences
from Qt.QtCore import QAbstractTableModel, Qt, QModelIndex


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


class PandasModel(QAbstractTableModel):
    import pandas as pd

    def __init__(self, df=pd.DataFrame(), parent=None):
        QAbstractTableModel.__init__(self, parent=parent)
        self._df = df.copy()

    def toDataFrame(self):
        return self._df.copy()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            try:
                return self._df.columns.tolist()[section]
            except (IndexError, ):
                return None
        elif orientation == Qt.Vertical:
            try:
                # return self.df.index.tolist()
                return self._df.index.tolist()[section]
            except (IndexError, ):
                return None

    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if not index.isValid():
            return None

        return self._df.ix[index.row(), index.column()]

    def setData(self, index, value, role):
        row = self._df.index[index.row()]
        col = self._df.columns[index.column()]
        if hasattr(value, 'toPyObject'):
            # PyQt4 gets a QVariant
            value = value.toPyObject()
        else:
            # PySide gets an unicode
            dtype = self._df[col].dtype
            if dtype != object:
                value = None if value == '' else dtype.type(value)
        self._df.set_value(row, col, value)
        return True

    def rowCount(self, parent=QModelIndex()):
        return len(self._df.index)

    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)

    def sort(self, column, order):
        colname = self._df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(colname, ascending= order == Qt.AscendingOrder, inplace=True)
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()


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
