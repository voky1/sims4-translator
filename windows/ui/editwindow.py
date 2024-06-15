# -*- coding: utf-8 -*-

from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtWidgets import QComboBox, QGridLayout,QLabel, QLineEdit, QPushButton, QSizePolicy, QSpacerItem, QSplitter, QVBoxLayout, QWidget

from widgets.tableview import QDictionaryTableView
from widgets.editor import QTextEditor
from utils.functions import icon

from utils.functions import monospace_font


class Ui_EditWindow(object):

    def setupUi(self, EditWindow):
        EditWindow.resize(1009, 663)
        EditWindow.setMinimumSize(961, 611)

        centralwidget = QWidget(EditWindow)
        self.setCentralWidget(centralwidget)

        layout = QGridLayout(centralwidget)

        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout.addItem(spacer, 4, 3, 1, 1)

        self.btn_translate = QPushButton(centralwidget)
        self.btn_translate.setIcon(icon('api'))

        layout.addWidget(self.btn_translate, 4, 1, 1, 1)

        self.btn_ok = QPushButton(centralwidget)

        layout.addWidget(self.btn_ok, 4, 5, 1, 1)

        font = monospace_font()

        self.txt_resource = QLineEdit(centralwidget)
        self.txt_resource.setFont(font)
        self.txt_resource.setReadOnly(True)

        layout.addWidget(self.txt_resource, 0, 0, 1, 6)

        self.lbl_status = QLabel(centralwidget)

        layout.addWidget(self.lbl_status, 4, 2, 1, 1)

        self.cb_api = QComboBox(centralwidget)

        layout.addWidget(self.cb_api, 4, 0, 1, 1)

        self.tableview = QDictionaryTableView(EditWindow)

        splitter = QSplitter(centralwidget)
        splitter.setOrientation(Qt.Vertical)

        splitter_top = QSplitter(splitter)
        splitter_top.setOrientation(Qt.Horizontal)
        splitter_top.setChildrenCollapsible(False)

        self.txt_search = QTextEditor(EditWindow)
        self.txt_search.setFont(font)
        self.txt_search.setReadOnly(True)
        self.txt_search.setPlainText('')

        splitter_top.addWidget(self.tableview)
        splitter_top.addWidget(self.txt_search)
        splitter.addWidget(splitter_top)

        splitter_bottom = QSplitter(splitter)
        splitter_bottom.setOrientation(Qt.Horizontal)

        widget_left = QWidget(splitter_bottom)

        layout_left = QVBoxLayout(widget_left)
        layout_left.setContentsMargins(0, 0, 0, 0)

        self.lbl_original = QLabel(EditWindow)

        self.txt_original = QTextEditor(EditWindow)
        self.txt_original.setFont(font)
        self.txt_original.setReadOnly(True)

        layout_left.addWidget(self.lbl_original)
        layout_left.addWidget(self.txt_original)

        self.lbl_original_diff = QLabel(EditWindow)

        self.txt_original_diff = QTextEditor(EditWindow)
        self.txt_original_diff.setFont(font)
        self.txt_original_diff.setReadOnly(True)

        layout_left.addWidget(self.lbl_original_diff)
        layout_left.addWidget(self.txt_original_diff)

        splitter_bottom.addWidget(widget_left)

        widget_right = QWidget(splitter_bottom)

        layout_right = QVBoxLayout(widget_right)
        layout_right.setContentsMargins(0, 0, 0, 0)

        self.lbl_translate = QLabel(EditWindow)

        self.txt_translate = QTextEditor(EditWindow)
        self.txt_translate.setFont(font)

        layout_right.addWidget(self.lbl_translate)
        layout_right.addWidget(self.txt_translate)

        self.lbl_translate_diff = QLabel(EditWindow)

        self.txt_translate_diff = QTextEditor(EditWindow)
        self.txt_translate_diff.setFont(font)
        self.txt_translate_diff.setReadOnly(True)

        layout_right.addWidget(self.lbl_translate_diff)
        layout_right.addWidget(self.txt_translate_diff)

        splitter_bottom.addWidget(widget_right)

        splitter.addWidget(splitter_bottom)

        layout.addWidget(splitter, 1, 0, 1, 6)

        self.btn_cancel = QPushButton(EditWindow)

        layout.addWidget(self.btn_cancel, 4, 4, 1, 1)

        self.txt_comment = QLineEdit(EditWindow)

        layout.addWidget(self.txt_comment, 3, 0, 1, 6)

        QWidget.setTabOrder(self.txt_translate, self.txt_original)
        QWidget.setTabOrder(self.txt_original, self.tableview)
        QWidget.setTabOrder(self.tableview, self.txt_search)
        QWidget.setTabOrder(self.txt_search, self.txt_resource)

        splitter.setSizes((150, 350))
        splitter_top.setSizes((500, 300))
        splitter_bottom.setSizes((250, 500))

        QMetaObject.connectSlotsByName(EditWindow)
