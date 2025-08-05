# -*- coding: utf-8 -*-

from PySide6.QtCore import QMetaObject
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, \
    QRadioButton, QVBoxLayout


class Ui_ReplaceDialog(object):

    def setupUi(self, ReplaceDialog):
        ReplaceDialog.setMinimumSize(450, 0)

        layout = QVBoxLayout(ReplaceDialog)

        layout_form = QFormLayout()

        self.label_search = QLabel(ReplaceDialog)
        self.label_replace = QLabel(ReplaceDialog)

        layout_form.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_search)
        layout_form.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_replace)

        self.cb_search = QComboBox(ReplaceDialog)
        self.cb_search.setEditable(True)

        self.cb_replace = QComboBox(ReplaceDialog)
        self.cb_replace.setEditable(True)

        layout_form.setWidget(0, QFormLayout.ItemRole.FieldRole, self.cb_search)
        layout_form.setWidget(1, QFormLayout.ItemRole.FieldRole, self.cb_replace)

        layout.addLayout(layout_form)

        self.groupbox = QGroupBox(ReplaceDialog)

        layout_group = QVBoxLayout(self.groupbox)

        self.rb_all_strings = QRadioButton(self.groupbox)

        self.rb_not_validated_strings = QRadioButton(self.groupbox)
        self.rb_not_validated_strings.setChecked(True)

        layout_group.addWidget(self.rb_all_strings)
        layout_group.addWidget(self.rb_not_validated_strings)

        layout.addWidget(self.groupbox)
        layout.addStretch()

        layout_buttons = QHBoxLayout()
        layout_buttons.setContentsMargins(0, 4, 0, 0)

        self.cb_case_sensitive = QCheckBox(ReplaceDialog)
        self.cb_case_sensitive.setChecked(True)

        self.btn_replace = QPushButton(ReplaceDialog)
        self.btn_cancel = QPushButton(ReplaceDialog)

        self.btn_replace.setDefault(True)
        self.btn_cancel.setAutoDefault(False)

        layout_buttons.addWidget(self.cb_case_sensitive)
        layout_buttons.addStretch()
        layout_buttons.addWidget(self.btn_cancel)
        layout_buttons.addWidget(self.btn_replace)

        layout.addLayout(layout_buttons)

        ReplaceDialog.adjustSize()
        ReplaceDialog.setMinimumSize(ReplaceDialog.size())

        QMetaObject.connectSlotsByName(ReplaceDialog)
