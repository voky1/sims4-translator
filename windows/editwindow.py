# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, QObject, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu
from typing import TYPE_CHECKING

from .ui.editwindow import Ui_EditWindow

from singletons.config import config
from singletons.interface import interface
from singletons.translator import translator
from utils.signals import dictionary_signals
from utils.functions import text_to_edit, text_to_stbl, icon
from utils.constants import *


if TYPE_CHECKING:
    from windows.mainwindow import MainWindow


class EditWindow(QMainWindow, Ui_EditWindow):

    def __init__(self, parent: 'MainWindow'):
        super().__init__(parent)
        self.setupUi(self)

        self.main_window = parent

        self.item = None

        self.tableview.clicked.connect(self.tableview_click)
        self.tableview.customContextMenuRequested.connect(self.generate_item_context_menu)

        self.btn_ok.clicked.connect(self.ok_click)
        self.btn_cancel.clicked.connect(self.cancel_click)

        self.cb_api.currentTextChanged.connect(self.change_api)

        self.btn_translate.clicked.connect(self.translate_click)

        self.txt_original.selected.connect(self.selection_change)
        self.txt_original_diff.selected.connect(self.selection_change)

        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(interface.text('EditWindow', 'Search and Edit'))
        self.btn_translate.setText(interface.text('EditWindow', 'Translate'))
        self.btn_ok.setText('  {}  '.format(interface.text('EditWindow', 'OK (Ctrl+Enter)')))
        self.lbl_original.setText(interface.text('EditWindow', 'Original text'))
        self.lbl_original_diff.setText(interface.text('EditWindow', 'Different original'))
        self.lbl_translate.setText(interface.text('EditWindow', 'Current translation'))
        self.lbl_translate_diff.setText(interface.text('EditWindow', 'Different translation'))
        self.btn_cancel.setText(interface.text('EditWindow', 'Cancel'))
        self.txt_comment.setPlaceholderText(interface.text('EditWindow', 'Comment...'))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            if event.modifiers() and Qt.ControlModifier:
                self.ok_click()
        elif event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def change_api(self):
        config.set_value('api', 'engine', self.cb_api.currentText())

    @Slot(QObject)
    def selection_change(self, sender):
        text = sender.textCursor().selectedText()
        if len(text) >= 3:
            self.main_window.dictionary_model.proxy.filter(text=text)

    def tableview_click(self, index):
        model = self.tableview.model()
        item = model.sourceModel().items[model.mapToSource(index).row()]
        if item:
            if index.column() == COLUMN_DICTIONARIES_TRANSLATE:
                text = item[RECORD_DICTIONARY_TRANSLATE]
            else:
                text = item[RECORD_DICTIONARY_SOURCE]
            self.txt_search.setPlainText(text_to_edit(text))

    def exec(self, item):
        self.item = item

        self.txt_original.setPlainText(text_to_edit(item.source))
        self.txt_translate.setPlainText(text_to_edit(item.translate))

        self.txt_comment.setText(item.comment)

        engine = config.value('api', 'engine')
        self.cb_api.clear()
        self.cb_api.addItems(translator.engines)
        engine_index = self.cb_api.findText(engine)
        self.cb_api.setCurrentIndex(engine_index if engine_index >= 0 else 0)

        if item.source_old:
            self.txt_original_diff.setPlainText(text_to_edit(item.source_old))
            self.txt_original_diff.setVisible(True)
            self.lbl_original_diff.setVisible(True)
        else:
            self.txt_original_diff.setVisible(False)
            self.lbl_original_diff.setVisible(False)

        if item.translate_old:
            self.txt_translate_diff.setPlainText(text_to_edit(item.translate_old))
            self.txt_translate_diff.setVisible(True)
            self.lbl_translate_diff.setVisible(True)
        else:
            self.txt_translate_diff.setVisible(False)
            self.lbl_translate_diff.setVisible(False)

        self.txt_resource.setText('Record: STBL - 0x{instance:016x}[0x{id:08x}]'.format(instance=item.resource.instance,
                                                                                        id=item.id))

        self.show()

        self.txt_translate.setFocus()

    def ok_click(self):
        self.main_window.undo.wrap(self.item)
        self.main_window.undo.commit()

        self.item.translate = text_to_stbl(self.txt_translate.toPlainText())
        self.item.flag = FLAG_VALIDATED
        self.item.comment = self.txt_comment.text()

        self.item.translate_old = None

        dictionary_signals.update.emit(self.item)

        self.close()

    def translate_click(self):
        self.lbl_status.setStyleSheet('')
        self.lbl_status.setText(interface.text('EditWindow', 'Loading...'))
        QApplication.processEvents()
        response = translator.translate(self.cb_api.currentText(), self.item.source)
        if response.status_code == 200:
            self.txt_translate.setPlainText(response.text)
            self.lbl_status.setText('')
        else:
            self.lbl_status.setStyleSheet('color: red;')
            self.lbl_status.setText(response.text)

    def cancel_click(self):
        self.close()

    def generate_item_context_menu(self, position):
        index = self.sender().indexAt(position)
        if not index.isValid():
            return

        position.setY(position.y() + 22)

        context_menu = QMenu()

        use_action = context_menu.addAction(icon('validate_2'), interface.text('EditWindow', 'Use this translation'))

        action = context_menu.exec_(self.sender().mapToGlobal(position))
        if action is None:
            return

        if action == use_action:
            item = self.tableview.selected_item()
            self.txt_translate.setPlainText(text_to_edit(item[RECORD_DICTIONARY_TRANSLATE]))
