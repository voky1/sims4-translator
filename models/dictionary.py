# -*- coding: utf-8 -*-

import operator
from PySide6.QtCore import Qt, QSortFilterProxyModel

from .abstact import AbstractTableModel

from singletons.interface import interface
from singletons.state import app_state
from utils.functions import text_to_table
from utils.constants import *


class Model(AbstractTableModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.addition_sort = RECORD_DICTIONARY_PACKAGE

        self.index_mapping = {
            COLUMN_DICTIONARIES_PACKAGE: RECORD_DICTIONARY_PACKAGE,
            COLUMN_DICTIONARIES_SOURCE: RECORD_DICTIONARY_SOURCE,
            COLUMN_DICTIONARIES_TRANSLATE: RECORD_DICTIONARY_TRANSLATE,
        }

    def columnCount(self, parent=None):
        return 5

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        if row < 0 or row >= len(self.filtered):
            return None

        item = self.filtered[row]

        if role == Qt.FontRole:
            if column == COLUMN_DICTIONARIES_PACKAGE:
                return app_state.monospace.font()

        elif role == Qt.ForegroundRole:
            if column in (COLUMN_DICTIONARIES_SOURCE, COLUMN_DICTIONARIES_TRANSLATE):
                if column == COLUMN_DICTIONARIES_SOURCE:
                    txt = item[RECORD_DICTIONARY_SOURCE]
                else:
                    txt = item[RECORD_DICTIONARY_TRANSLATE]
                if not txt or not str(txt).strip(' '):
                    return self.color_null

        elif role == Qt.DisplayRole:
            if not column:
                return None

            if column == COLUMN_DICTIONARIES_PACKAGE:
                return item[RECORD_DICTIONARY_PACKAGE]

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
        idx = self.index_mapping.get(column, RECORD_DICTIONARY_LENGTH)
        key = operator.itemgetter(idx,
                                  self.addition_sort) if 0 <= self.addition_sort != idx else operator.itemgetter(idx)
        self.filtered.sort(key=key, reverse=reverse)
        self.endResetModel()


class ProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__text = None

        self.__column = COLUMN_DICTIONARIES_LENGTH
        self.__order = Qt.AscendingOrder

    def filter(self, text: str):
        self.__text = text.lower() if text else None
        self.process_filter()

    def process_filter(self):
        model = self.sourceModel()
        if self.__text:
            filtered_data = [i for i in model.items if self.__text in str(i[RECORD_DICTIONARY_SOURCE]).lower()]
            model.filter(filtered_data)
            model.sort(self.__column, self.__order)
        else:
            model.filter([])

    def headerData(self, section, orientation, role=None):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            header_mapping = {
                COLUMN_DICTIONARIES_PACKAGE: 'ID',
                COLUMN_DICTIONARIES_SOURCE: interface.text('MainTableView', 'Original'),
                COLUMN_DICTIONARIES_TRANSLATE: interface.text('MainTableView', 'Translated')
            }
            return header_mapping.get(section, '')
        return None

    def sort(self, column, order=Qt.AscendingOrder):
        self.__column = column
        self.__order = order
        self.sourceModel().sort(column, order)
