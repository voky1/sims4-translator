# -*- coding: utf-8 -*-

import os
import zlib
import json
import glob
from PySide6.QtCore import Qt, QThreadPool, QRunnable, Slot
from typing import TYPE_CHECKING

from packer import Packer

from singletons.config import config
from singletons.interface import interface
from utils.signals import progress_signals, dictionary_signals
from utils.functions import text_to_stbl
from utils.constants import *


if TYPE_CHECKING:
    from windows.mainwindow import MainWindow


class UpdaterWorker(QRunnable):

    def __init__(self, item, storage):
        super().__init__()

        self.storage = storage
        self.item = item

    def run(self):
        source = text_to_stbl(self.item.source)
        translate = text_to_stbl(self.item.translate)
        found = self._update_or_append(source, translate)
        if not found:
            self.storage.dictionary_model.append(['-', source, translate, len(source)])
        self.storage.edit_window.tableview.resort()

    def _update_or_append(self, source, translate):
        for model_item in self.storage.dictionary_model.model.items:
            if model_item[RECORD_DICTIONARY_SOURCE] == source and model_item[RECORD_DICTIONARY_PACKAGE] == '-':
                model_item[RECORD_DICTIONARY_TRANSLATE] = translate
                model_item[RECORD_DICTIONARY_LENGTH] = 0
                return True
        return False


class DictionariesStorage:

    def __init__(self, parent: 'MainWindow') -> None:
        self.main_window = parent
        self.edit_window = parent.edit_window
        self.dictionary_model = parent.dictionary_model

        self.directory = config.value('dictionaries', 'dictpath')
        if not self.directory:
            self.directory = os.path.abspath('./dictionaries')

        self.__loaded = False

        self.__sid = {}
        self.__sources = {}
        self.__hash = {}

        self.__pool = QThreadPool()

        dictionary_signals.update.connect(self.update)

    @property
    def loaded(self) -> bool:
        return self.__loaded

    def search(self, sid: int = None, source: str = None) -> list:
        if sid:
            return self.__sid.get(sid, [])
        elif source:
            return self.__sources.get(source, [])
        return []

    def load(self):
        dictionary_files = glob.glob(os.path.join(self.directory, '*.dct'))

        if dictionary_files:
            progress_signals.initiate.emit(interface.text('System', 'Loading dictionaries...'), len(dictionary_files))

            for filename in dictionary_files:
                dictionary_name = os.path.splitext(os.path.basename(filename))[0]

                with open(filename, 'rb') as fp:
                    packer = Packer(fp.read(), mode='r')

                if packer.get_raw_bytes(3) == b'DCT':
                    version = packer.get_byte()
                    items = packer.get_json()
                else:
                    content = zlib.decompress(packer.get_content()).decode('utf-8')
                    version = 1
                    items = json.loads(content)

                self.read_dictionary(dictionary_name, version, items)

                progress_signals.increment.emit()

            self.dictionary_model.append(list(self.__hash.values()))
            self.edit_window.tableview.sortByColumn(COLUMN_DICTIONARIES_LENGTH, Qt.SortOrder.AscendingOrder)

            self.__hash = {}

            progress_signals.finished.emit()

        self.__loaded = True

    def read_dictionary(self, dictionary_name: str, version: int, items: list) -> None:
        name = dictionary_name.lower()

        for i, item in enumerate(items):
            if version == 1:
                item[0] = int(item[0], 16)
                item.append(0)

            if version < 3:
                item.append('')

            if version < 4:
                item.pop(3)

            if item[1] and item[1] != item[2]:
                self.update_hash(name, item)

    def update_hash(self, name: str, item: list):
        self.__sid.setdefault(item[0], []).append((name, item[1], item[2], item[3]))

        sources = self.__sources.get(item[1], [])
        if item[2] not in sources:
            sources.append(item[2])
            self.__sources[item[1]] = sources

        k = f'{item[1]}__{item[2]}'
        if k not in self.__hash:
            self.__hash[k] = [name, item[1], item[2], len(item[1])]

    @Slot(object)
    def update(self, item):
        if not item.compare():
            worker = UpdaterWorker(item, self)
            worker.setAutoDelete(True)
            self.__pool.start(worker)

    def save(self, force: bool = False, multi: bool = False):
        model = self.main_window.main_model
        storage = self.main_window.packages_storage
        package = storage.package
        if multi or package is None:
            for p in storage.packages:
                if p.modified or force:
                    self.save_standalone(p.name, model.items(key=p.key))
                    p.modify(False)
        elif package is not None and (package.modified or force):
            self.save_standalone(package.name, model.items(key=package.key))
            package.modify(False)

    def save_standalone(self, name, items):
        if not os.path.isdir(self.directory):
            os.mkdir(self.directory)

        path = os.path.join(self.directory, name + '.dct')

        f = Packer(b'', mode='w')

        f.put_raw_bytes(b'DCT')
        f.put_byte(DICTIONARY_VERSION)

        _items = []

        for item in items:
            if item.flag != FLAG_UNVALIDATED and item.source:
                _items.append([
                    item.id,
                    text_to_stbl(item.source),
                    text_to_stbl(item.translate),
                    item.comment
                ])

        f.put_json(_items)

        with open(path, 'w+b') as fp:
            fp.write(f.get_content())
