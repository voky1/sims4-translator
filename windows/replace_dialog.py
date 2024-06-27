# -*- coding: utf-8 -*-

import re
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog

from .ui.replace_dialog import Ui_ReplaceDialog

from singletons.interface import interface
from singletons.signals import color_signals
from singletons.state import app_state
from singletons.undo import undo
from utils.constants import *


class ReplaceDialog(QDialog, Ui_ReplaceDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

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

        if search:
            for item in app_state.packages_storage.items():
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

    @staticmethod
    def update_combobox(combobox):
        current_text = combobox.currentText()
        if current_text:
            values = [current_text]
            for i in range(combobox.count()):
                item_text = combobox.itemText(i)
                if len(values) < 10 and item_text not in values:
                    values.append(item_text)
            combobox.clear()
            combobox.addItems(values)

    def save_values(self):
        self.update_combobox(self.cb_search)
        self.update_combobox(self.cb_replace)
