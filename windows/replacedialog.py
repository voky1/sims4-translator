# -*- coding: utf-8 -*-

import re
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog
from typing import TYPE_CHECKING

from .ui.replacedialog import Ui_ReplaceDialog

from singletons.interface import interface
from utils.signals import color_signals
from utils.constants import *


if TYPE_CHECKING:
    from windows.mainwindow import MainWindow


class ReplaceDialog(QDialog, Ui_ReplaceDialog):

    def __init__(self, parent: 'MainWindow'):
        super().__init__(parent)
        self.setupUi(self)

        self.main_window = parent

        self.btn_replace.clicked.connect(self.replace_click)
        self.btn_cancel.clicked.connect(self.cancel_click)

        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(interface.text('ReplaceDialog', 'Search and replace'))
        self.cb_case_sensitive.setText(interface.text('ReplaceDialog', 'Case sensitive'))
        self.label_search.setText(interface.text('ReplaceDialog', 'Search'))
        self.label_replace.setText(interface.text('ReplaceDialog', 'Replace'))
        self.groupbox.setTitle(interface.text('ReplaceDialog', 'Search and replace in:'))
        self.rb_all_strings.setText(interface.text('ReplaceDialog', 'All strings'))
        self.rb_not_validated_strings.setText(interface.text('ReplaceDialog', 'Not validated strings'))
        self.btn_cancel.setText(interface.text('ReplaceDialog', 'Cancel'))
        self.btn_replace.setText(interface.text('ReplaceDialog', 'OK'))

    def showEvent(self, event):
        self.cb_search.clearEditText()
        self.cb_replace.clearEditText()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def replace_click(self):
        search = self.cb_search.currentText()
        replace = self.cb_replace.currentText()

        main_model = self.main_window.main_model
        undo = self.main_window.undo

        if search:
            for item in main_model.items():
                QApplication.processEvents()

                if self.rb_not_validated_strings.isChecked() and item.flag != FLAG_UNVALIDATED:
                    continue

                flags = re.IGNORECASE if not self.cb_case_sensitive.isChecked() else 0
                if re.search(search, item.translate, flags=flags):
                    undo.wrap(item)

                    item.translate = re.sub(search, replace, item.translate, flags=flags)
                    item.flag = FLAG_PROGRESS

            undo.commit()

            color_signals.update.emit()

            self.save_values()

        self.close()

    def cancel_click(self):
        self.close()

    def save_values(self):
        search = self.cb_search.currentText()
        replace = self.cb_replace.currentText()

        if search:
            values = [search]
            if self.cb_search.count():
                for i in range(self.cb_search.count()):
                    if len(values) < 10 and self.cb_search.itemText(i) not in values:
                        values.append(self.cb_search.itemText(i))

            self.cb_search.clear()
            self.cb_search.addItems(values)

        if replace:
            values = [replace]
            if self.cb_replace.count():
                for i in range(self.cb_replace.count()):
                    if len(values) < 10 and self.cb_replace.itemText(i) not in values:
                        values.append(self.cb_replace.itemText(i))

            self.cb_replace.clear()
            self.cb_replace.addItems(values)
