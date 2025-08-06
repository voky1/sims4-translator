# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableView, QAbstractScrollArea, QAbstractItemView, QHeaderView

from .delegate import MainDelegatePaint, DictionaryDelegatePaint, HeaderProxy

from singletons.config import config
from singletons.state import app_state
from utils.constants import *


class AbstractTableView(QTableView):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)

        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setShowGrid(False)
        self.setGridStyle(Qt.PenStyle.NoPen)
        self.setSortingEnabled(True)
        self.setWordWrap(False)

        header = self.verticalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        header.setDefaultSectionSize(26)
        header.setVisible(False)

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSortIndicator(0, Qt.SortOrder.AscendingOrder)
        header.setHighlightSections(False)
        header.setStyle(HeaderProxy())

    def selected_item(self):
        model = self.model()
        sources = self.selectionModel().selectedRows()
        return model.sourceModel().filtered[model.mapToSource(sources[0]).row()] if sources else None

    def selected_items(self):
        model = self.model()
        sources = self.selectionModel().selectedRows()
        return [model.sourceModel().filtered[model.mapToSource(s).row()] for s in sources] if sources else []

    def refresh(self):
        self.model().layoutChanged.emit()

    def resort(self):
        header = self.horizontalHeader()
        self.model().sourceModel().sort(header.sortIndicatorSection(), header.sortIndicatorOrder())


class QMainTableView(AbstractTableView):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)

        self.sortByColumn(COLUMN_MAIN_INDEX, Qt.SortOrder.AscendingOrder)

    def set_model(self):
        self.setModel(app_state.packages_storage.proxy)
        self.setItemDelegate(MainDelegatePaint())
        self.resize_columns()
        self.hide_columns()

    def resize_columns(self):
        header = self.horizontalHeader()

        header.setSectionResizeMode(COLUMN_MAIN_TRANSLATE, QHeaderView.ResizeMode.Stretch)

        self.setColumnWidth(COLUMN_MAIN_INDEX, 50)
        self.setColumnWidth(COLUMN_MAIN_INSTANCE, 160)
        self.setColumnWidth(COLUMN_MAIN_SOURCE, 300)
        self.setColumnWidth(COLUMN_MAIN_COMMENT, 175)
        self.setColumnWidth(COLUMN_MAIN_FLAG, 50)

        self.setColumnHidden(0, True)

    def hide_columns(self):
        self.setColumnHidden(COLUMN_MAIN_ID, not config.value('view', 'id'))
        self.setColumnHidden(COLUMN_MAIN_INSTANCE, not config.value('view', 'instance'))
        self.setColumnHidden(COLUMN_MAIN_GROUP, not config.value('view', 'group'))
        self.setColumnHidden(COLUMN_MAIN_SOURCE, not config.value('view', 'source'))
        self.setColumnHidden(COLUMN_MAIN_COMMENT, not config.value('view', 'comment'))


class QDictionaryTableView(AbstractTableView):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.SelectedClicked)

        self.sortByColumn(COLUMN_DICTIONARIES_LENGTH, Qt.SortOrder.AscendingOrder)

    def set_model(self):
        self.setModel(app_state.dictionaries_storage.proxy)
        self.setItemDelegate(DictionaryDelegatePaint())
        self.resize_columns()

    def resize_columns(self):
        header = self.horizontalHeader()

        header.setSectionResizeMode(COLUMN_DICTIONARIES_TRANSLATE, QHeaderView.ResizeMode.Stretch)

        self.setColumnWidth(COLUMN_DICTIONARIES_PACKAGE, 125)
        self.setColumnWidth(COLUMN_DICTIONARIES_SOURCE, 200)
        self.setColumnWidth(COLUMN_DICTIONARIES_LENGTH, 5)

        self.setColumnHidden(0, True)
