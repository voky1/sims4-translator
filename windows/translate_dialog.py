# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, QObject, QThreadPool, QRunnable, Signal, Slot
from PySide6.QtWidgets import QDialog
from typing import Union, List

from windows.ui.translate_dialog import Ui_TranslateDialog

from storages.records import MainRecord

import themes.light as light
import themes.dark as dark

from singletons.config import config
from singletons.interface import interface
from singletons.signals import progress_signals, color_signals
from singletons.state import app_state
from singletons.translator import translator
from singletons.undo import undo
from utils.functions import text_to_stbl, text_to_edit
from utils.constants import *


def split_by_char_limit(items: List[MainRecord], char_limit: int = 256) -> list:
    result = []
    current_chunk = []
    current_length = 0

    for item in items:
        text_length = len(item.source)
        if current_length + text_length > char_limit:
            result.append(current_chunk)
            current_chunk = [item]
            current_length = text_length
        else:
            current_chunk.append(item)
            current_length += text_length

    if current_chunk:
        result.append(current_chunk)

    return result


class TranslateSignals(QObject):
    finished = Signal()
    warning = Signal(str)
    error = Signal(str)


class BatchTranslateWorker(QRunnable):

    def __init__(self, chunk: Union[MainRecord, List[MainRecord]], engine: str):
        super().__init__()

        self.chunk = chunk
        self.engine = engine

        self.signals = TranslateSignals()

    def run(self):
        chunk = self.chunk
        is_fast = not isinstance(chunk, MainRecord)

        if is_fast:
            text_strings = []

            for item in chunk:
                text_string = text_to_edit(item.source)
                hex_replacement_n = r"\x0a"
                hex_replacement_r = r"\x0d"
                text_string = text_string.replace("\n", hex_replacement_n)
                text_string = text_string.replace("\r", hex_replacement_r)
                text_strings.append(text_string)

            combined_text = '\n'.join(text_strings)

        else:
            combined_text = text_to_edit(chunk.source)

        response = translator.translate(self.engine, combined_text)

        if response.status_code == 200:
            translated_text = response.text

            if is_fast:
                translated_texts = translated_text.split('\n')

                if len(translated_texts) == len(chunk):
                    for i, item in enumerate(chunk):
                        undo.wrap(item)
                        translated_text = translated_texts[i]
                        hex_replacement_n = bytes(r"\x0a", 'utf-8').decode('unicode-escape')
                        hex_replacement_r = bytes(r"\x0d", 'utf-8').decode('unicode-escape')
                        translated_text = translated_text.replace("\\x0a", hex_replacement_n)
                        translated_text = translated_text.replace("\\x0d", hex_replacement_r)
                        item.translate = text_to_stbl(translated_text)
                        item.flag = FLAG_VALIDATED
                else:
                    self.signals.warning.emit(interface.text('TranslateDialog', 'Some lines could not be translated.'))

            else:
                undo.wrap(chunk)
                chunk.translate = text_to_stbl(translated_text)
                chunk.flag = FLAG_VALIDATED

        else:
            self.signals.error.emit(response.text)

        self.signals.finished.emit()


