# -*- coding: utf-8 -*-

from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtWidgets import QWidget, QAbstractItemView, QCheckBox, QComboBox, QGroupBox, QHBoxLayout, QLabel, \
    QLineEdit, QPushButton, QTableView, QVBoxLayout, QTabWidget

from utils.functions import monospace_font


class Ui_OptionsDialog(object):

    def setupUi(self, OptionsDialog):
        OptionsDialog.resize(545, 440)
        OptionsDialog.setMinimumSize(545, 440)

        layout = QVBoxLayout(OptionsDialog)

        self.tab_general = QWidget()
        self.tab_dictionaries = QWidget()

        self.tabs = QTabWidget(OptionsDialog)
        self.tabs.addTab(self.tab_general, '')
        self.tabs.addTab(self.tab_dictionaries, '')

        layout.addWidget(self.tabs)

        self.build_general_tab()
        self.build_dictionaries_tab()

        QMetaObject.connectSlotsByName(OptionsDialog)

    def build_general_tab(self):
        vlayout = QVBoxLayout(self.tab_general)

        self.gb_interface = QGroupBox(self.tab_general)

        layout_group = QHBoxLayout(self.gb_interface)

        self.cb_language = QComboBox(self.gb_interface)
        self.cb_language.setMinimumSize(100, 0)

        layout_group.addWidget(self.cb_language)
        layout_group.addStretch()

        vlayout.addWidget(self.gb_interface)

        gbox = QGroupBox(self.tab_general)
        layout_group = QVBoxLayout(gbox)

        self.cb_backup = QCheckBox(gbox)
        self.cb_experemental = QCheckBox(gbox)
        self.cb_strong = QCheckBox(gbox)

        layout_group.addWidget(self.cb_backup)
        layout_group.addWidget(self.cb_experemental)
        layout_group.addWidget(self.cb_strong)

        vlayout.addWidget(gbox)

        self.gb_lang = QGroupBox(self.tab_general)

        layout_lang = QHBoxLayout(self.gb_lang)

        self.label_source = QLabel(self.gb_lang)
        self.label_dest = QLabel(self.gb_lang)

        self.cb_source = QComboBox(self.gb_lang)
        self.cb_dest = QComboBox(self.gb_lang)

        layout_lang.addStretch()
        layout_lang.addWidget(self.label_source)
        layout_lang.addWidget(self.cb_source)
        layout_lang.addStretch()
        layout_lang.addWidget(self.label_dest)
        layout_lang.addWidget(self.cb_dest)
        layout_lang.addStretch()

        vlayout.addWidget(self.gb_lang)

        self.gb_deepl = QGroupBox(self.tab_general)

        layout_deepl = QHBoxLayout(self.gb_deepl)

        self.txt_deepl_key = QLineEdit(self.gb_deepl)

        layout_deepl.addWidget(self.txt_deepl_key)

        vlayout.addWidget(self.gb_deepl)

        vlayout.addStretch()

    def build_dictionaries_tab(self):
        vlayout = QVBoxLayout(self.tab_dictionaries)

        self.gb_path = QGroupBox(self.tab_dictionaries)

        layout_path = QHBoxLayout(self.gb_path)

        self.txt_path = QLineEdit(self.gb_path)

        self.btn_path = QPushButton(self.gb_path)
        self.btn_path.setFixedWidth(25)
        self.btn_path.setText('...')

        layout_path.addWidget(self.txt_path)
        layout_path.addWidget(self.btn_path)

        vlayout.addWidget(self.gb_path)

        self.tableview = QTableView(self.tab_dictionaries)
        self.tableview.setFont(monospace_font())
        self.tableview.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableview.setAutoScroll(False)
        self.tableview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableview.setSelectionMode(QAbstractItemView.NoSelection)
        self.tableview.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableview.setShowGrid(False)
        self.tableview.setGridStyle(Qt.NoPen)
        self.tableview.setWordWrap(False)
        self.tableview.horizontalHeader().setVisible(False)
        self.tableview.verticalHeader().setVisible(False)
        self.tableview.verticalHeader().setMinimumSectionSize(0)

        self.btn_build = QPushButton(self.tab_dictionaries)
        self.btn_build.setAutoDefault(False)

        vlayout.addWidget(self.tableview)
        vlayout.addWidget(self.btn_build)
