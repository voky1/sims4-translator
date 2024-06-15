# -*- coding: utf-8 -*-

import os
import operator
import xml.etree.ElementTree as ElementTree
from PySide6.QtCore import Qt, QSize, QThreadPool
from PySide6.QtWidgets import QDialog
from typing import TYPE_CHECKING

from packer.stbl import Stbl

from .ui.exportdialog import Ui_ExportDialog

from singletons.interface import interface
from utils.functions import opendir, save_xml, save_stbl, text_to_stbl, text_to_edit, prettify
from utils.signals import progress_signals
from utils.constants import *


if TYPE_CHECKING:
    from windows.mainwindow import MainWindow


class ExportDialog(QDialog, Ui_ExportDialog):

    def __init__(self, parent: 'MainWindow'):
        super().__init__(parent)
        self.setupUi(self)

        self.main_window = parent

        self.__export = -1

        self.cb_current.clicked.connect(self.current_click)
        self.cb_separate.clicked.connect(self.separate_click)

        self.btn_export.clicked.connect(self.export_click)
        self.btn_cancel.clicked.connect(self.cancel_click)

        self.__pool = QThreadPool()
        self.__pool.setMaxThreadCount(1)

        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(interface.text('ExportDialog', 'Export translate'))
        self.gb_rec.setTitle(interface.text('ExportDialog', 'Exported records'))
        self.rb_all.setText(interface.text('ExportDialog', 'Everything'))
        self.rb_translated.setText(interface.text('ExportDialog', 'Everything but untranslated strings'))
        self.cb_current.setText(interface.text('ExportDialog', 'Only selected instance'))
        self.cb_separate.setText(interface.text('ExportDialog', 'Each instance as a separate file'))
        self.btn_export.setText(interface.text('ExportDialog', 'Export'))
        self.btn_cancel.setText(interface.text('ExportDialog', 'Cancel'))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.__export = -1

    def current_click(self):
        if self.cb_current.isChecked():
            self.cb_separate.setChecked(False)
            self.cb_separate.setEnabled(False)
        else:
            self.cb_separate.setEnabled(True)

    def separate_click(self):
        if self.cb_separate.isChecked():
            self.cb_current.setChecked(False)
            self.cb_current.setEnabled(False)
        else:
            self.cb_current.setEnabled(True)

    def stbl(self):
        self.export(EXPORT_STBL)

    def xml(self):
        self.export(EXPORT_XML)

    def xml_dp(self):
        self.export(EXPORT_XML_DP)

    def export(self, export):
        self.__export = export

        height = 134

        self.cb_current.setVisible(False)
        self.cb_separate.setVisible(False)

        package = self.main_window.packages_storage.package

        if package is not None and package.instance and len(package.instances) > 1:
            self.cb_current.setVisible(True)
            height += 24

        if self.__export != EXPORT_STBL and (package is None or len(package.instances) > 1):
            self.cb_separate.setVisible(True)
            height += 24

        self.setMinimumSize(QSize(390, height))
        self.resize(390, height)

        self.exec()

    def export_click(self):
        if self.__export < 0:
            return

        filename = None
        directory = None

        current = self.cb_current.isVisible() and self.cb_current.isChecked()
        separate = self.cb_separate.isVisible() and self.cb_separate.isChecked()

        main_model = self.main_window.main_model

        items = sorted(main_model.items(), key=operator.itemgetter(RECORD_MAIN_INDEX), reverse=False)

        package = self.main_window.packages_storage.package

        if self.__export == EXPORT_STBL:
            if package is not None and package.instance:
                items = main_model.items(instance=package.instance)
                item = items[0] if items else None
                if item:
                    filename = save_stbl(item.resource.filename)
            else:
                directory = opendir()
        else:
            if separate and not current:
                directory = opendir()
            else:
                if package is not None:
                    if current or package.instance and len(package.instances) > 1:
                        items = main_model.items(instance=package.instance)
                        item = items[0] if items else None
                        if item:
                            filename = save_xml(item.resource.filename)
                    else:
                        filename = save_xml(package.name)
                else:
                    filename = save_xml('translate_merged')

        if filename or directory:
            export_callback = None

            if self.__export == EXPORT_STBL:
                export_callback = self.export_stbl
            elif self.__export == EXPORT_XML:
                export_callback = self.export_xml
            elif self.__export == EXPORT_XML_DP:
                export_callback = self.export_xml_dp

            if export_callback:
                progress_signals.initiate.emit(interface.text('System', 'Exporting translate...'), len(items) / 100)
                export_callback(items, filename=filename, directory=directory, everything=self.rb_all.isChecked())
                progress_signals.finished.emit()

    def cancel_click(self):
        self.close()

    @staticmethod
    def export_stbl(items, directory=None, filename=None, everything=False):
        stbl = {}

        for i, item in enumerate(items):
            if i % 100 == 0:
                progress_signals.increment.emit()

            if not everything and item.flag == FLAG_UNVALIDATED:
                continue

            rid = item.resource.convert_instance()

            if rid not in stbl:
                stbl[rid] = Stbl(rid)

            stbl[rid].add(item.id, item.translate)

        if filename:
            for rid, inst in stbl.items():
                with open(filename, 'wb') as fp:
                    fp.write(inst.binary)
                break
        elif directory:
            for rid, inst in stbl.items():
                filename = os.path.join(directory, rid.filename + '.stbl')
                with open(filename, 'wb') as fp:
                    fp.write(inst.binary)

    @staticmethod
    def export_xml(items, directory=None, filename=None, everything=False):
        root = ElementTree.Element('STBLXMLResources')
        content = ElementTree.SubElement(root, 'Content')

        tables = {}

        for i, item in enumerate(items):
            if i % 100 == 0:
                progress_signals.increment.emit()

            if not everything and item.flag == FLAG_UNVALIDATED:
                continue

            rid = item.resource.convert_instance()

            if rid not in tables:
                tables[rid] = ElementTree.SubElement(content, 'Table')
                tables[rid].set('instance', rid.str_instance)
                tables[rid].set('group', rid.str_group)

            string = ElementTree.SubElement(tables[rid], 'String')
            string.set('id', '{id:08x}'.format(id=item.id))

            _source = ElementTree.SubElement(string, 'Source')
            _source.text = text_to_edit(item.source)

            _dest = ElementTree.SubElement(string, 'Dest')
            _dest.text = text_to_edit(item.translate)

            if item.comment:
                _comment = ElementTree.SubElement(string, 'Comment')
                _comment.text = item.comment

        if filename:
            with open(filename, 'wb') as fp:
                fp.write(prettify(root))
        elif directory:
            for rid, table in tables.items():
                filename = os.path.join(directory, rid.filename + '.xml')
                content.clear()
                content.append(table)
                with open(filename, 'wb') as fp:
                    fp.write(prettify(root))

    @staticmethod
    def export_xml_dp(items, directory=None, filename=None, everything=False):
        root = ElementTree.Element('StblData')
        content = ElementTree.SubElement(root, 'TextStringDefinitions')

        tables = {}

        for i, item in enumerate(items):
            if i % 100 == 0:
                progress_signals.increment.emit()

            if not everything and item.flag == FLAG_UNVALIDATED:
                continue

            rid = item.resource.convert_instance()

            if rid not in tables:
                tables[rid] = []

            string = ElementTree.SubElement(content, 'TextStringDefinition')
            string.set('InstanceID', '0x{id:08X}'.format(id=item.id))
            string.set('TextString', text_to_stbl(item.translate))

            tables[rid].append(string)

        if filename:
            with open(filename, 'wb') as fp:
                fp.write(prettify(root))
        elif directory:
            for rid, strings in tables.items():
                filename = os.path.join(directory, rid.filename + '.xml')
                content.clear()
                content.extend(strings)
                with open(filename, 'wb') as fp:
                    fp.write(prettify(root))
