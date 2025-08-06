# -*- coding: utf-8 -*-

from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit, QPushButton, QSplitter, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtGui import QIcon

from widgets.tableview import QDictionaryTableView
from widgets.editor import QTextEditor


class Ui_EditDialog(object):

    def setupUi(self, EditDialog):
        EditDialog.resize(1009, 663)
        EditDialog.setMinimumSize(961, 611)

        self.lbl_original = QLabel(EditDialog)
        self.lbl_original_diff = QLabel(EditDialog)
        self.lbl_translate = QLabel(EditDialog)
        self.lbl_translate_diff = QLabel(EditDialog)

        self.txt_original = QTextEditor()
        self.txt_original.setReadOnly(True)

        self.txt_original_diff = QTextEditor()
        self.txt_original_diff.setReadOnly(True)

        self.txt_translate = QTextEditor()

        self.txt_translate_diff = QTextEditor()
        self.txt_translate_diff.setReadOnly(True)

        self.txt_search = QTextEditor()
        self.txt_search.setReadOnly(True)

        self.txt_resource = QLineEdit(EditDialog)
        self.txt_resource.setReadOnly(True)
        self.txt_resource.setObjectName('monospace')

        self.tableview = QDictionaryTableView(EditDialog)

        layout = QVBoxLayout(EditDialog)
        layout.setSpacing(8)

        layout.addWidget(self.txt_resource)

        left_widget = QWidget(EditDialog)
        right_widget = QWidget(EditDialog)

        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.lbl_original)
        left_layout.addWidget(self.txt_original)
        left_layout.addWidget(self.lbl_original_diff)
        left_layout.addWidget(self.txt_original_diff)

        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.lbl_translate)
        right_layout.addWidget(self.txt_translate)
        right_layout.addWidget(self.lbl_translate_diff)
        right_layout.addWidget(self.txt_translate_diff)

        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.addWidget(self.tableview)
        top_splitter.addWidget(self.txt_search)
        top_splitter.setSizes([500, 300])
        top_splitter.setHandleWidth(8)

        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        bottom_splitter.addWidget(left_widget)
        bottom_splitter.addWidget(right_widget)
        bottom_splitter.setSizes([300, 500])
        bottom_splitter.setHandleWidth(8)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(top_splitter)
        splitter.addWidget(bottom_splitter)
        splitter.setSizes([200, 350])
        splitter.setHandleWidth(8)

        layout.addWidget(splitter)

        self.txt_comment = QLineEdit(EditDialog)

        layout.addWidget(self.txt_comment)

        self.cb_api = QComboBox(EditDialog)

        self.btn_translate = QPushButton(EditDialog)
        self.btn_translate.setIcon(QIcon(':/images/api.png'))
        self.btn_translate.setAutoDefault(False)

        self.lbl_status = QLabel(EditDialog)

        self.btn_ok = QPushButton(EditDialog)
        self.btn_cancel = QPushButton(EditDialog)

        self.btn_ok.setDefault(True)
        self.btn_cancel.setAutoDefault(False)

        hlayout = QHBoxLayout()

        hlayout.addWidget(self.cb_api)
        hlayout.addWidget(self.btn_translate)
        hlayout.addWidget(self.lbl_status)
        hlayout.addStretch()
        hlayout.addWidget(self.btn_cancel)
        hlayout.addWidget(self.btn_ok)

        layout.addLayout(hlayout)

        QMetaObject.connectSlotsByName(EditDialog)
