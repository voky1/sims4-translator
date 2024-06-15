# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, QCoreApplication, QObject, QTimer, QAbstractTableModel, \
    Signal, Slot, QThreadPool, QRunnable
from PySide6.QtWidgets import QHeaderView, QStyledItemDelegate, QDialog
from PySide6.QtGui import QColor
from typing import TYPE_CHECKING

from windows.ui.optionsdialog import Ui_OptionsDialog

from packer.dbpf import DbpfPackage
from packer.stbl import Stbl

from storages.dictionaries import DictionariesStorage
from storages.records import MainRecord

from singletons.config import config
from singletons.expansion import expansion, Exp
from singletons.interface import interface
from singletons.language import language
from utils.signals import progress_signals
from utils.functions import opendir
from utils.constants import *


if TYPE_CHECKING:
    from windows.mainwindow import MainWindow


class DictSignals(QObject):
    finished = Signal()


class DictWorker(QRunnable):

    __slots__ = ()

    def __init__(self, exp: Exp, storage: DictionariesStorage):
        super().__init__()

        self.expansion = exp
        self.storage = storage

        self.signals = DictSignals()

    def run(self):
        file_source = self.expansion.file_source
        file_dest = self.expansion.file_dest

        _strings = {}

        items = []

        lang_source = config.value('translation', 'source')
        lang_dest = config.value('translation', 'destination')

        with DbpfPackage.read(file_source) as dbfile:
            for rid in dbfile.search_stbl():
                if rid.language == lang_source:
                    stbl = Stbl(rid=rid, value=dbfile[rid].content)
                    for sid, value in stbl.strings.items():
                        QCoreApplication.processEvents()
                        if value:
                            _strings[sid] = value

        with DbpfPackage.read(file_dest) as dbfile:
            for rid in dbfile.search_stbl():
                if rid.language == lang_dest:
                    stbl = Stbl(rid=rid, value=dbfile[rid].content)
                    for sid, value in stbl.strings.items():
                        QCoreApplication.processEvents()
                        if sid in _strings and _strings[sid] and value:
                            items.append(
                                MainRecord(0, sid, 0, 0, _strings[sid], value, FLAG_TRANSLATED, rid, rid, None, None,
                                           None, [], ''))

        self.storage.save_standalone(self.expansion.dictionary, items)

        self.signals.finished.emit()


