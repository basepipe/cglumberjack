import logging

from Qt import QtCore


class LJTableSearchProxy(QtCore.QSortFilterProxyModel):
    def __init__(self):
        QtCore.QSortFilterProxyModel.__init__(self)
        self.search_wgt = None
        self.search_text = None
        self.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setDynamicSortFilter(True)

    def set_search_widget(self, wgt):
        self.search_wgt = wgt

    def invalidateFilter(self):
        text = self.search_wgt.text()
        logging.debug("search: filtering on %s" % text)
        if text:
            self.search_text = text.lower()
        else:
            self.search_text = None
        QtCore.QSortFilterProxyModel.invalidateFilter(self)

    def filterAcceptsRow(self, src_row, src_parent):
        if not self.search_text:  # there is no search we can accept
            return True

        column_count = self.sourceModel().columnCount(src_row)
        for x in range(0, column_count + 1):
            src_index = self.sourceModel().index(src_row, x, src_parent)
            data = self.sourceModel().data(src_index, QtCore.Qt.DisplayRole)

            if self.search_text in data.lower():
                return True
        return False

