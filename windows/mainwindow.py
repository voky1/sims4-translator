# -*- coding: utf-8 -*-

import sys
import pyperclip
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QMessageBox
from PySide6.QtGui import QAction

from .ui.mainwindow import Ui_MainWindow

from .editwindow import EditWindow
from .optionsdialog import OptionsDialog
from .replacedialog import ReplaceDialog
from .exportdialog import ExportDialog
from .importdialog import ImportDialog
from .translatedialog import TranslateDialog

from models.main import MainModel
from models.dictionary import DictionaryModel
from storages.packages import PackagesStorage
from storages.dictionaries import DictionariesStorage

from singletons.config import config
from singletons.interface import interface
from singletons.translator import translator
from utils.signals import progress_signals, undo_signals, color_signals
from utils.functions import icon, open_supported, open_xml, save_package, save_xml
from utils.undo import Undo
from utils.constants import *


class ColumnAction(QAction):

    def __init__(self, parent=None, text=None, index=0) -> None:
        super().__init__(parent)

        self.main_window = parent

        self.setCheckable(True)

        self.__text = text
        self.__index = index

        name = self.config_name
        self.__checked = config.value('view', name) if name else False

        self.setChecked(self.__checked)

        self.triggered.connect(self.clicked)

    def retranslate(self):
        self.setText(interface.text('MainTableView', self.__text))

    @property
    def config_name(self):
        if self.__index == COLUMN_MAIN_ID:
            return 'id'
        elif self.__index == COLUMN_MAIN_INSTANCE:
            return 'instance'
        elif self.__index == COLUMN_MAIN_GROUP:
            return 'group'
        elif self.__index == COLUMN_MAIN_SOURCE:
            return 'source'
        elif self.__index == COLUMN_MAIN_COMMENT:
            return 'comment'
        return None

    def clicked(self):
        self.__checked = not self.__checked
        self.setChecked(self.__checked)
        self.main_window.tableview.setColumnHidden(self.__index, not self.__checked)
        name = self.config_name
        if name:
            config.set_value('view', name, self.__checked)


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.setAcceptDrops(True)

        self.tableview.doubleClicked.connect(self.edit_string)
        self.tableview.customContextMenuRequested.connect(self.generate_item_context_menu)

        self.action_load_file.triggered.connect(self.load_file)
        self.action_add_file.triggered.connect(self.add_file)
        self.action_save.triggered.connect(self.save)
        self.action_save_as.triggered.connect(self.save_as)
        self.action_finalize.triggered.connect(self.finalize)
        self.action_finalize_as.triggered.connect(self.finalize_as)
        self.action_load_bundle.triggered.connect(self.load_bundle)
        self.action_save_bundle.triggered.connect(self.save_bundle)
        self.action_import_translation.triggered.connect(self.import_translation)
        self.action_export_stbl.triggered.connect(self.export_translation_stbl)
        self.action_export_xml.triggered.connect(self.export_translation_xml)
        self.action_export_xml_dp.triggered.connect(self.export_translation_xml_dp)
        self.action_save_dictionary.triggered.connect(self.save_dictionary)
        self.action_close.triggered.connect(self.close)
        self.action_exit.triggered.connect(sys.exit)

        self.action_replace.triggered.connect(self.replace)
        self.action_translate_from_dictionaries.triggered.connect(self.translate_from_dict)
        self.action_validate_all_translations.triggered.connect(self.validate_2_all)
        self.action_reset_all_translations.triggered.connect(self.validate_0_all)
        self.action_translate.triggered.connect(self.batch_translate)
        self.action_undo.triggered.connect(self.undo_restore)

        self.action_colorbar.triggered.connect(self.colorbar_toggle)
        self.action_colorbar.setChecked(config.value('view', 'colorbar'))

        self.action_options.triggered.connect(self.options)
        self.action_group_original.triggered.connect(self.group_original)
        self.action_group_highbit.triggered.connect(self.group_highbit)
        self.action_group_lowbit.triggered.connect(self.group_lowbit)

        self.action_group_original.setChecked(config.value('group', 'original'))
        self.action_group_highbit.setChecked(config.value('group', 'highbit'))
        self.action_group_lowbit.setChecked(config.value('group', 'lowbit'))

        self.action_about_qt.triggered.connect(self.about_qt)

        self.action_num_standart.triggered.connect(self.num_standart)
        self.action_num_source.triggered.connect(self.num_source)
        self.action_num_xml_dp.triggered.connect(self.num_xml_dp)

        self.toolbar.search_toggle.triggered.connect(self.search_toggle)
        self.toolbar.filter_validate_0.triggered.connect(self.filter_timer_trigger)
        self.toolbar.filter_validate_1.triggered.connect(self.filter_timer_trigger)
        self.toolbar.filter_validate_2.triggered.connect(self.filter_timer_trigger)
        self.toolbar.filter_validate_3.triggered.connect(self.filter_timer_trigger)
        self.toolbar.filter_validate_4.triggered.connect(self.filter_timer_trigger)
        self.toolbar.edt_search.textChanged.connect(self.search_timer_trigger)
        self.toolbar.cb_files.currentIndexChanged.connect(self.change_file)
        self.toolbar.cb_instances.currentIndexChanged.connect(self.change_instance)

        self.__search_flag = SEARCH_IN_SOURCE

        self.edit_window = EditWindow(self)
        self.replace_dialog = ReplaceDialog(self)
        self.export_dialog = ExportDialog(self)
        self.import_dialog = ImportDialog(self)
        self.translate_dialog = TranslateDialog(self)

        self.main_model = MainModel(self)
        self.dictionary_model = DictionaryModel(self)

        self.packages_storage = PackagesStorage(self)
        self.dictionaries_storage = DictionariesStorage(self)

        self.tableview.set_model(self.main_model)
        self.edit_window.tableview.set_model(self.dictionary_model)

        self.num_change()

        self.action_column = [
            ColumnAction(self, 'ID', COLUMN_MAIN_ID),
            ColumnAction(self, 'Instance', COLUMN_MAIN_INSTANCE),
            ColumnAction(self, 'Group', COLUMN_MAIN_GROUP),
            ColumnAction(self, 'Original', COLUMN_MAIN_SOURCE),
            ColumnAction(self, 'Comment', COLUMN_MAIN_COMMENT),
        ]

        for col in self.action_column:
            self.menu_view.insertAction(self.action_insert, col)
        self.menu_view.insertSeparator(self.action_insert)

        self.menu_view.removeAction(self.action_insert)
        self.action_insert = None

        self.filter_timer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.update_proxy)

        progress_signals.initiate.connect(self.__initiate_progress)
        progress_signals.increment.connect(self.__increment_progress)
        progress_signals.finished.connect(self.__finished_progress)
        undo_signals.refresh.connect(self.__undo_refresh)
        undo_signals.clean_all.connect(self.__undo_clean_all)
        undo_signals.clean_by_key.connect(self.__undo_clean_by_key)

        self.undo = Undo(self)

        self.retranslate()

    def retranslate(self):
        self.action_load_file.setText(interface.text('MainWindow', 'Load file...'))
        self.action_save_as.setText(interface.text('MainWindow', 'Save as...'))
        self.action_close.setText(interface.text('MainWindow', 'Close'))
        self.action_save.setText(interface.text('MainWindow', 'Save'))
        self.action_save_dictionary.setText(interface.text('MainWindow', 'Save dictionary'))
        self.action_replace.setText(interface.text('MainWindow', 'Search and replace...'))
        self.action_validate_all_translations.setText(interface.text('MainWindow', 'Validate all translations'))
        self.action_reset_all_translations.setText(interface.text('MainWindow', 'Reset all translations'))
        self.action_exit.setText(interface.text('MainWindow', 'Exit'))
        self.action_add_file.setText(interface.text('MainWindow', 'Add file...'))
        self.action_undo.setText(interface.text('MainWindow', 'Undo'))
        self.action_about_qt.setText(interface.text('MainWindow', 'About Qt...'))
        self.action_options.setText(interface.text('MainWindow', 'Options...'))
        self.action_export_xml.setText(interface.text('MainWindow', 'To XML...'))
        self.action_translate_from_dictionaries.setText(interface.text('MainWindow', 'Translate from dictionaries'))
        self.action_translate.setText(interface.text('MainWindow', 'Batch translate...'))
        self.action_finalize.setText(interface.text('MainWindow', 'Finalize package'))
        self.action_finalize_as.setText(interface.text('MainWindow', 'Finalize package as...'))
        self.action_export_xml_dp.setText(interface.text('MainWindow', 'To XML (Deaderpool\'s STBL editor)...'))
        self.action_group_original.setText(interface.text('MainWindow', 'Use original group'))
        self.action_group_highbit.setText(interface.text('MainWindow', 'Use high-bit'))
        self.action_export_stbl.setText(interface.text('MainWindow', 'To STBL...'))
        self.action_group_lowbit.setText(interface.text('MainWindow', 'Use low-bit'))
        self.action_import_translation.setText(interface.text('MainWindow', 'Import translation...'))
        self.action_save_bundle.setText(interface.text('MainWindow', 'Save bundle...'))
        self.action_load_bundle.setText(interface.text('MainWindow', 'Load bundle...'))
        self.action_num_standart.setText(interface.text('MainWindow', 'Standart'))
        self.action_num_source.setText(interface.text('MainWindow', 'From the source file'))
        self.action_num_xml.setText(interface.text('MainWindow', 'XML format'))
        self.action_num_xml_dp.setText(interface.text('MainWindow', 'XML format (Deaderpool\'s STBL editor)'))
        self.action_colorbar.setText(interface.text('MainWindow', 'Color visualization'))
        self.menu_file.setTitle(interface.text('MainWindow', 'File'))
        self.menu_export_translation.setTitle(interface.text('MainWindow', 'Export translation'))
        self.menu_translation.setTitle(interface.text('MainWindow', 'Translation'))
        self.menu_view.setTitle(interface.text('MainWindow', 'View'))
        self.menu_numeration.setTitle(interface.text('MainWindow', 'Numeration'))
        self.menu_options.setTitle(interface.text('MainWindow', 'Options'))
        self.menu_group.setTitle(interface.text('MainWindow', 'Group'))
        self.menu_help.setTitle(interface.text('MainWindow', 'Help'))

        for col in self.action_column:
            col.retranslate()

    def dragEnterEvent(self, event):
        event.setAccepted(False)
        filename = event.mimeData().text().lower()
        if filename.endswith('.package') or filename.endswith('.stbl') or filename.endswith('.xml'):
            event.setAccepted(True)

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        self.load(event.mimeData().text().replace('file:///', ''))

    def closeEvent(self, event):
        if self.check_modified(True):
            config.save()
            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F1:
            if event.modifiers() and Qt.ControlModifier:
                self.validate_2_all()
            else:
                self.validate_2()

        elif event.key() == Qt.Key_F2:
            self.validate_1()

        elif event.key() == Qt.Key_F4:
            if event.modifiers() and Qt.ControlModifier:
                self.validate_0_all()
            else:
                self.validate_0()

        elif event.key() == Qt.Key_C and event.modifiers() and Qt.ControlModifier:
            self.copy()

        elif event.key() == Qt.Key_V and event.modifiers() and Qt.ControlModifier:
            self.paste()

        elif event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.edit_string()

        elif event.key() == Qt.Key_O and event.modifiers() and Qt.ControlModifier:
            self.open_file()

        elif event.key() == Qt.Key_S and event.modifiers() and Qt.ControlModifier:
            self.save()

        elif event.key() == Qt.Key_R and event.modifiers() and Qt.ControlModifier:
            self.replace()

        elif event.key() == Qt.Key_Z and event.modifiers() and Qt.ControlModifier:
            self.undo_restore()

        elif event.key() == Qt.Key_T and event.modifiers() and Qt.ControlModifier:
            self.translate()

        else:
            super().keyPressEvent(event)

    def search_toggle(self):
        if self.__search_flag == SEARCH_IN_SOURCE:
            self.__search_flag = SEARCH_IN_DESTINATION
            self.toolbar.search_toggle.setIcon(icon('search_dest'))
            self.toolbar.search_toggle.setToolTip(interface.text('ToolBar', 'Search in translation'))
        elif self.__search_flag == SEARCH_IN_DESTINATION:
            self.__search_flag = SEARCH_IN_ID
            self.toolbar.search_toggle.setIcon(icon('search_id'))
            self.toolbar.search_toggle.setToolTip(interface.text('ToolBar', 'Search in ID'))
        else:
            self.__search_flag = SEARCH_IN_SOURCE
            self.toolbar.search_toggle.setIcon(icon('search_source'))
            self.toolbar.search_toggle.setToolTip(interface.text('ToolBar', 'Search in original'))

        if self.toolbar.edt_search.text():
            self.filter_timer_trigger()

    def change_file(self):
        self.toolbar.cb_instances.blockSignals(True)
        self.toolbar.cb_instances.clear()
        self.toolbar.cb_instances.addItem(interface.text('ToolBar', '-- All instances --'))
        package = self.packages_storage.package
        if package:
            self.toolbar.cb_instances.addItems(package.instances)
        self.toolbar.cb_instances.blockSignals(False)
        color_signals.update.emit()
        self.filter_timer_trigger()

    def change_instance(self):
        color_signals.update.emit()
        self.filter_timer_trigger()

    def search_timer_trigger(self):
        self.filter_timer.start(250)

    def filter_timer_trigger(self):
        self.filter_timer.start(90)

    def update_proxy(self):
        flags = []
        if not self.toolbar.filter_validate_0.isChecked():
            flags.append(FLAG_UNVALIDATED)
        if not self.toolbar.filter_validate_1.isChecked():
            flags.append(FLAG_PROGRESS)
            flags.append(FLAG_REPLACED)
        if not self.toolbar.filter_validate_2.isChecked():
            flags.append(FLAG_VALIDATED)
        if not self.toolbar.filter_validate_3.isChecked():
            flags.append(FLAG_TRANSLATED)

        cb_instances = self.toolbar.cb_instances
        cb_files = self.toolbar.cb_files
        self.main_model.proxy.filter(text=self.toolbar.edt_search.text(),
                                     textmode=self.__search_flag,
                                     instance=cb_instances.currentText() if cb_instances.currentIndex() > 0 else None,
                                     package=cb_files.currentText() if cb_files.currentIndex() > 0 else None,
                                     different=self.toolbar.filter_validate_4.isChecked(),
                                     flags=flags)

    def set_state_menu(self):
        state = self.packages_storage.enabled

        self.action_import_translation.setEnabled(state)
        self.menu_export_translation.setEnabled(state)

        self.action_add_file.setEnabled(state)
        self.action_save.setEnabled(state)
        self.action_save_as.setEnabled(state)
        self.action_save_bundle.setEnabled(self.packages_storage.multiplied)
        self.action_save_dictionary.setEnabled(state)
        self.action_close.setEnabled(state)
        self.action_replace.setEnabled(state)
        self.action_translate_from_dictionaries.setEnabled(state)
        self.action_validate_all_translations.setEnabled(state)
        self.action_reset_all_translations.setEnabled(state)
        self.action_translate.setEnabled(state)

        package = self.packages_storage.package
        self.action_finalize.setEnabled(state and package and package.is_package)
        self.action_finalize_as.setEnabled(state and package and package.is_package)

        color_signals.update.emit()
        self.colorbar.setVisible(config.value('view', 'colorbar') and state)

    def check_modified(self, multi: bool = False):
        package = self.packages_storage.package
        if multi and self.packages_storage.modified or not multi and package and package.modified:
            flags = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel

            response = QMessageBox.question(self,
                                            self.windowTitle(),
                                            interface.text('Messages', 'Save dictionary for modified packages?'),
                                            flags,
                                            QMessageBox.StandardButton.NoButton)

            if response == QMessageBox.Yes:
                self.dictionaries_storage.save(multi=multi)

            return response != QMessageBox.Cancel

        return True

    def load(self, filename: str, added: bool = False):
        if filename:
            if not self.dictionaries_storage.loaded:
                self.dictionaries_storage.load()
            self.packages_storage.load(filename, added)

    def open_file(self, added: bool = False):
        filename = open_supported(True)
        if filename:
            self.load(filename, added)

    def load_file(self):
        self.open_file()

    def add_file(self):
        self.open_file(True)

    def import_translation(self):
        filename = open_supported()
        if filename:
            found = False

            if filename.lower().endswith('.xml'):
                found = self.packages_storage.check_xml(filename)
            elif filename.lower().endswith('.stbl'):
                found = self.packages_storage.check_stbl(filename)
            elif filename.lower().endswith('.package'):
                found = self.packages_storage.check_package(filename)

            if found:
                self.import_dialog.filename = filename
                self.import_dialog.exec()
            else:
                QMessageBox.information(self, self.windowTitle(),
                                        interface.text('Messages', 'Not found text records in this file!'))

    def export_translation_stbl(self):
        self.export_dialog.stbl()

    def export_translation_xml(self):
        self.export_dialog.xml()

    def export_translation_xml_dp(self):
        self.export_dialog.xml_dp()

    def translate_from_dict(self):
        for item in self.main_model.items():
            if item.flag == FLAG_UNVALIDATED:
                translated = self.dictionaries_storage.search(source=item.source)
                if translated:
                    self.undo.wrap(item)
                    item.translate = translated[0]
                    item.flag = FLAG_PROGRESS if len(translated) > 1 else FLAG_TRANSLATED

        color_signals.update.emit()

        self.tableview.refresh()
        self.undo.commit()

    def batch_translate(self):
        self.translate_dialog.exec()

    def translate(self):
        item = self.tableview.selected_item()
        if item:
            self.__initiate_progress(interface.text('System', 'Translating...'), 0)
            response = translator.translate(config.value('api', 'engine'), item.source)
            if response.status_code == 200:
                self.undo.wrap(item)
                item.translate = response.text
                item.flag = FLAG_VALIDATED
                color_signals.update.emit()
                self.tableview.refresh()
                self.undo.commit()
                self.__finished_progress()

    def save_dictionary(self):
        self.dictionaries_storage.save(force=True)

    def save(self):
        package = self.packages_storage.package
        if package:
            package.save()
        else:
            self.save_as()

    def save_as(self):
        package = self.packages_storage.package
        filename = save_package(
            package.filename if package else 'translate_merged_' + config.value('translation',
                                                                                'destination'))
        if filename:
            self.packages_storage.save(filename)

    def finalize(self):
        package = self.packages_storage.package
        if package:
            package.finalize()

    def finalize_as(self):
        package = self.packages_storage.package
        if package:
            filename = save_package(package.name)
            if filename:
                package.finalize(filename)

    def load_bundle(self):
        filename = open_xml()
        if filename:
            if not self.dictionaries_storage.loaded:
                self.dictionaries_storage.load()
            self.packages_storage.load_bundle(filename)

    def save_bundle(self):
        filename = save_xml('packages_bundle')
        if filename:
            self.packages_storage.save_bundle(filename)

    def edit_string(self):
        item = self.tableview.selected_item()
        if item:
            self.edit_window.exec(item)

    def validate_selected(self, flag):
        if not self.packages_storage.enabled:
            return

        items = self.tableview.selected_items()
        for item in items:
            self.undo.wrap(item)
            item.flag = flag
            item.translate_old = None
            if flag == FLAG_UNVALIDATED:
                item.translate = item.source

        color_signals.update.emit()

        self.tableview.refresh()
        self.undo.commit()

    def validate_all(self, flag):
        if not self.packages_storage.enabled:
            return

        for item in self.main_model.items():
            self.undo.wrap(item)
            item.flag = flag
            item.translate_old = None
            if flag == FLAG_UNVALIDATED:
                item.translate = item.source

        color_signals.update.emit()

        self.tableview.refresh()
        self.undo.commit()

    def validate_0(self):
        self.validate_selected(FLAG_UNVALIDATED)

    def validate_0_all(self):
        self.validate_all(FLAG_UNVALIDATED)

    def validate_1(self):
        self.validate_selected(FLAG_PROGRESS)

    def validate_2(self):
        self.validate_selected(FLAG_VALIDATED)

    def validate_2_all(self):
        self.validate_all(FLAG_VALIDATED)

    def copy(self):
        item = self.tableview.selected_item()
        if item:
            pyperclip.copy(item.translate)

    def paste(self):
        if not self.packages_storage.enabled:
            return

        paste = pyperclip.paste()
        for item in self.tableview.selected_items():
            self.undo.wrap(item)
            item.translate = paste
            item.translate_old = None
            item.flag = FLAG_VALIDATED

        color_signals.update.emit()

        self.tableview.refresh()
        self.undo.commit()

    def close(self):
        package = self.packages_storage.package
        if self.check_modified(package is None):
            self.packages_storage.close()
            self.set_state_menu()

    def replace(self):
        if self.packages_storage.enabled:
            self.replace_dialog.exec()

    def options(self):
        dlg = OptionsDialog(self)
        dlg.exec()

    def colorbar_toggle(self):
        config.set_value('view', 'colorbar', self.action_colorbar.isChecked())
        self.set_state_menu()

    def group_change(self):
        self.action_group_original.setChecked(config.value('group', 'original'))
        self.action_group_highbit.setChecked(config.value('group', 'highbit'))
        self.action_group_lowbit.setChecked(config.value('group', 'lowbit'))

        for item in self.main_model.model.items:
            rid = item[RECORD_MAIN_RESOURCE_ORIGINAL]
            if not config.group_original:
                rid = item[RECORD_MAIN_RESOURCE_ORIGINAL].convert_group(highbit=config.group_high)
            item[RECORD_MAIN_GROUP] = rid.group
            item[RECORD_MAIN_RESOURCE] = rid

    def group_original(self):
        config.set_value('group', 'original', True)
        config.set_value('group', 'highbit', False)
        config.set_value('group', 'lowbit', False)
        self.group_change()

    def group_highbit(self):
        config.set_value('group', 'original', False)
        config.set_value('group', 'highbit', True)
        config.set_value('group', 'lowbit', False)
        self.group_change()

    def group_lowbit(self):
        config.set_value('group', 'original', False)
        config.set_value('group', 'highbit', False)
        config.set_value('group', 'lowbit', True)
        self.group_change()

    def num_change(self):
        numeration = config.value('view', 'numeration')
        self.action_num_standart.setChecked(numeration == NUMERATION_STANDART)
        self.action_num_source.setChecked(numeration == NUMERATION_SOURCE)
        self.action_num_xml_dp.setChecked(numeration == NUMERATION_XML_DP)
        self.tableview.refresh()

    def num_standart(self):
        config.set_value('view', 'numeration', NUMERATION_STANDART)
        self.num_change()

    def num_source(self):
        config.set_value('view', 'numeration', NUMERATION_SOURCE)
        self.num_change()

    def num_xml(self):
        config.set_value('view', 'numeration', NUMERATION_XML)
        self.num_change()

    def num_xml_dp(self):
        config.set_value('view', 'numeration', NUMERATION_XML_DP)
        self.num_change()

    def undo_restore(self):
        self.undo.restore()

    @staticmethod
    def about_qt():
        QApplication.instance().aboutQt()

    def generate_item_context_menu(self, position):
        index = self.sender().indexAt(position)
        if not index.isValid():
            return

        position.setY(position.y() + 22)

        context_menu = QMenu()

        edit_action = context_menu.addAction(icon('edit'), interface.text('MainWindow', 'Edit String'))
        edit_action.setShortcut('Enter')

        context_menu.addSeparator()

        validate_2_action = context_menu.addAction(icon('validate_2'),
                                                   interface.text('MainWindow', 'Validate as [translated]'))
        validate_2_action.setShortcut('F1')

        validate_1_action = context_menu.addAction(icon('validate_1'),
                                                   interface.text('MainWindow', 'Validate as [work in progress]'))
        validate_1_action.setShortcut('F2')

        validate_0_action = context_menu.addAction(icon('validate_0'),
                                                   interface.text('MainWindow', 'Cancel translation'))
        validate_0_action.setShortcut('F4')

        context_menu.addSeparator()

        copy_action = context_menu.addAction(icon('copy'), interface.text('MainWindow', 'Copy'))
        copy_action.setShortcut('Ctrl+C')

        paste_action = context_menu.addAction(icon('paste'), interface.text('MainWindow', 'Paste'))
        paste_action.setShortcut('Ctrl+V')

        context_menu.addSeparator()

        translate_action = context_menu.addAction(icon('api'), interface.text('MainWindow', 'Translate'))
        translate_action.setShortcut('Ctrl+T')

        action = context_menu.exec_(self.sender().mapToGlobal(position))
        if action is None:
            return

        if action == edit_action:
            self.edit_string()

        if action == copy_action:
            self.copy()

        if action == paste_action:
            self.paste()

        if action == translate_action:
            self.translate()

        if action == validate_2_action:
            self.validate_2()

        if action == validate_1_action:
            self.validate_1()

        if action == validate_0_action:
            self.validate_0()

    @Slot(str, int)
    def __initiate_progress(self, message: str, value: int):
        if value:
            self.progress_bar.setMaximum(value)
            self.progress_bar.setValue(0)
        else:
            self.progress_bar.setMaximum(0)
            self.progress_bar.setValue(-1)
        self.progress_label.setText(message)
        self.progress_widget.setVisible(True)
        QApplication.processEvents()

    @Slot()
    def __increment_progress(self):
        maximum = self.progress_bar.maximum()
        value = self.progress_bar.value() + 1
        if maximum and value <= maximum:
            self.progress_bar.setValue(value)
            QApplication.processEvents()

    @Slot()
    def __finished_progress(self):
        self.progress_bar.setValue(0)
        self.progress_widget.setVisible(False)

    @Slot()
    def __undo_refresh(self):
        self.action_undo.setEnabled(self.undo.available)
        self.tableview.refresh()

    @Slot()
    def __undo_clean_all(self):
        self.undo.clean()

    @Slot(str)
    def __undo_clean_by_key(self, key: str):
        self.undo.clean(key)
