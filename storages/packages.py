# -*- coding: utf-8 -*-

import os
import operator
import pathlib
import gc
import xml.etree.ElementTree as ElementTree
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from typing import Union, Dict, List
from pathlib import Path

from packer.dbpf import DbpfPackage
from packer.resource import ResourceID
from packer.stbl import Stbl

from .container import Container
from .records import MainRecord

from models.main import Model, ProxyModel

from singletons.config import config
from singletons.interface import interface
from singletons.signals import progress_signals, window_signals
from singletons.state import app_state
from singletons.undo import undo
from utils.functions import text_to_stbl, compare, fnv64, prettify, create_temporary_copy
from utils.constants import *


class StorageSignals(QObject):
    loaded = Signal(list)
    closed = Signal(str)
    cleared = Signal()


class PackagesStorage:

    def __init__(self) -> None:
        self.packages: List[Container] = []

        self.model = Model()
        self.proxy = ProxyModel()
        self.proxy.setSourceModel(self.model)

        self.signals = StorageSignals()

    def find(self, key: str) -> Union[Container, None]:
        for package in self.packages:
            if package.key == key:
                return package
        return None

    def exists(self, key: str) -> bool:
        package = self.find(key)
        return package is not None

    @property
    def current_package(self) -> Container:
        key = app_state.current_package
        return self.find(key) if key else None

    @property
    def current_instance(self) -> int:
        return app_state.current_instance

    @property
    def modified(self) -> bool:
        for package in self.packages:
            if package.modified:
                return True
        return False

    @property
    def enabled(self) -> bool:
        return len(self.packages) > 0

    @property
    def multiplied(self) -> bool:
        return len(self.packages) > 1

    def modify(self, state: bool = True) -> None:
        for package in self.packages:
            package.modify(state)

    def items(self, key: str = None, instance: int = 0) -> List[MainRecord]:
        items = self.model.items

        if key or instance:
            if instance > 0:
                items = [i for i in items if i.instance == instance]
            elif key:
                items = [i for i in items if i.package == key]

        else:
            package_key = app_state.current_package
            package_instance = app_state.current_instance

            if package_instance > 0:
                items = [i for i in items if i.instance == package_instance]
            elif package_key:
                items = [i for i in items if i.package == package_key]

        return items

    def load(self, files: Union[list, str], added: bool = False) -> None:
        if not isinstance(files, list):
            files = [files]

        if not added:
            self.close()

        if len(files) > 1:
            progress_signals.initiate.emit(interface.text('System', 'Opening files...'), 0)
        else:
            progress_signals.initiate.emit(interface.text('System', 'Opening file...'), 0)

        idx_all = len(self) + 1

        loaded = []
        items = []
        empty = []

        dictionaries_storage = app_state.dictionaries_storage
        strong_dict = config.value('dictionaries', 'strong')
        group_original = config.value('group', 'original')
        group_highbit = config.value('group', 'highbit')

        for file in files:
            package = Container(file)

            if self.exists(package.key):
                continue

            strings = package.open()

            if strings:
                progress_signals.initiate.emit(
                    interface.text('System', 'Opening file {}...').format(package.fullname),
                    len(strings) / 100)

                for i, string in enumerate(strings):
                    if i % 100 == 0:
                        progress_signals.increment.emit()

                    flag = FLAG_UNVALIDATED

                    rid = string[0]
                    sid = string[1]
                    source = text_to_stbl(string[2])
                    dest = text_to_stbl(string[3])
                    comment = string[4]
                    line_source = string[5]
                    line_instance = string[5]
                    old = None

                    if not package.is_package:
                        flag = FLAG_TRANSLATED
                    else:
                        _translated = dictionaries_storage.search(sid=sid)
                        if _translated:
                            translated = [t for t in _translated if t[0].lower() == package.name.lower()]
                            if not translated and not strong_dict:
                                translated = _translated
                            if translated:
                                tr = translated[0]
                                dest = tr[2]
                                comment = tr[3]
                                flag = FLAG_TRANSLATED
                                if len(translated) > 1:
                                    flag = FLAG_PROGRESS
                                if not compare(tr[1], source):
                                    old = tr[1]
                        elif not strong_dict:
                            _translated = dictionaries_storage.search(source=source)
                            if _translated:
                                dest = _translated[0]
                                flag = FLAG_TRANSLATED
                                if len(_translated) > 1:
                                    flag = FLAG_PROGRESS

                    __rid = rid
                    if not group_original:
                        __rid = rid.convert_group(highbit=group_highbit)

                    items.append(MainRecord(
                        idx_all,
                        sid,
                        __rid.instance,
                        __rid.group,
                        source,
                        dest,
                        flag,
                        __rid,
                        rid,
                        package.key,
                        old,
                        None,
                        (i + 1, line_source, i + 4, line_instance + 3),
                        comment
                    ))
                    idx_all += 1

                self.packages.append(package)
                loaded.append(package.key)

            else:
                empty.append(package.name)

        if items:
            self.model.append(items)

        progress_signals.finished.emit()

        if empty:
            if len(files) == 1:
                window_signals.message.emit(interface.text('Messages', 'Not found text records in this file!'))
            elif len(files) == len(empty):
                window_signals.message.emit(interface.text('Messages', 'Not found text records in this files!'))
            else:
                names = "\n".join(empty)
                window_signals.message.emit(
                    interface.text('Messages', 'Not found text records in following files:') + "\n\n{}".format(names))

        self.signals.loaded.emit(loaded)

    def load_bundle(self, filename: str) -> None:
        if not os.path.exists(filename):
            return

        with open(filename, 'r', encoding='utf-8') as fp:
            content = fp.read()

        try:
            parser = ElementTree.XMLParser(encoding='utf-8')
            tree = ElementTree.fromstring(content, parser=parser)
        except ElementTree.ParseError:
            return

        files = []

        if tree.findall('Content/File'):
            prefix = tree.find('Content').get('prefix')
            prefix = prefix if prefix else ''
            for s in tree.findall('Content/File'):
                files.append(os.path.abspath(os.path.join(prefix, s.get('path'))))

        if files:
            self.load(files)

    def save_bundle(self, filename: str) -> None:
        root = ElementTree.Element('XMLPackages')
        content = ElementTree.SubElement(root, 'Content')

        packages = [str(Path(p.path).resolve()) for p in self.packages]
        packages.sort()

        try:
            common_prefix = os.path.commonpath(packages)
            content.set('prefix', str(common_prefix))
        except ValueError:
            common_prefix = None

        for f in packages:
            relative_path = Path(f).relative_to(common_prefix) if common_prefix else f
            string = ElementTree.SubElement(content, 'File')
            string.set('path', str(relative_path))

        with open(filename, 'wb') as fp:
            fp.write(prettify(root))

    def get_stbl(self, convert: bool = True) -> Dict[ResourceID, Stbl]:
        stbl = {}

        items = sorted(self.model.items, key=operator.itemgetter(RECORD_MAIN_INDEX), reverse=False)

        experemental = config.value('save', 'experemental')

        for item in items:
            rid = item.resource

            if convert and experemental:
                if item.flag == FLAG_UNVALIDATED:
                    continue
                rid = ResourceID(group=rid.group,
                                 type=rid.type,
                                 instance=fnv64('translator:' + os.path.abspath('.') + rid.str_instance))

            rid = rid.convert_instance()
            if rid not in stbl:
                stbl[rid] = Stbl(rid)

            stbl[rid].add(item.id, item.translate)

        return stbl

    def save(self, path):
        stbl = self.get_stbl()

        progress_signals.initiate.emit(
            interface.text('System', 'Saving package {}...').format(os.path.basename(path)),
            len(stbl.keys()))

        with DbpfPackage.write(path) as outpkg:
            for rid, inst in stbl.items():
                outpkg.put(rid, inst.binary)
                progress_signals.increment.emit()

        progress_signals.finished.emit()

    def finalize(self, fpath, tpath):
        fpath = os.path.abspath(fpath)
        tpath = os.path.abspath(tpath)

        if not os.path.exists(fpath):
            return

        stbl = self.get_stbl(convert=False)

        with open(fpath, 'rb') as f:
            magic = f.read(4)

        if magic == b'DBPF':
            is_temp = False

            if config.value('save', 'backup') and fpath.lower() == tpath.lower():
                fpath = self.current_package.backup(fpath)
            else:
                fpath = create_temporary_copy(fpath)
                is_temp = True

            dbfile = DbpfPackage(fpath, mode='r')
            outpkg = DbpfPackage(tpath, mode='w')

            instances = dbfile.search()

            progress_signals.initiate.emit(
                interface.text('System', 'Saving package {}...').format(os.path.basename(tpath)),
                len(instances))

            language_dest = config.value('translation', 'destination')

            for rid in instances:
                if rid.language == language_dest:
                    for r, s in stbl.items():
                        if r.group == rid.group and r.instance == rid.instance:
                            outpkg.put(r, s.binary)
                            del stbl[r]
                            break
                else:
                    content = dbfile[rid].content
                    if content:
                        outpkg.put(rid, content)

                progress_signals.increment.emit()

            dbfile.close()

            if is_temp:
                file_to_rem = pathlib.Path(fpath)
                file_to_rem.unlink()

            for rid, s in stbl.items():
                outpkg.put(rid, s.binary)

            outpkg.commit()

            progress_signals.finished.emit()

    def close(self) -> None:
        if not self.packages:
            return

        package_key = app_state.current_package

        if package_key and len(self.packages) > 1:
            undo.clean(package_key)

            items = []

            idx = 1
            for item in self.model.items:
                if item.package != package_key:
                    item.idx = idx
                    items.append(item)
                    idx += 1
                else:
                    item.clear()

            self.model.replace(items)

            self.packages = [p for p in self.packages if p.key != package_key]

            self.signals.closed.emit(package_key)

        else:
            undo.clean()
            self.model.clear()
            self.packages.clear()
            self.signals.cleared.emit()

        gc.collect()

    def __len__(self) -> int:
        return sum(len(p) for p in self.packages)

    @staticmethod
    def check_package(path):
        if not os.path.exists(path):
            return False

        with DbpfPackage.read(path) as dbfile:
            stbl = dbfile.search_stbl()
            return len(stbl) > 0

    @staticmethod
    def check_stbl(path):
        if not os.path.exists(path):
            return False

        with open(path, 'rb') as f:
            if f.read(4) == b'STBL':
                return True

        return False

    @staticmethod
    def check_xml(path):
        if not os.path.exists(path):
            return False

        with open(path, 'r', encoding='utf-8') as fp:
            content = fp.read()
            try:
                parser = ElementTree.XMLParser(encoding='utf-8')
                tree = ElementTree.fromstring(content, parser=parser)
                if tree.findall('TextStringDefinitions/TextStringDefinition') or tree.findall('Content/Table/String'):
                    return True
            except ElementTree.ParseError:
                return False

        return False

    @staticmethod
    def read_package(path):
        if not os.path.exists(path):
            return {}

        table = {}

        language_dest = config.value('translation', 'destination')

        with DbpfPackage.read(path) as dbfile:
            for rid in dbfile.search_stbl():
                if rid.language == language_dest:
                    stbl = Stbl(rid=rid, value=dbfile[rid].content)
                    for sid, value in stbl.strings.items():
                        if value:
                            QApplication.processEvents()
                            table[sid] = value

        return table

    @staticmethod
    def read_stbl(path):
        if not os.path.exists(path):
            return {}

        table = {}

        with open(path, 'rb') as fp:
            filename = os.path.basename(path)
            filename = os.path.splitext(filename)[0]
            stbl = Stbl(ResourceID.from_string(filename), value=fp.read())
            for sid, value in stbl.strings.items():
                if value:
                    QApplication.processEvents()
                    table[sid] = value

        return table

    @staticmethod
    def read_xml(path):
        if not os.path.exists(path):
            return {}

        with open(path, 'r', encoding='utf-8') as fp:
            content = fp.read()

        try:
            parser = ElementTree.XMLParser(encoding='utf-8')
            tree = ElementTree.fromstring(content, parser=parser)
        except ElementTree.ParseError:
            return {}

        table = {}

        if tree.findall('TextStringDefinitions/TextStringDefinition'):
            for s in tree.findall('TextStringDefinitions/TextStringDefinition'):
                QApplication.processEvents()
                sid = int(s.get('InstanceID'), 16)
                source = text_to_stbl(s.get('TextString'))
                table[sid] = source
        else:
            for s in tree.findall('Content/Table/String'):
                QApplication.processEvents()
                sid = int(s.get('id'), 16)
                table[sid] = text_to_stbl(s.find('Dest').text)

        return table


packages_storage = PackagesStorage()
