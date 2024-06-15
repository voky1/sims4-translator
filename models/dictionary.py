# -*- coding: utf-8 -*-

import operator
from PySide6.QtCore import Qt, QSortFilterProxyModel
from typing import TYPE_CHECKING

from .abstact import AbstractModel, AbstractTableModel

from singletons.interface import interface
from utils.functions import text_to_table
from utils.constants import *


if TYPE_CHECKING:
    from windows.mainwindow import MainWindow


class Model(AbstractTableModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.addition_sort = RECORD_DICTIONARY_PACKAGE

    def columnCount(self, parent=None):
        return 0 if parent.isValid() else 5

    def data(self, index, role=None):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        if row < 0 or row >= self.count:
            return None

        item = self.items[row]

        if role == Qt.FontRole:
            if column == COLUMN_DICTIONARIES_PACKAGE:
                return self.monospace

        # elif role == Qt.ForegroundRole:
        #     if column in (COLUMN_DICTIONARIES_SOURCE, COLUMN_DICTIONARIES_TRANSLATE):
        #         if column == COLUMN_DICTIONARIES_SOURCE:
        #             txt = item[RECORD_DICTIONARY_SOURCE]
        #         else:
        #             txt = item[RECORD_DICTIONARY_TRANSLATE]
        #         if not txt or not str(txt).strip(' '):
        #             return self.color_null

        elif role == Qt.DisplayRole:
            if not column or column == COLUMN_DICTIONARIES_PACKAGE:
                return item[RECORD_DICTIONARY_PACKAGE]

            elif not column or column == COLUMN_DICTIONARIES_LENGTH:
                return None

            elif column in (COLUMN_DICTIONARIES_SOURCE, COLUMN_DICTIONARIES_TRANSLATE):
                if column == COLUMN_DICTIONARIES_SOURCE:
                    txt = item[RECORD_DICTIONARY_SOURCE]
                else:
                    txt = item[RECORD_DICTIONARY_TRANSLATE]
                if txt:
                    if not str(txt).strip(' '):
                        return '[SPACEBAR]' * (len(txt.split(' ')) - 1)
                    else:
                        return text_to_table(txt)
                return '[NULL]'

        return None

    def sort(self, column, order=Qt.AscendingOrder):
        self.beginResetModel()
        reverse = order == Qt.DescendingOrder
        index_mapping = {
            COLUMN_DICTIONARIES_PACKAGE: RECORD_DICTIONARY_PACKAGE,
            COLUMN_DICTIONARIES_SOURCE: RECORD_DICTIONARY_SOURCE,
            COLUMN_DICTIONARIES_TRANSLATE: RECORD_DICTIONARY_TRANSLATE,
        }
        idx = index_mapping.get(column, RECORD_DICTIONARY_LENGTH)
        key = operator.itemgetter(idx,
                                  self.addition_sort) if 0 <= self.addition_sort != idx else operator.itemgetter(idx)
        self.items.sort(key=key, reverse=reverse)
        self.endResetModel()


class ProxyModel(QSortFilterProxyModel):

    _HEADER_DATA = {
        COLUMN_DICTIONARIES_PACKAGE: 'ID',
        COLUMN_DICTIONARIES_SOURCE: interface.text('MainTableView', 'Original'),
        COLUMN_DICTIONARIES_TRANSLATE: interface.text('MainTableView', 'Translated')
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__text = None

        self.__model = None

    def setSourceModel(self, model):
        super().setSourceModel(model)
        self.__model = model

    def filter(self, text=None):
        self.__text = text if text else None
        self.invalidateFilter()

    def filterAcceptsRow(self, row, parent):
        model = self.__model
        if model is None:
            return False

        if row < 0 or row >= model.count:
            return False

        item = model.items[row]

        if self.__text:
            if self.__text in item[RECORD_DICTIONARY_SOURCE]:
                return True

        return False

    def headerData(self, section, orientation, role=None):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._HEADER_DATA.get(section, '')
        return None

    def sort(self, column, order=Qt.AscendingOrder):
        self.__model.sort(column, order)


class DictionaryModel(AbstractModel):

    def __init__(self, parent: 'MainWindow') -> None:
        super().__init__()

        self.model = Model(parent)
        self.proxy = ProxyModel()
        self.proxy.setSourceModel(self.model)

        self.main_window = parent
