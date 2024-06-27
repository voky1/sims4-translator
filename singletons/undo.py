# -*- coding: utf-8 -*-

from collections import namedtuple
from PySide6.QtCore import QObject, Signal

from storages.records import MainRecord

from singletons.state import app_state


class UndoSignals(QObject):
    updated = Signal()
    restored = Signal()


class UndoRecord(namedtuple('UndoRecord', 'items modified')):

    def restore(self):
        for item in self.items:
            item[0].translate = item[1]
            item[0].translate_old = item[2]
            item[0].comment = item[3]
            item[0].flag = item[4]


class Undo:

    def __init__(self):
        self.__records = []
        self.__wrapper = []

        self.signals = UndoSignals()

    @property
    def available(self) -> bool:
        return len(self.__records) > 0

    def wrap(self, item: MainRecord) -> None:
        self.__wrapper.append((item, item.translate, item.translate_old, item.comment, item.flag))

    def commit(self) -> None:
        if not self.__wrapper:
            return

        packages = {}
        for item in self.__wrapper:
            package_key = item[0].package
            packages.setdefault(package_key, []).append(item)

        records = {}
        for key, items in packages.items():
            package = app_state.packages_storage.find(key)
            records[key] = UndoRecord(items=items, modified=package.modified)
            package.modify()

        self.__records = self.__records[-20:] + [records]

        self.__wrapper = []

        self.signals.updated.emit()

    def restore(self) -> None:
        if self.available:
            for key, record in self.__records[-1].items():
                package = app_state.packages_storage.find(key)
                if package:
                    record.restore()
                    package.modify(record.modified if package.modified else True)
            del self.__records[-1]
            self.signals.restored.emit()

    def clean(self, key: str = None) -> None:
        __records = []

        if key:
            for records in self.__records:
                if key in records:
                    del records[key]
                if records:
                    __records.append(records)

        self.__records = __records

        self.signals.updated.emit()


undo = Undo()
