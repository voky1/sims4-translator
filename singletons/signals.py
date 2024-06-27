# -*- coding: utf-8 -*-

from PySide6.QtCore import QObject, Signal


class ProgressSignals(QObject):
    initiate = Signal(str, int)
    increment = Signal()
    finished = Signal()


class WindowSignals(QObject):
    message = Signal(str)


class ColorSignals(QObject):
    update = Signal()


class StorageSignals(QObject):
    updated = Signal()


progress_signals = ProgressSignals()
window_signals = WindowSignals()
color_signals = ColorSignals()
storage_signals = StorageSignals()
