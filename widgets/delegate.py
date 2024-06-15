# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtGui import QColor

from utils.constants import *


class MainDelegatePaint(QStyledItemDelegate):

    def __init__(self, parent=None, model=None):
        super().__init__(parent)

        self.model = model.model
        self.proxy = model.proxy

        self.__colors = {
            FLAG_UNVALIDATED: [QColor('#eaaaaa'), QColor('#eabbbb')],
            FLAG_PROGRESS: [QColor('#dcaadc'), QColor('#dcbbdc')],
            FLAG_VALIDATED: [QColor('#aaaadc'), QColor('#bbbbdc')],
            FLAG_REPLACED: [QColor('#c7ffff'), QColor('#e6ffff')],
            FLAG_TRANSLATED: [QColor('#ededed'), QColor('#ffffff')]
        }

        self.__different = [QColor('#dcdcaa'), QColor('#dcdcbb')]

    def paint(self, painter, option, index):
        try:
            row = self.proxy.mapToSource(index).row()
            column = index.column()

            if 0 <= row < self.model.count:
                item = self.model.items[row]

                remainder = index.row() % 2

                if column == COLUMN_MAIN_SOURCE and item.source_old or column == COLUMN_MAIN_TRANSLATE and item.translate_old:
                    color = self.__different[remainder]
                else:
                    color = self.__colors[item.flag][remainder]

                painter.fillRect(option.rect, color)

        except IndexError:
            pass

        super().paint(painter, option, index)


class DictionaryDelegatePaint(QStyledItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__color = [QColor('#ededed'), QColor('#ffffff')]

    def paint(self, painter, option, index):
        painter.fillRect(option.rect, self.__color[index.row() % 2])
        super().paint(painter, option, index)
