# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QLineEdit, QProxyStyle, QStyle
from PySide6.QtGui import QIcon, QPixmap

from singletons.config import config


class CustomProxyStyle(QProxyStyle):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.theme_name = config.value('interface', 'theme')

    def standardIcon(self, standardIcon, option=None, widget=None):
        if standardIcon == QStyle.SP_LineEditClearButton:
            return QIcon(QPixmap(f':/images/{self.theme_name}/backspace.png'))
        return super().standardIcon(standardIcon, option, widget)


class QCleaningLineEdit(QLineEdit):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyle(CustomProxyStyle())
