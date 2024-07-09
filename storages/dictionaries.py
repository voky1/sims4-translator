# -*- coding: utf-8 -*-

import os
import zlib
import json
import glob
from PySide6.QtCore import QObject, Signal, QThreadPool, QRunnable

from packer import Packer

from models.dictionary import Model, ProxyModel

from singletons.config import config
from singletons.interface import interface
from singletons.signals import progress_signals, storage_signals
from singletons.state import app_state
from utils.functions import text_to_stbl
from utils.constants import *


class StorageSignals(QObject):
    updated = Signal()


class UpdaterWorker(QRunnable):

    def __init__(self, item):
        super().__init__()

        self.item = item

        self.signals = StorageSignals()

    def run(self):
        source = text_to_stbl(self.item.source)
        translate = text_to_stbl(self.item.translate)
        found = self._update_or_append(source, translate)
        if not found:
            app_state.dictionaries_storage.model.append(['-', source, translate, len(source)])
        storage_signals.updated.emit()

    @staticmethod
    def _update_or_append(source, translate):
        for model_item in app_state.dictionaries_storage.model.items:
            if model_item[RECORD_DICTIONARY_SOURCE] == source and model_item[RECORD_DICTIONARY_PACKAGE] == '-':
                model_item[RECORD_DICTIONARY_TRANSLATE] = translate
                return True
        return False


class DictionariesStorage:

    def __init__(self) -> None:
        self.model = Model()
        self.proxy = ProxyModel()
        self.proxy.setSourceModel(self.model)

        self.directory = config.value('dictionaries', 'dictpath')
        if not self.directory:
            self.directory = os.path.abspath('./dictionary')

        self.loaded = False

        self.signals = StorageSignals()

        self.__sid = {}
        self.__sources = {}
        self.__hash = {}

        self.__pool = QThreadPool()

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

            self.model.append(list(self.__hash.values()))
            self.signals.updated.emit()

            self.__hash.clear()

            progress_signals.finished.emit()

        self.loaded = True

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

        if item[1] not in self.__sources:
            self.__sources[item[1]] = []
        if item[2] not in self.__sources[item[1]]:
            self.__sources[item[1]].append(item[2])

        k = f'{item[1]}__{item[2]}'
        if k not in self.__hash:
            self.__hash[k] = [name, item[1], item[2], len(item[1])]

    def update(self, item):
        if not item.compare():
            worker = UpdaterWorker(item)
            worker.setAutoDelete(True)
            self.__pool.start(worker)

    def save(self, force: bool = False, multi: bool = False):
        storage = app_state.packages_storage
        package = storage.current_package
        if multi or package is None:
            for p in storage.packages:
                if p.modified or force:
                    self.save_standalone(p.name, storage.items(key=p.key))
                    p.modify(False)
        elif package is not None and (package.modified or force):
            self.save_standalone(package.name, storage.items(key=package.key))
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
