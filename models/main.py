# -*- coding: utf-8 -*-

import operator
from PySide6.QtCore import Qt, QSortFilterProxyModel
from typing import Union, List

from .abstact import AbstractTableModel

from singletons.config import config
from singletons.interface import interface
from singletons.state import app_state
from utils.functions import text_to_table
from utils.constants import *


class Model(AbstractTableModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.addition_sort = RECORD_MAIN_INDEX

        self.index_mapping = {
            COLUMN_MAIN_ID: RECORD_MAIN_ID,
            COLUMN_MAIN_INSTANCE: RECORD_MAIN_INSTANCE,
            COLUMN_MAIN_GROUP: RECORD_MAIN_GROUP,
            COLUMN_MAIN_SOURCE: RECORD_MAIN_SOURCE,
            COLUMN_MAIN_TRANSLATE: RECORD_MAIN_TRANSLATE,
            COLUMN_MAIN_FLAG: RECORD_MAIN_FLAG,
            COLUMN_MAIN_COMMENT: RECORD_MAIN_COMMENT
        }

    def columnCount(self, parent=None):
        return 9

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        if row < 0 or row >= len(self.filtered):
            return None

        item = self.filtered[row]

        if role == Qt.FontRole:
            if column in (COLUMN_MAIN_INDEX, COLUMN_MAIN_ID, COLUMN_MAIN_GROUP, COLUMN_MAIN_INSTANCE):
                return app_state.monospace.font()

        elif role == Qt.ForegroundRole:
            if column in (COLUMN_MAIN_SOURCE, COLUMN_MAIN_TRANSLATE):
                txt = item.source if column == COLUMN_MAIN_SOURCE else item.translate
                if not txt or not str(txt).strip(' '):
                    return self.color_null

        elif role == Qt.DisplayRole:
            if not column:
                return None

            if column == COLUMN_MAIN_INDEX:
                numeration = config.value('view', 'numeration')
                if numeration == NUMERATION_SOURCE:
                    return item.idx_source
                elif numeration == NUMERATION_XML_DP:
                    instance = app_state.current_instance
                    return item[RECORD_MAIN_INDEX_ALT][3] if instance > 0 else item[RECORD_MAIN_INDEX_ALT][2]
                else:
                    if app_state.current_package:
                        return item[RECORD_MAIN_INDEX_ALT][0]
                    else:
                        return item.idx

            elif column == COLUMN_MAIN_ID:
                return item.id_hex

            elif column == COLUMN_MAIN_INSTANCE:
                return item.instance_hex

            elif column == COLUMN_MAIN_GROUP:
                return item.group_hex

            elif column in (COLUMN_MAIN_SOURCE, COLUMN_MAIN_TRANSLATE):
                txt = item.source if column == COLUMN_MAIN_SOURCE else item.translate
                if txt:
                    if not str(txt).strip(' '):
                        return '[SPACEBAR]' * (len(txt.split(' ')) - 1)
                    else:
                        return text_to_table(txt)
                return '[NULL]'

            elif column == COLUMN_MAIN_COMMENT:
                return item.comment

        return None

    def sort(self, column, order=Qt.AscendingOrder):
        self.beginResetModel()
        reverse = order == Qt.DescendingOrder
        idx = self.index_mapping.get(column, RECORD_MAIN_INDEX)
        key = operator.itemgetter(idx,
                                  self.addition_sort) if 0 <= self.addition_sort != idx else operator.itemgetter(idx)
        self.filtered.sort(key=key, reverse=reverse)
        self.endResetModel()


class ProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__package = None
        self.__instance = None
        self.__text = None
        self.__mode = SEARCH_IN_SOURCE
        self.__flags = []
        self.__different = False

        self.__column = COLUMN_MAIN_INDEX
        self.__order = Qt.AscendingOrder

    def filter(self, package: str, instance: Union[str, int], text: str, mode: int, flags: List[int], different: bool):
        self.__package = package
        self.__mode = mode
        self.__flags = flags if flags else []
        self.__different = different

        if text:
            if mode == SEARCH_IN_ID:
                try:
                    self.__text = int(text, 16)
                except ValueError:
                    self.__text = -1
            else:
                self.__text = text.lower()
        else:
            self.__text = None

        if instance:
            try:
                self.__instance = int(instance, 16) if isinstance(instance, str) else instance
            except ValueError:
                self.__instance = -1
        else:
            self.__instance = None

        self.process_filter()

    def process_filter(self):
        model = self.sourceModel()
        filtered_data = [i for i in model.items if self.check_filter(i)]
        model.filter(filtered_data)
        model.sort(self.__column, self.__order)

    def check_filter(self, item):
        if (self.__package and item[RECORD_MAIN_PACKAGE] != self.__package) \
                or (self.__instance and item[RECORD_MAIN_INSTANCE] != self.__instance) \
                or (self.__flags and item[RECORD_MAIN_FLAG] in self.__flags):
            return False

        if self.__different:
            record_main_translate_old = item[RECORD_MAIN_TRANSLATE_OLD]
            record_main_source_old = item[RECORD_MAIN_SOURCE_OLD]
            if not record_main_translate_old and not record_main_source_old:
                return False

        if self.__text:
            if self.__mode == SEARCH_IN_ID:
                return self.__text == item[RECORD_MAIN_ID]
            elif self.__mode == SEARCH_IN_SOURCE:
                return self.__text in item[RECORD_MAIN_SOURCE].lower()
            elif self.__mode == SEARCH_IN_DESTINATION:
                return self.__text in item[RECORD_MAIN_TRANSLATE].lower()
            else:
                return False

        return True

    def headerData(self, section, orientation, role=None):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            header_mapping = {
                COLUMN_MAIN_INDEX: '#',
                COLUMN_MAIN_ID: interface.text('MainTableView', 'ID'),
                COLUMN_MAIN_INSTANCE: interface.text('MainTableView', 'Instance'),
                COLUMN_MAIN_GROUP: interface.text('MainTableView', 'Group'),
                COLUMN_MAIN_SOURCE: interface.text('MainTableView', 'Original'),
                COLUMN_MAIN_TRANSLATE: interface.text('MainTableView', 'Translated'),
                COLUMN_MAIN_COMMENT: interface.text('MainTableView', 'Comment')
            }
            return header_mapping.get(section, '')
        return None

    def sort(self, column, order=Qt.AscendingOrder):
        self.__column = column
        self.__order = order
        self.sourceModel().sort(column, order)
