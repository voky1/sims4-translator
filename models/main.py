# -*- coding: utf-8 -*-

import operator
from PySide6.QtCore import Qt, QSortFilterProxyModel
from typing import TYPE_CHECKING, List

from .abstact import AbstractModel, AbstractTableModel

from storages.records import MainRecord

from singletons.config import config
from singletons.interface import interface
from utils.functions import text_to_table
from utils.constants import *


if TYPE_CHECKING:
    from windows.mainwindow import MainWindow


class Model(AbstractTableModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.addition_sort = RECORD_MAIN_INDEX

        self.main_window = None

    def columnCount(self, parent=None):
        return 0 if parent.isValid() else 9

    def data(self, index, role=None):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        if row < 0 or row >= self.count:
            return None

        item = self.items[row]

        if role == Qt.TextAlignmentRole:
            if column == COLUMN_MAIN_FLAG:
                return int(Qt.AlignCenter)

        elif role == Qt.FontRole:
            if column in (COLUMN_MAIN_ID, COLUMN_MAIN_INSTANCE, COLUMN_MAIN_GROUP):
                return self.monospace

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
                    instance = self.main_window.packages_storage.instance
                    return item[RECORD_MAIN_INDEX_ALT][3] if instance > 0 else item[RECORD_MAIN_INDEX_ALT][2]
                else:
                    if self.main_window.toolbar.cb_files.currentIndex():
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
        index_mapping = {
            COLUMN_MAIN_ID: RECORD_MAIN_ID,
            COLUMN_MAIN_INSTANCE: RECORD_MAIN_INSTANCE,
            COLUMN_MAIN_GROUP: RECORD_MAIN_GROUP,
            COLUMN_MAIN_SOURCE: RECORD_MAIN_SOURCE,
            COLUMN_MAIN_TRANSLATE: RECORD_MAIN_TRANSLATE,
            COLUMN_MAIN_FLAG: RECORD_MAIN_FLAG,
            COLUMN_MAIN_COMMENT: RECORD_MAIN_COMMENT
        }
        idx = index_mapping.get(column, RECORD_MAIN_INDEX)
        key = operator.itemgetter(idx, self.addition_sort) if 0 <= self.addition_sort != idx else operator.itemgetter(idx)
        self.items.sort(key=key, reverse=reverse)
        self.endResetModel()


class ProxyModel(QSortFilterProxyModel):

    _HEADER_DATA = {
        COLUMN_MAIN_ID: interface.text('MainTableView', 'ID'),
        COLUMN_MAIN_INSTANCE: interface.text('MainTableView', 'Instance'),
        COLUMN_MAIN_GROUP: interface.text('MainTableView', 'Group'),
        COLUMN_MAIN_SOURCE: interface.text('MainTableView', 'Original'),
        COLUMN_MAIN_TRANSLATE: interface.text('MainTableView', 'Translated'),
        COLUMN_MAIN_COMMENT: interface.text('MainTableView', 'Comment'),
        COLUMN_MAIN_FLAG: interface.text('MainTableView', 'LD')
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__text = None
        self.__text_mode = SEARCH_IN_SOURCE
        self.__package = None
        self.__instance = None
        self.__different = False
        self.__flags = []

        self.__model = None

    def setSourceModel(self, model):
        super().setSourceModel(model)
        self.__model = model

    def filter(self, text=None, textmode=SEARCH_IN_SOURCE, package=None, instance=None, different=False, flags=None):
        self.__text = text.lower() if text else None
        self.__text_mode = textmode
        self.__package = package
        if instance:
            try:
                self.__instance = int(instance, 16) if isinstance(instance, str) else instance
            except Exception:
                self.__instance = -1
        else:
            self.__instance = None
        self.__different = different
        self.__flags = flags if flags else []

        if self.__text_mode == SEARCH_IN_ID and self.__text:
            try:
                self.__text = int(self.__text, 16)
            except Exception:
                self.__text = -1

        self.invalidateFilter()

    def filterAcceptsRow(self, row, parent):
        model = self.__model

        if not model or row < 0 or row >= model.rowCount():
            return False

        item = model.items[row]

        if self.__package and item.package != self.__package:
            return False

        if self.__instance and item.instance != self.__instance:
            return False

        if self.__flags and item.flag in self.__flags:
            return False

        if self.__different and not item[RECORD_MAIN_TRANSLATE_OLD] and not item[RECORD_MAIN_SOURCE_OLD]:
            return False

        if self.__text:
            if self.__text_mode == SEARCH_IN_SOURCE and self.__text in item.source.lower():
                return True
            elif self.__text_mode == SEARCH_IN_DESTINATION and self.__text in item.translate.lower():
                return True
            elif self.__text_mode == SEARCH_IN_ID and self.__text == item.id:
                return True
            else:
                return False

        return True

    def headerData(self, section, orientation, role=None):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._HEADER_DATA.get(section, '#')
        return None

    def sort(self, column, order=Qt.AscendingOrder):
        self.__model.sort(column, order)


class MainModel(AbstractModel):

    def __init__(self, parent: 'MainWindow') -> None:
        super().__init__()

        self.model = Model(parent)
        self.proxy = ProxyModel()
        self.proxy.setSourceModel(self.model)

        self.main_window = parent
        self.model.main_window = parent

    def items(self, key: str = None, instance: int = 0) -> List[MainRecord]:
        items = self.model.items

        if instance > 0:
            items = [i for i in items if i.instance == instance]

        else:
            package = self.main_window.packages_storage.package
            if package is not None or key is not None:
                key = key if key is not None else package.key
                items = [i for i in items if i.package == key]

        return items
