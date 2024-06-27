# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

from .ui.import_dialog import Ui_ImportDialog

from singletons.interface import interface
from singletons.signals import progress_signals, color_signals
from singletons.state import app_state
from singletons.undo import undo
from utils.functions import compare, text_to_stbl
from utils.constants import *


class ImportDialog(QDialog, Ui_ImportDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

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
            table = app_state.packages_storage.read_xml(self.filename)
        elif self.filename.lower().endswith('.stbl'):
            table = app_state.packages_storage.read_stbl(self.filename)
        elif self.filename.lower().endswith('.package'):
            table = app_state.packages_storage.read_package(self.filename)

        if self.rb_selection.isChecked():
            items = app_state.tableview.selected_items()
        else:
            items = app_state.packages_storage.items()

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

        progress_signals.initiate.emit(interface.text('System', 'Importing translate...'), len(items) / 100)

        for i, item in enumerate(items):
            if i % 100 == 0:
                progress_signals.increment.emit()

            if self.rb_all.isChecked() or self.rb_selection.isChecked() or item.flag in flags:
                sid = item.id
                if sid in table:
                    source = item.source
                    dest = item.translate
                    translate = table[sid]
                    if not compare(dest, translate) and not compare(source, translate):
                        undo.wrap(item)
                        if self.cb_replace.isChecked():
                            if item.flag != FLAG_UNVALIDATED:
                                item.translate_old = item.translate
                            item.translate = text_to_stbl(translate)
                            item.flag = FLAG_VALIDATED
                        else:
                            if item.flag == FLAG_UNVALIDATED:
                                item.translate = text_to_stbl(translate)
                                item.flag = FLAG_VALIDATED
                            else:
                                item.translate_old = text_to_stbl(translate)

        undo.commit()

        color_signals.update.emit()
        progress_signals.finished.emit()

    def import_click(self):
        self.translate()
        self.close()

    def cancel_click(self):
        self.close()
