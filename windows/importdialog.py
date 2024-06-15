# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog
from typing import TYPE_CHECKING

from .ui.importdialog import Ui_ImportDialog

from singletons.interface import interface
from utils.functions import compare, text_to_stbl
from utils.constants import *


if TYPE_CHECKING:
    from windows.mainwindow import MainWindow


class ImportDialog(QDialog, Ui_ImportDialog):

    def __init__(self, parent: 'MainWindow'):
        super().__init__(parent)
        self.setupUi(self)

        self.main_window = parent

        self.filename = None

        self.btn_import.clicked.connect(self.import_click)
        self.btn_cancel.clicked.connect(self.cancel_click)

        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(interface.text('ImportDialog', 'Import translate'))
        self.gb_overwrite.setTitle(interface.text('ImportDialog', 'Overwrite'))
        self.rb_all.setText(interface.text('ImportDialog', 'Everything'))
        self.rb_validated.setText(interface.text('ImportDialog', 'Everything but already validated strings'))
        self.rb_validated_partial.setText(interface.text('ImportDialog',
                                                         'Everything but already validated and partial strings'))
        self.rb_partial.setText(interface.text('ImportDialog', 'Partial strings'))
        self.rb_selection.setText(interface.text('ImportDialog', 'Selection only'))
        self.cb_replace.setText(interface.text('ImportDialog', 'Replace existing translation'))
        self.btn_import.setText(interface.text('ImportDialog', 'Import'))
        self.btn_cancel.setText(interface.text('ImportDialog', 'Cancel'))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.filename = None

    def translate(self):
        if not self.filename:
            return

        table = {}

        if self.filename.lower().endswith('.xml'):
            table = self.main_window.packages_storage.read_xml(self.filename)
        elif self.filename.lower().endswith('.stbl'):
            table = self.main_window.packages_storage.read_stbl(self.filename)
        elif self.filename.lower().endswith('.package'):
            table = self.main_window.packages_storage.read_package(self.filename)

        if self.rb_selection.isChecked():
            items = self.main_window.tableview.selected_items()
        else:
            items = self.main_window.main_model.items()

        if not table or not items:
            return

        if self.rb_validated.isChecked():
            flags = [FLAG_UNVALIDATED, FLAG_PROGRESS, FLAG_REPLACED]
        elif self.rb_validated_partial.isChecked():
            flags = [FLAG_UNVALIDATED]
        elif self.rb_partial.isChecked():
            flags = [FLAG_PROGRESS, FLAG_REPLACED]
        else:
            flags = []

        undo = self.main_window.undo

        for i, item in enumerate(items):
            if i % 100 == 0:
                QApplication.processEvents()

            flag = item.flag

            if self.rb_all.isChecked() or self.rb_selection.isChecked() or flag in flags:
                sid = item.id
                if sid in table:
                    source = item.source
                    dest = item.translate
                    translate = table[sid]
                    if not compare(dest, translate) and not compare(source, translate):
                        undo.wrap(item)
                        if self.cb_replace.isChecked():
                            if flag != FLAG_UNVALIDATED:
                                item.translate_old = item.translate
                            item.translate = text_to_stbl(translate)
                            item.flag = FLAG_VALIDATED
                        else:
                            if flag == FLAG_UNVALIDATED:
                                item.translate = text_to_stbl(translate)
                                item.flag = FLAG_VALIDATED
                            else:
                                item.translate_old = text_to_stbl(translate)

        undo.commit()

    def import_click(self):
        self.translate()
        self.close()

    def cancel_click(self):
        self.close()
