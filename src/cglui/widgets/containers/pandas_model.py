from Qt.QtCore import QAbstractTableModel, Qt
import pandas as pd


class PandasModel(QAbstractTableModel):

    def __init__(self, df=pd.DataFrame(), parent=None):
        QAbstractTableModel.__init__(self, parent=parent)
        self._df = df.copy()

    def headerData(self, rowcol, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._df.columns[rowcol]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return self._df.index[rowcol]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._df.values[index.row()][index.column()])
        return None

    def rowCount(self, parent=None):
        return len(self._df.index)

    def columnCount(self, parent=None):
        return len(self._df.columns)