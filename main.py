# -*- coding: utf-8 -*-

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase

from windows.main_window import MainWindow

from singletons.state import app_state

from storages.packages import PackagesStorage
from storages.dictionaries import DictionariesStorage

from themes.stylesheet import stylesheet

import resources.resource_rc


def main():
    sys.argv += ['-style', 'windows']

    app = QApplication(sys.argv)

    packages_storage = PackagesStorage()
    dictionaries_storage = DictionariesStorage()

    app_state.set_packages_storage(packages_storage)
    app_state.set_dictionaries_storage(dictionaries_storage)

    QFontDatabase.addApplicationFont(':/fonts/roboto.ttf')
    QFontDatabase.addApplicationFont(':/fonts/jetbrainsmono.ttf')
    QFontDatabase.addApplicationFont(':/fonts/jetbrainsmono-semibold.ttf')

    app.setStyleSheet(stylesheet())

    window = MainWindow()
    window.show()

    exit_status = app.exec()

    app.setStyleSheet('')

    sys.exit(exit_status)


if __name__ == '__main__':
    main()
