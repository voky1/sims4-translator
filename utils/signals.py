# -*- coding: utf-8 -*-

from PySide6.QtCore import QObject, Signal


class Singleton(type(QObject), type):

    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class ProgressSignals(QObject, metaclass=Singleton):
    initiate = Signal(str, int)
    finished = Signal()
    increment = Signal()


class UndoSignals(QObject, metaclass=Singleton):
    refresh = Signal()
    clean_all = Signal()
    clean_by_key = Signal(str)


class DictionarySignals(QObject, metaclass=Singleton):
    update = Signal(object)


progress_signals = ProgressSignals()
undo_signals = UndoSignals()
dictionary_signals = DictionarySignals()
