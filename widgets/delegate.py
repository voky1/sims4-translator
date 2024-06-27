# -*- coding: utf-8 -*-

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QStyledItemDelegate, QProxyStyle, QStyleOptionHeader, QStyle
from PySide6.QtGui import QColor, QIcon

import themes.light as light
import themes.dark as dark

from singletons.config import config
from singletons.state import app_state
from utils.constants import *


class MainDelegatePaint(QStyledItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model = app_state.packages_storage.model
        self.proxy = app_state.packages_storage.proxy

        is_dark_theme = config.value('interface', 'theme') == 'dark'

        colors_light = {
            FLAG_UNVALIDATED: [QColor(light.UNVALIDATED_TABLEVIEW), QColor(light.UNVALIDATED_TABLEVIEW_ODD)],
            FLAG_PROGRESS: [QColor(light.PROGRESS_TABLEVIEW), QColor(light.PROGRESS_TABLEVIEW_ODD)],
            FLAG_VALIDATED: [QColor(light.VALIDATED_TABLEVIEW), QColor(light.VALIDATED_TABLEVIEW_ODD)],
            FLAG_REPLACED: [QColor('#c7ffff'), QColor('#e6ffff')],
            FLAG_TRANSLATED: [QColor(light.TRANSLATED_TABLEVIEW), QColor(light.TRANSLATED_TABLEVIEW_ODD)]
        }

        colors_dark = {
            FLAG_UNVALIDATED: [QColor(dark.UNVALIDATED_TABLEVIEW), QColor(dark.UNVALIDATED_TABLEVIEW_ODD)],
            FLAG_PROGRESS: [QColor(dark.PROGRESS_TABLEVIEW), QColor(dark.PROGRESS_TABLEVIEW_ODD)],
            FLAG_VALIDATED: [QColor(dark.VALIDATED_TABLEVIEW), QColor(dark.VALIDATED_TABLEVIEW_ODD)],
            FLAG_REPLACED: [QColor('#c7ffff'), QColor('#e6ffff')],
            FLAG_TRANSLATED: [QColor(dark.TRANSLATED_TABLEVIEW), QColor(dark.TRANSLATED_TABLEVIEW_ODD)]
        }

        diffirent_light = [QColor(light.DIFFERENT_TABLEVIEW), QColor(light.DIFFERENT_TABLEVIEW_ODD)]
        diffirent_dark = [QColor(dark.DIFFERENT_TABLEVIEW), QColor(dark.DIFFERENT_TABLEVIEW_ODD)]

        self.__colors = colors_dark if is_dark_theme else colors_light
        self.__diffirent = diffirent_dark if is_dark_theme else diffirent_light

    def paint(self, painter, option, index):
        try:
            row = self.proxy.mapToSource(index).row()
            column = index.column()

            if 0 <= row < len(self.model.filtered):
                item = self.model.filtered[row]

                remainder = index.row() % 2
                if (column == COLUMN_MAIN_SOURCE and item.source_old or
                        column == COLUMN_MAIN_TRANSLATE and item.translate_old):
                    color = self.__diffirent[remainder]
                else:
                    color = self.__colors[item.flag][remainder]

                painter.fillRect(option.rect, color)

        except IndexError:
            pass

        super().paint(painter, option, index)


class DictionaryDelegatePaint(QStyledItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent)

        is_dark_theme = config.value('interface', 'theme') == 'dark'

        colors_light = [QColor(light.TRANSLATED_TABLEVIEW), QColor(light.TRANSLATED_TABLEVIEW_ODD)]
        colors_dark = [QColor(dark.TRANSLATED_TABLEVIEW), QColor(dark.TRANSLATED_TABLEVIEW_ODD)]

        self.__colors = colors_dark if is_dark_theme else colors_light

    def paint(self, painter, option, index):
        painter.fillRect(option.rect, self.__colors[index.row() % 2])
        super().paint(painter, option, index)


class HeaderProxy(QProxyStyle):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.theme_name = config.value('interface', 'theme')

        self.text_color = QColor(dark.TEXT) if self.theme_name == 'dark' else QColor(light.TEXT)

    def drawControl(self, element, option, painter, widget=None):
        if element == QStyle.CE_HeaderLabel:
            sort_option = option.sortIndicator
            rect = option.rect

            text_width = option.fontMetrics.horizontalAdvance(option.text)
            text_height = option.fontMetrics.height()
            text_rect = QRect(rect.left() + (rect.width() - text_width) / 2,
                              rect.top() + 1 + (rect.height() - text_height) / 2,
                              text_width, text_height)
            painter.setPen(self.text_color)
            painter.drawText(text_rect, option.text)

            sort_icon = None
            if sort_option == QStyleOptionHeader.SortDown:
                sort_icon = QIcon(f':/images/{self.theme_name}/arrow_down.png').pixmap(10, 6)
            elif sort_option == QStyleOptionHeader.SortUp:
                sort_icon = QIcon(f':/images/{self.theme_name}/arrow_up.png').pixmap(10, 6)

            if sort_icon:
                sort_rect = QRect(rect.left() + (rect.width() - sort_icon.width()) / 2,
                                  rect.top(), sort_icon.width(), sort_icon.height())
                painter.drawPixmap(sort_rect, sort_icon)

        else:
            super().drawControl(element, option, painter, widget)
