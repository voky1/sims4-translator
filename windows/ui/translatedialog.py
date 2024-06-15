# -*- coding: utf-8 -*-

from PySide6.QtCore import QMetaObject
from PySide6.QtWidgets import QComboBox, QGroupBox, QHBoxLayout, QPushButton, QRadioButton, QVBoxLayout, \
    QLabel, QTextEdit


from utils.functions import monospace_font


class Ui_TranslateDialog(object):

    def setupUi(self, TranslateDialog):
        TranslateDialog.resize(590, 441)
        TranslateDialog.setMinimumSize(590, 441)

        layout = QVBoxLayout(TranslateDialog)

        gbox = QGroupBox(TranslateDialog)
        vlayout = QVBoxLayout(gbox)

        self.rb_all = QRadioButton(gbox)
        self.rb_validated = QRadioButton(gbox)
        self.rb_validated_partial = QRadioButton(gbox)
        self.rb_partial = QRadioButton(gbox)
        self.rb_selection = QRadioButton(gbox)

        self.rb_validated.setChecked(True)

        vlayout.addWidget(self.rb_all)
        vlayout.addWidget(self.rb_validated)
        vlayout.addWidget(self.rb_validated_partial)
        vlayout.addWidget(self.rb_partial)
        vlayout.addWidget(self.rb_selection)

        layout.addWidget(gbox)

        gbox2 = QGroupBox(TranslateDialog)
        vlayout2 = QVBoxLayout(gbox2)

        self.rb_slow = QRadioButton(gbox2)
        self.rb_fast = QRadioButton(gbox2)

        self.lbl_slow = QLabel(gbox2)
        self.lbl_fast = QLabel(gbox2)

        self.lbl_slow.setWordWrap(True)
        self.lbl_fast.setWordWrap(True)

        self.lbl_slow.setStyleSheet('color: #696867;')
        self.lbl_fast.setStyleSheet('color: #696867;')

        self.rb_slow.setChecked(True)

        vlayout2.addWidget(self.rb_slow)
        vlayout2.addWidget(self.lbl_slow)
        vlayout2.addWidget(self.rb_fast)
        vlayout2.addWidget(self.lbl_fast)

        layout.addWidget(gbox2)

        self.log_box = QGroupBox(TranslateDialog)
        vlayout3 = QVBoxLayout(self.log_box)

        self.edt_log = QTextEdit(self.log_box)
        self.edt_log.setReadOnly(True)
        self.edt_log.setFont(monospace_font())

        vlayout3.addWidget(self.edt_log)

        layout.addWidget(self.log_box)

        hlayout = QHBoxLayout()

        self.cb_api = QComboBox(TranslateDialog)

        self.btn_cancel = QPushButton(TranslateDialog)
        self.btn_translate = QPushButton(TranslateDialog)

        self.btn_cancel.setDefault(True)

        hlayout.addWidget(self.cb_api)
        hlayout.addStretch()
        hlayout.addWidget(self.btn_cancel)
        hlayout.addWidget(self.btn_translate)

        layout.addLayout(hlayout)

        QMetaObject.connectSlotsByName(TranslateDialog)
