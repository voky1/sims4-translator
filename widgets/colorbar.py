# -*- coding: utf-8 -*-

from PySide6.QtCore import QObject, QThreadPool, QRunnable, Signal, Slot
from PySide6.QtWidgets import QWidget, QFrame, QHBoxLayout
from typing import TYPE_CHECKING

from utils.signals import color_signals
from utils.constants import *


if TYPE_CHECKING:
    from windows.mainwindow import MainWindow


class UpdateSignals(QObject):
    finished = Signal(int, int, int, int)


class UpdateWorker(QRunnable):

    def __init__(self, items):
        super().__init__()

        self.items = items

        self.signals = UpdateSignals()

    def run(self):
        translated_count = 0
        validated_count = 0
        progess_count = 0
        unvalidated_count = 0

        for item in self.items:
            flag = item.flag
            if flag == FLAG_TRANSLATED:
                translated_count += 1
            elif flag == FLAG_VALIDATED:
                validated_count += 1
            elif flag == FLAG_PROGRESS:
                progess_count += 1
            elif flag == FLAG_UNVALIDATED:
                unvalidated_count += 1

        self.signals.finished.emit(translated_count, validated_count, progess_count, unvalidated_count)


class QColorBar(QFrame):

    def __init__(self, parent: 'MainWindow'):
        super().__init__(parent)

        self.main_window = parent

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.setFixedHeight(10)

        self.translated = QWidget(self)
        self.validated = QWidget(self)
        self.progress = QWidget(self)
        self.unvalidated = QWidget(self)

        self.translated.setStyleSheet('background: #fff;')
        self.validated.setStyleSheet('background: #aaaadc;')
        self.progress.setStyleSheet('background: #dcaadc;')
        self.unvalidated.setStyleSheet('background: #eaaaaa;')

        self.layout.addWidget(self.translated)
        self.layout.addWidget(self.validated)
        self.layout.addWidget(self.progress)
        self.layout.addWidget(self.unvalidated)

        color_signals.update.connect(self.__update)

        self.__pool = QThreadPool()

    @Slot()
    def __update(self):
        worker = UpdateWorker(self.main_window.main_model.items())
        worker.setAutoDelete(True)
        worker.signals.finished.connect(self.__finished)
        self.__pool.start(worker)
    
    @Slot(int, int, int, int)
    def __finished(self, translated_count, validated_count, progess_count, unvalidated_count):
        self.update_colors(translated_count, validated_count, progess_count, unvalidated_count)

    def update_colors(self, translated_count, validated_count, progess_count, unvalidated_count):
        self.translated.setVisible(translated_count > 0)
        self.validated.setVisible(validated_count > 0)
        self.progress.setVisible(progess_count > 0)
        self.unvalidated.setVisible(unvalidated_count > 0)

        self.layout.setStretch(0, translated_count)
        self.layout.setStretch(1, validated_count)
        self.layout.setStretch(2, progess_count)
        self.layout.setStretch(3, unvalidated_count)
