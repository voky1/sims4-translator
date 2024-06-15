# -*- coding: utf-8 -*-

from PySide6.QtCore import QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor

from utils.functions import monospace_font


class AbstractTableModel(QAbstractTableModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.items = []
        self.count = 0

        self.addition_sort = -1

        self.color_null = QColor(114, 114, 213)

        self.monospace = monospace_font()

    def rowCount(self, parent=None):
        return self.count

    def columnCount(self, parent=None):
        return 0

    def replace(self, rows):
        self.beginResetModel()
        self.items = rows
        self.count = len(self.items)
        self.endResetModel()

    def append(self, rows):
        self.beginResetModel()
        if rows:
            if isinstance(rows[0], list):
                self.items.extend(rows)
            else:
                self.items.append(rows)
            self.count = len(self.items)
        self.endResetModel()

    def remove(self, index):
        rc = self.count
        self.beginRemoveRows(QModelIndex(), rc, rc)
        del self.items[index]
        self.count = rc - 1
        self.endRemoveRows()


class AbstractModel:

    def __init__(self):
        self.model = None
        self.proxy = None

    def replace(self, items):
        self.model.replace(items)

    def append(self, items):
        self.model.append(items)

    def remove(self, index):
        self.model.remove(index)