class Model(QAbstractTableModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.items = []
        self.count = 0

        self.color_null = QColor(127, 127, 127)

    def rowCount(self, parent=None):
        return self.count

    def columnCount(self, parent=None):
        return 3

    def data(self, index, role=None):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        if row < 0 or row >= self.count:
            return None

        item = self.items[row]
        extension = isinstance(item, tuple)

        if role == Qt.TextAlignmentRole:
            if column == 2:
                return int(Qt.AlignRight)

        elif role == Qt.ForegroundRole:
            if extension and not item.exists:
                return self.color_null

        elif role == Qt.DisplayRole:
            if not column:
                return None

            if column == 1:
                return item.offset + item.name if extension else interface.text('OptionsDialog', item)

            elif column == 2:
                return item.status + ' ' if extension else None

        return None


class DelegatePaint(QStyledItemDelegate):

    def __init__(self, parent=None, model=None):
        super().__init__(parent)

        self.__model = model

        self.__found = QColor(221, 255, 221)
        self.__not_found = QColor(255, 221, 221)

    def paint(self, painter, option, index):
        try:
            row = index.row()
            if 0 <= row < self.__model.count:
                item = self.__model.items[row]
                extension = isinstance(item, tuple)
                if extension and item.exists:
                    painter.fillRect(option.rect, self.__found if item.exists_strings else self.__not_found)
        except IndexError:
            pass
        super().paint(painter, option, index)


class OptionsDialog(QDialog, Ui_OptionsDialog):

    def __init__(self, parent: 'MainWindow'):
        super().__init__(parent)
        self.setupUi(self)

        self.main_window = parent

        self.cb_backup.setChecked(config.value('save', 'backup'))
        self.cb_experemental.setChecked(config.value('save', 'experemental'))
        self.cb_strong.setChecked(config.value('dictionaries', 'strong'))

        for lang in interface.languages:
            self.cb_language.addItem(lang.name, lang.code)

        self.cb_language.setCurrentIndex(interface.current_index)

        for k in language.locales:
            self.cb_source.addItem(k)
            self.cb_dest.addItem(k)

        self.cb_source.setCurrentText(config.value('translation', 'source'))
        self.cb_dest.setCurrentText(config.value('translation', 'destination'))

        self.cb_backup.clicked.connect(self.checkbox_click)
        self.cb_experemental.clicked.connect(self.checkbox_click)
        self.cb_strong.clicked.connect(self.checkbox_click)

        self.txt_path.setText(config.value('dictionaries', 'gamepath'))
        self.txt_deepl_key.setText(config.value('api', 'deepl_key'))

        self.cb_language.currentTextChanged.connect(self.interface_change)
        self.cb_source.currentTextChanged.connect(self.language_change)
        self.cb_dest.currentTextChanged.connect(self.language_change)

        self.txt_path.textChanged.connect(self.change_path)
        self.btn_path.clicked.connect(self.select_path)

        self.txt_deepl_key.textChanged.connect(self.change_deepl_key)

        self.btn_build.clicked.connect(self.build_click)

        self.culling_timer = QTimer()
        self.culling_timer.setSingleShot(True)
        self.culling_timer.timeout.connect(self.refresh)

        self.start_culling_timer()
        self.blank = Model()
        self.model = Model()
        self.model.items = expansion.items
        self.model.count = len(self.model.items)
        self.tableview.setModel(self.model)

        header = self.tableview.verticalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        header.setDefaultSectionSize(16)

        self.tableview.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.tableview.setColumnWidth(2, 150)
        self.tableview.setColumnHidden(0, True)

        self.tableview.setItemDelegate(DelegatePaint(model=self.model))

        self.__pool = QThreadPool()
        self.__progress = 0

        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(interface.text('OptionsDialog', 'Options and dictionaries'))
        self.gb_interface.setTitle(interface.text('OptionsDialog', 'Interface'))
        self.cb_backup.setText(interface.text('OptionsDialog', 'Create backup package before finalization'))
        self.cb_experemental.setText(interface.text('OptionsDialog',
                                                    'Saving translation without conflicts (experemental)'))
        self.cb_strong.setText(interface.text('OptionsDialog',
                                              'Do not use automatic translation from other dictionaries'))
        self.gb_path.setTitle(interface.text('OptionsDialog', 'Game path'))
        self.gb_lang.setTitle(interface.text('OptionsDialog', 'Languages'))
        self.label_source.setText(interface.text('OptionsDialog', 'Source'))
        self.label_dest.setText(interface.text('OptionsDialog', 'Destination'))
        self.btn_build.setText(interface.text('OptionsDialog', 'Build dictionaries'))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_general), interface.text('OptionsDialog', 'General'))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_dictionaries), interface.text('OptionsDialog', 'Dictionaries'))
        self.gb_deepl.setTitle(interface.text('OptionsDialog', 'DeepL API key'))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def start_culling_timer(self):
        self.culling_timer.start(50)

    def refresh(self):
        self.tableview.setModel(self.blank)

        self.model = Model()
        self.model.items = expansion.items
        self.model.count = len(self.model.items)

        self.tableview.setModel(self.model)

    def change_deepl_key(self):
        config.set_value('api', 'deepl_key', self.txt_deepl_key.text())

    def change_path(self):
        config.set_value('dictionaries', 'gamepath', self.txt_path.text())
        self.start_culling_timer()

    def select_path(self):
        directory = opendir(config.value('dictionaries', 'gamepath'))
        if directory:
            self.txt_path.setText(directory)

    def language_change(self):
        config.set_value('translation', 'source', self.cb_source.currentText())
        config.set_value('translation', 'destination', self.cb_dest.currentText())
        self.start_culling_timer()

    def interface_change(self):
        config.set_value('interface', 'language', self.cb_language.currentData())
        interface.reload()
        self.retranslate()
        self.model.layoutChanged.emit()
        self.main_window.edit_window.retranslate()
        self.main_window.export_dialog.retranslate()
        self.main_window.import_dialog.retranslate()
        self.main_window.replace_dialog.retranslate()
        self.main_window.translate_dialog.retranslate()
        self.main_window.retranslate()
        self.main_window.toolbar.retranslate()
        self.main_window.tableview.refresh()

    def checkbox_click(self):
        config.set_value('save', 'backup', self.cb_backup.isChecked())
        config.set_value('save', 'experemental', self.cb_experemental.isChecked())
        config.set_value('dictionaries', 'strong', self.cb_strong.isChecked())

    def build_click(self):
        exists = expansion.exists()

        if exists:
            self.__progress = len(exists)

            progress_signals.initiate.emit(interface.text('System', 'Build dictionaries...'), self.__progress)

            for exp in exists:
                worker = DictWorker(exp, self.main_window.dictionaries_storage)
                worker.setAutoDelete(True)
                worker.signals.finished.connect(self.__finished)
                self.__pool.start(worker)

    @Slot()
    def __finished(self):
        progress_signals.increment.emit()
        self.__progress -= 1
        if self.__progress <= 0:
            self.__progress = 0
            progress_signals.finished.emit()

    def close_click(self):
        self.close()
