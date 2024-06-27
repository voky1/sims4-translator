# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QToolBar as ToolBar, QComboBox, QWidget, QSizePolicy
from PySide6.QtGui import QAction, QIcon

from widgets.lineedit import QCleaningLineEdit

from singletons.interface import interface


class QToolBar(ToolBar):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMovable(False)
        self.setIconSize(QSize(18, 18))
        self.setFloatable(False)
        self.setContextMenuPolicy(Qt.PreventContextMenu)

        self.search_toggle = QAction(QIcon(':/images/search_source'), None)

        self.filter_validate_3 = QAction(QIcon(':/images/validate_3'), None)
        self.filter_validate_3.setCheckable(True)
        self.filter_validate_3.setChecked(True)

        self.filter_validate_0 = QAction(QIcon(':/images/validate_0'), None)
        self.filter_validate_0.setCheckable(True)
        self.filter_validate_0.setChecked(True)

        self.filter_validate_2 = QAction(QIcon(':/images/validate_2'), None)
        self.filter_validate_2.setCheckable(True)
        self.filter_validate_2.setChecked(True)

        self.filter_validate_1 = QAction(QIcon(':/images/validate_1'), None)
        self.filter_validate_1.setCheckable(True)
        self.filter_validate_1.setChecked(True)

        self.filter_validate_4 = QAction(QIcon(':/images/validate_4'), None)
        self.filter_validate_4.setCheckable(True)

        self.edt_search = FixedLineEdit()
        self.cb_files = FilesComboBox()
        self.cb_instances = InstancesComboBox()

        self.addSeparator()
        self.addWidget(self.edt_search)
        self.addSeparator()
        self.addAction(self.search_toggle)

        self.addSeparator()

        self.addAction(self.filter_validate_3)
        self.addAction(self.filter_validate_0)
        self.addAction(self.filter_validate_2)
        self.addAction(self.filter_validate_1)

        self.addSeparator()

        self.addAction(self.filter_validate_4)

        self.addSeparator()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.addWidget(spacer)

        self.addWidget(self.cb_files)
        self.addSeparator()
        self.addWidget(self.cb_instances)
        self.addSeparator()

        self.retranslate()

    def retranslate(self):
        self.search_toggle.setToolTip(interface.text('ToolBar', 'Search in original'))
        self.filter_validate_0.setToolTip(interface.text('ToolBar', 'Not translated'))
        self.filter_validate_1.setToolTip(interface.text('ToolBar', 'Partial translation'))
        self.filter_validate_2.setToolTip(interface.text('ToolBar', 'Validated translation'))
        self.filter_validate_3.setToolTip(interface.text('ToolBar', 'Translated'))
        self.filter_validate_4.setToolTip(interface.text('ToolBar', 'Different strings'))

        self.edt_search.setPlaceholderText(interface.text('ToolBar', 'Search...'))
        self.cb_instances.setItemText(0, interface.text('ToolBar', '-- All instances --'))
        self.cb_files.setItemText(0, interface.text('ToolBar', '-- All files --'))


class FixedLineEdit(QCleaningLineEdit):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.adjusted_size = 200

        self.setClearButtonEnabled(True)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.setContentsMargins(0, 0, 0, 0)

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        return QSize(self.adjusted_size, 26)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.clear()


class InstancesComboBox(QComboBox):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.adjusted_size = 200

        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.setContentsMargins(0, 0, 0, 0)

        self.addItem('')

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        return QSize(self.adjusted_size, 26)


class FilesComboBox(QComboBox):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.adjusted_size = 470

        size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.setSizePolicy(size_policy)
        self.setContentsMargins(0, 0, 0, 0)

        self.addItem('')

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        return QSize(self.adjusted_size, 26)
