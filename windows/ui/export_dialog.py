# -*- coding: utf-8 -*-

from PySide6.QtCore import QMetaObject
from PySide6.QtWidgets import QCheckBox, QGroupBox, QHBoxLayout, QPushButton, QRadioButton, QVBoxLayout


class Ui_ExportDialog(object):

    def setupUi(self, ExportDialog):
        ExportDialog.resize(390, 134)
        ExportDialog.setMinimumSize(390, 134)

        layout = QVBoxLayout(ExportDialog)

        self.gb_rec = QGroupBox(ExportDialog)

        layout_rec = QVBoxLayout(self.gb_rec)

        self.rb_all = QRadioButton(self.gb_rec)

        self.rb_translated = QRadioButton(self.gb_rec)
        self.rb_translated.setChecked(True)

        layout_rec.addWidget(self.rb_all)
        layout_rec.addWidget(self.rb_translated)

        layout.addWidget(self.gb_rec)

        self.cb_current_instance = QCheckBox(ExportDialog)
        self.cb_separate_instances = QCheckBox(ExportDialog)
        self.cb_separate_packages = QCheckBox(ExportDialog)

        layout.addWidget(self.cb_current_instance)
        layout.addWidget(self.cb_separate_instances)
        layout.addWidget(self.cb_separate_packages)
        layout.addStretch()

        layout_buttons = QHBoxLayout()
        layout_buttons.setContentsMargins(0, 4, 0, 0)

        self.btn_export = QPushButton(ExportDialog)
        self.btn_cancel = QPushButton(ExportDialog)

        self.btn_export.setDefault(True)
        self.btn_cancel.setAutoDefault(False)

        layout_buttons.addStretch()
        layout_buttons.addWidget(self.btn_cancel)
        layout_buttons.addWidget(self.btn_export)

        layout.addLayout(layout_buttons)

        QMetaObject.connectSlotsByName(ExportDialog)