class TranslateDialog(QDialog, Ui_TranslateDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.cb_api.currentTextChanged.connect(self.change_api)

        self.btn_translate.clicked.connect(self.translate_click)
        self.btn_cancel.clicked.connect(self.cancel_click)

        self.__pool = QThreadPool()

        self.__progress = 0
        self.__translating = False
        self.__error = False
        self.__log = []

        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(interface.text('TranslateDialog', 'Batch translate'))
        self.rb_all.setText(interface.text('ImportDialog', 'Everything'))
        self.rb_validated.setText(interface.text('ImportDialog', 'Everything but already validated strings'))
        self.rb_validated_partial.setText(interface.text('ImportDialog',
                                                         'Everything but already validated and partial strings'))
        self.rb_partial.setText(interface.text('ImportDialog', 'Partial strings'))
        self.rb_selection.setText(interface.text('ImportDialog', 'Selection only'))
        self.btn_cancel.setText(interface.text('TranslateDialog', 'Cancel'))
        self.btn_translate.setText(interface.text('TranslateDialog', 'Translate'))
        self.rb_slow.setText(interface.text('TranslateDialog', 'Line-by-line translation'))
        self.rb_fast.setText(interface.text('TranslateDialog', 'Multiline translation'))
        self.lbl_slow.setText(interface.text('TranslateDialog', 'Slow but more accurate translation.'))
        self.lbl_fast.setText(interface.text('TranslateDialog', 'A faster, but perhaps less accurate translation. It is recommended to use it together with DeepL, because when using Google, some strings may not be translated.'))
        self.log_box.setTitle(interface.text('TranslateDialog', 'Log'))

    def showEvent(self, event):
        engine = config.value('api', 'engine')
        self.cb_api.clear()
        self.cb_api.addItems(translator.engines)
        engine_index = self.cb_api.findText(engine)
        self.cb_api.setCurrentIndex(engine_index if engine_index >= 0 else 0)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def change_api(self):
        config.set_value('api', 'engine', self.cb_api.currentText())

    def translate(self):
        progress_signals.initiate.emit(interface.text('System', 'Translating...'), 0)

        if self.rb_selection.isChecked():
            items = app_state.tableview.selected_items()
        else:
            items = app_state.packages_storage.items()
            if self.rb_validated.isChecked():
                items = [i for i in items if i.flag in (FLAG_UNVALIDATED, FLAG_PROGRESS, FLAG_REPLACED)]
            elif self.rb_validated_partial.isChecked():
                items = [i for i in items if i.flag == FLAG_UNVALIDATED]
            elif self.rb_partial.isChecked():
                items = [i for i in items if i.flag in (FLAG_PROGRESS, FLAG_REPLACED)]

        if not items:
            progress_signals.finished.emit()
            return

        self.btn_translate.setText(interface.text('TranslateDialog', 'Stop translate'))

        if self.rb_fast.isChecked():
            chunk_items = split_by_char_limit(items, 1024)
        else:
            chunk_items = items

        self.__progress = len(chunk_items)
        self.__translating = True
        self.__error = False
        self.__log = []

        self.edt_log.clear()

        progress_signals.initiate.emit(interface.text('System', 'Translating...'), self.__progress)

        for chunk in chunk_items:
            if not self.__error:
                worker = BatchTranslateWorker(chunk, self.cb_api.currentText())
                worker.setAutoDelete(True)
                worker.signals.warning.connect(self.__warning_translate_chunk)
                worker.signals.error.connect(self.__error_translate_chunk)
                worker.signals.finished.connect(self.__finished_translate_chunk)
                self.__pool.start(worker)

    def stop_translate(self):
        self.__progress = self.__pool.activeThreadCount()
        self.__pool.clear()
        progress_signals.initiate.emit(interface.text('System',
                                                      'Stopping translate, waiting for the finish of the threads...'),
                                       self.__progress)
        self.__pool.waitForDone()

    @Slot()
    def __finished_translate_chunk(self):
        self.__progress -= 1
        if self.__progress == 0:
            undo.commit()
            self.__progress = 0
            self.__translating = False
            self.btn_translate.setText(interface.text('TranslateDialog', 'Translate'))
            color_signals.update.emit()
            progress_signals.finished.emit()

        app_state.tableview.refresh()
        progress_signals.increment.emit()

    @Slot(str)
    def __error_translate_chunk(self, text: str):
        if not self.__error:
            self.__error = True
            color = dark.TEXT_ERROR if config.value('interface', 'theme') == 'dark' else light.TEXT_ERROR
            self.__log.append(f'<span style="color: {color};">{text}</span>')
            self.print_log()
            self.stop_translate()

    @Slot(str)
    def __warning_translate_chunk(self, text: str):
        self.__log.append(text)
        self.print_log()

    def print_log(self):
        self.edt_log.setText('<br>'.join(self.__log))
        self.edt_log.verticalScrollBar().setValue(self.edt_log.verticalScrollBar().maximum())

    def translate_click(self):
        if not self.__translating:
            self.translate()
        else:
            self.stop_translate()

    def cancel_click(self):
        self.close()
