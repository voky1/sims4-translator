# -*- coding: utf-8 -*-

import os
import operator
import xml.etree.ElementTree as ElementTree
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog
from typing import List

from packer.stbl import Stbl

from storages.records import MainRecord

from .ui.export_dialog import Ui_ExportDialog

from singletons.interface import interface
from singletons.signals import progress_signals
from singletons.state import app_state
from utils.functions import opendir, save_xml, save_stbl, text_to_stbl, text_to_edit, prettify
from utils.constants import *


class ExportDialog(QDialog, Ui_ExportDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.__export = -1

        self.cb_current_instance.clicked.connect(self.current_instance_click)
        self.cb_separate_instances.clicked.connect(self.separate_instances_click)
        self.cb_separate_packages.clicked.connect(self.separate_packages_click)

        self.btn_export.clicked.connect(self.export_click)
        self.btn_cancel.clicked.connect(self.cancel_click)

        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(interface.text('ExportDialog', 'Export translate'))
        self.gb_rec.setTitle(interface.text('ExportDialog', 'Exported records'))
        self.rb_all.setText(interface.text('ExportDialog', 'Everything'))
        self.rb_translated.setText(interface.text('ExportDialog', 'Everything but untranslated strings'))
        self.cb_current_instance.setText(interface.text('ExportDialog', 'Only selected instance'))
        self.cb_separate_instances.setText(interface.text('ExportDialog', 'Each instance as a separate file'))
        self.cb_separate_packages.setText(interface.text('ExportDialog', 'Each package as a separate file'))
        self.btn_export.setText(interface.text('ExportDialog', 'Export'))
        self.btn_cancel.setText(interface.text('ExportDialog', 'Cancel'))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.__export = -1

    def current_instance_click(self):
        if self.cb_current_instance.isChecked():
            self.cb_separate_instances.setChecked(False)
            self.cb_separate_instances.setEnabled(False)
            self.cb_separate_packages.setChecked(False)
            self.cb_separate_packages.setEnabled(False)
        else:
            self.cb_separate_instances.setEnabled(True)
            self.cb_separate_packages.setEnabled(True)

    def separate_instances_click(self):
        if self.cb_separate_instances.isChecked():
            self.cb_current_instance.setChecked(False)
            self.cb_current_instance.setEnabled(False)
            self.cb_separate_packages.setChecked(False)
            self.cb_separate_packages.setEnabled(False)
        else:
            self.cb_current_instance.setEnabled(True)
            self.cb_separate_packages.setEnabled(True)

    def separate_packages_click(self):
        if self.cb_separate_packages.isChecked():
            self.cb_current_instance.setChecked(False)
            self.cb_current_instance.setEnabled(False)
            self.cb_separate_instances.setChecked(False)
            self.cb_separate_instances.setEnabled(False)
        else:
            self.cb_current_instance.setEnabled(True)
            self.cb_separate_instances.setEnabled(True)

    def stbl(self):
        self.__exec(EXPORT_STBL)

    def xml(self):
        self.__exec(EXPORT_XML)

    def xml_dp(self):
        self.__exec(EXPORT_XML_DP)

    def __exec(self, export: int):
        self.__export = export

        self.cb_current_instance.setVisible(False)
        self.cb_separate_instances.setVisible(False)
        self.cb_separate_packages.setVisible(False)

        package = app_state.packages_storage.current_package
        instance = app_state.packages_storage.current_instance

        if package is not None and instance > 0 and len(package.instances) > 1:
            self.cb_current_instance.setVisible(True)

        if self.__export != EXPORT_STBL:
            if not package or len(package.instances) > 1:
                self.cb_separate_instances.setVisible(True)

            if not package:
                self.cb_separate_packages.setVisible(True)

        self.setMinimumHeight(0)
        self.adjustSize()
        self.setMinimumSize(self.size())

        self.exec()

    def export(self):
        filename = None
        directory = None

        current_instance = self.cb_current_instance.isVisible() and self.cb_current_instance.isChecked()
        separate_instances = self.cb_separate_instances.isVisible() and self.cb_separate_instances.isChecked()
        separate_packages = self.cb_separate_packages.isVisible() and self.cb_separate_packages.isChecked()

        items = app_state.packages_storage.model.items

        package = app_state.packages_storage.current_package
        instance = app_state.packages_storage.current_instance

        one_instance = package is not None and instance > 0 and len(package.instances) == 1

        if self.__export == EXPORT_STBL:
            if one_instance or current_instance and package:
                items = app_state.packages_storage.items(instance=instance)
                item = items[0] if items else None
                if item:
                    filename = save_stbl(item.resource.filename)
            else:
                directory = opendir()
        else:
            if separate_instances or separate_packages:
                directory = opendir()
            else:
                if one_instance or current_instance and package:
                    items = app_state.packages_storage.items(instance=instance)
                    item = items[0] if items else None
                    if item:
                        filename = save_xml(item.resource.filename)
                elif package:
                    items = app_state.packages_storage.items(key=package.key)
                    filename = save_xml(package.name)
                else:
                    filename = save_xml('translate_merged')

        items = sorted(items, key=operator.itemgetter(RECORD_MAIN_INDEX), reverse=False)

        if filename or directory:
            progress_signals.initiate.emit(interface.text('System', 'Exporting translate...'), len(items) / 100)

            if self.__export == EXPORT_XML:
                self.export_xml(items, filename=filename, directory=directory)
            elif self.__export == EXPORT_XML_DP:
                self.export_xml_dp(items, filename=filename, directory=directory)
            else:
                self.export_stbl(items, filename=filename, directory=directory)

            progress_signals.finished.emit()

    def export_click(self):
        self.export()
        self.close()

    def cancel_click(self):
        self.close()

    def export_stbl(self, items: List[MainRecord], directory: str = None, filename: str = None) -> None:
        stbl = {}

        for i, item in enumerate(items):
            if i % 100 == 0:
                progress_signals.increment.emit()

            if not self.rb_all.isChecked() and item.flag == FLAG_UNVALIDATED:
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

    def export_xml(self, items: List[MainRecord], directory: str = None, filename: str = None) -> None:
        root = ElementTree.Element('STBLXMLResources')
        content = ElementTree.SubElement(root, 'Content')

        packages = {}
        tables = {}

        separate_packages = self.cb_separate_packages.isVisible() and self.cb_separate_packages.isChecked()

        for i, item in enumerate(items):
            if i % 100 == 0:
                progress_signals.increment.emit()

            if not self.rb_all.isChecked() and item.flag == FLAG_UNVALIDATED:
                continue

            rid = item.resource.convert_instance()

            if separate_packages:
                if item.package not in packages:
                    packages[item.package] = {}

                if rid not in packages[item.package]:
                    packages[item.package][rid] = ElementTree.SubElement(content, 'Table')
                    packages[item.package][rid].set('instance', rid.str_instance)
                    packages[item.package][rid].set('group', rid.str_group)

                string = ElementTree.SubElement(packages[item.package][rid], 'String')

            else:
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
            if separate_packages:
                for key, tables in packages.items():
                    package = app_state.packages_storage.find(key)
                    filename = os.path.join(directory, package.name + '.xml')
                    content.clear()
                    for rid, table in tables.items():
                        content.append(table)
                    with open(filename, 'wb') as fp:
                        fp.write(prettify(root))
            else:
                for rid, table in tables.items():
                    filename = os.path.join(directory, rid.filename + '.xml')
                    content.clear()
                    content.append(table)
                    with open(filename, 'wb') as fp:
                        fp.write(prettify(root))

    def export_xml_dp(self, items: List[MainRecord], directory: str = None, filename: str = None) -> None:
        root = ElementTree.Element('StblData')
        content = ElementTree.SubElement(root, 'TextStringDefinitions')

        packages = {}
        tables = {}

        separate_packages = self.cb_separate_packages.isVisible() and self.cb_separate_packages.isChecked()

        for i, item in enumerate(items):
            if i % 100 == 0:
                progress_signals.increment.emit()

            if not self.rb_all.isChecked() and item.flag == FLAG_UNVALIDATED:
                continue

            rid = item.resource.convert_instance()

            if separate_packages:
                if item.package not in packages:
                    packages[item.package] = {}
                if rid not in packages[item.package]:
                    packages[item.package][rid] = []
                strings = packages[item.package][rid]
            else:
                if rid not in tables:
                    tables[rid] = []
                strings = tables[rid]

            string = ElementTree.SubElement(content, 'TextStringDefinition')
            string.set('InstanceID', '0x{id:08X}'.format(id=item.id))
            string.set('TextString', text_to_stbl(item.translate))

            strings.append(string)

        if filename:
            with open(filename, 'wb') as fp:
                fp.write(prettify(root))
        elif directory:
            if separate_packages:
                for key, tables in packages.items():
                    package = app_state.packages_storage.find(key)
                    filename = os.path.join(directory, package.name + '.xml')
                    content.clear()
                    for rid, strings in tables.items():
                        content.extend(strings)
                    with open(filename, 'wb') as fp:
                        fp.write(prettify(root))
            else:
                for rid, strings in tables.items():
                    filename = os.path.join(directory, rid.filename + '.xml')
                    content.clear()
                    content.extend(strings)
                    with open(filename, 'wb') as fp:
                        fp.write(prettify(root))
