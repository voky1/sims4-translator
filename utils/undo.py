# -*- coding: utf-8 -*-

from collections import namedtuple

from storages.records import MainRecord

from utils.signals import undo_signals


class UndoRecord(namedtuple('UndoRecord', 'items modified')):

    items: list
    modified: bool

    def restore(self):
        for item in self.items:
            item[0].translate = item[1]
            item[0].translate_old = item[2]
            item[0].comment = item[3]
            item[0].flag = item[4]

class Undo:

    def __init__(self, parent=None):
        self.__storage = parent.packages_storage
        self.__undo = []
        self.__wrapper = []

    @property
    def available(self) -> bool:
        return len(self.__undo) > 0

    def wrap(self, item: MainRecord) -> None:
        self.__wrapper.append((item, item.translate, item.translate_old, item.comment, item.flag))

    def commit(self) -> None:
        if not self.__wrapper:
            return

        packages = {}
        for item in self.__wrapper:
            package_key = item[0].package
            packages.setdefault(package_key, []).append(item)

        undo = {}
        for key, items in packages.items():
            package = self.__storage.find(key)
            undo[key] = UndoRecord(items=items, modified=package.modified)
            package.modify()

        self.__undo = self.__undo[-20:] + [undo]

        self.__wrapper = []

        undo_signals.refresh.emit()

    def restore(self) -> None:
        if self.available:
            for key, undo in self.__undo[-1].items():
                package = self.__storage.find(key)
                if package:
                    undo.restore()
                    package.modify(undo.modified if package.modified else True)
            del self.__undo[-1]
            undo_signals.refresh.emit()

    def clean(self, key: str = None) -> None:
        __undo = []

        if key:
            __undo = []
            for undo in self.__undo:
                if key in undo:
                    del undo[key]
                if undo:
                    __undo.append(undo)

        self.__undo = __undo

        undo_signals.refresh.emit()
