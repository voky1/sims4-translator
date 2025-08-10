"""Options dialog UI definition.
Includes Interface, Game path, Languages, API keys with tutorial buttons, and Dictionaries tab."""

from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import (
    QWidget,
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QTabWidget,
    QHeaderView,
    QScrollArea,
    QFrame,
)


class Ui_OptionsDialog(object):
    def setupUi(self, OptionsDialog):
        OptionsDialog.resize(545, 490)
        OptionsDialog.setMinimumSize(545, 490)

        root = QVBoxLayout(OptionsDialog)

        self.tab_general = QWidget()
        self.tab_dictionaries = QWidget()

        self.tabs = QTabWidget(OptionsDialog)
        self.tabs.addTab(self.tab_general, '')
        self.tabs.addTab(self.tab_dictionaries, '')
        root.addWidget(self.tabs)

        self.build_general_tab()
        self.build_dictionaries_tab()

        QMetaObject.connectSlotsByName(OptionsDialog)

    def build_general_tab(self):
        # Outer layout holds the scroll area
        outer = QVBoxLayout(self.tab_general)
        self.scroll_general = QScrollArea(self.tab_general)
        self.scroll_general.setWidgetResizable(True)
        self.scroll_general.setFrameShape(QFrame.NoFrame)
        self.scroll_general.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.general_container = QWidget()
        self.scroll_general.setWidget(self.general_container)
        # Apply white background only to the container so buttons keep their native look
        self.general_container.setAutoFillBackground(True)
        pal = self.general_container.palette()
        pal.setColor(self.general_container.backgroundRole(), Qt.white)
        self.general_container.setPalette(pal)
        outer.addWidget(self.scroll_general)

        # Inner layout hosts all option groups
        vlayout = QVBoxLayout(self.general_container)
        vlayout.setSpacing(8)

        # Interface group
        self.gb_interface = QGroupBox(self.general_container)
        layout_group = QVBoxLayout(self.gb_interface)
        layout_lang = QHBoxLayout()
        layout_theme = QHBoxLayout()

        self.lbl_language = QLabel(self.gb_interface)
        self.lbl_language_authors = QLabel(self.gb_interface)
        self.lbl_language_hint = QLabel(self.gb_interface)
        self.cb_language = QComboBox(self.gb_interface)

        self.lbl_theme = QLabel(self.gb_interface)
        self.lbl_theme_hint = QLabel(self.gb_interface)
        self.cb_theme = QComboBox(self.gb_interface)

        self.lbl_language_hint.setWordWrap(True)
        self.lbl_language_hint.setObjectName('muted')

        self.lbl_language.setMinimumHeight(26)
        self.lbl_theme.setMinimumHeight(26)

        self.lbl_theme_hint.setVisible(False)
        self.lbl_theme_hint.setWordWrap(True)

        layout_lang_lbl = QVBoxLayout()
        layout_lang_authors = QHBoxLayout()
        layout_lang_hint = QVBoxLayout()

        layout_theme_lbl = QVBoxLayout()
        layout_theme_plug = QHBoxLayout()
        layout_theme_hint = QVBoxLayout()

        layout_lang_authors.addWidget(self.cb_language)
        layout_lang_authors.addWidget(self.lbl_language_authors)
        layout_lang_authors.addStretch()

        layout_lang_lbl.addWidget(self.lbl_language)
        layout_lang_lbl.addStretch()

        layout_lang_hint.addLayout(layout_lang_authors)
        layout_lang_hint.addWidget(self.lbl_language_hint)

        layout_lang.addLayout(layout_lang_lbl)
        layout_lang.addLayout(layout_lang_hint)

        layout_theme_lbl.addWidget(self.lbl_theme)
        layout_theme_lbl.addStretch()

        layout_theme_plug.addWidget(self.cb_theme)
        layout_theme_plug.addStretch()

        layout_theme_hint.addLayout(layout_theme_plug)
        layout_theme_hint.addWidget(self.lbl_theme_hint)

        layout_theme.addLayout(layout_theme_lbl)
        layout_theme.addLayout(layout_theme_hint)

        self.lbl_language.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_theme.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.lbl_language.setMinimumWidth(75)
        self.lbl_theme.setMinimumWidth(75)

        layout_group.addLayout(layout_lang)
        layout_group.addLayout(layout_theme)

        vlayout.addWidget(self.gb_interface)

        # Checkboxes group
        gbox = QGroupBox(self.general_container)
        layout_group = QVBoxLayout(gbox)

        self.cb_backup = QCheckBox(gbox)
        self.cb_experemental = QCheckBox(gbox)
        self.cb_strong = QCheckBox(gbox)

        layout_group.addWidget(self.cb_backup)
        layout_group.addWidget(self.cb_experemental)
        layout_group.addWidget(self.cb_strong)

        vlayout.addWidget(gbox)

        # Languages group
        self.gb_lang = QGroupBox(self.general_container)
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

        # DeepL group + tutorial button
        self.gb_deepl = QGroupBox(self.general_container)
        layout_deepl = QVBoxLayout(self.gb_deepl)
        self.txt_deepl_key = QLineEdit(self.gb_deepl)
        self.btn_deepl_tutorial = QPushButton(self.gb_deepl)
        layout_deepl.addWidget(self.txt_deepl_key)
        layout_deepl.addWidget(self.btn_deepl_tutorial)
        vlayout.addWidget(self.gb_deepl)

        # Google Cloud group
        self.gb_gcloud = QGroupBox(self.general_container)
        layout_gcloud = QVBoxLayout(self.gb_gcloud)
        self.txt_gcloud_key = QLineEdit(self.gb_gcloud)
        self.btn_gcloud_tutorial = QPushButton(self.gb_gcloud)
        layout_gcloud.addWidget(self.txt_gcloud_key)
        layout_gcloud.addWidget(self.btn_gcloud_tutorial)
        vlayout.addWidget(self.gb_gcloud)
        
        # Cohere group
        self.gb_cohere = QGroupBox(self.general_container)
        layout_cohere = QVBoxLayout(self.gb_cohere)
        self.txt_cohere_key = QLineEdit(self.gb_cohere)
        self.btn_cohere_tutorial = QPushButton(self.gb_cohere)
        layout_cohere.addWidget(self.txt_cohere_key)
        layout_cohere.addWidget(self.btn_cohere_tutorial)
        vlayout.addWidget(self.gb_cohere)

        vlayout.addStretch()

    def build_dictionaries_tab(self):
        vlayout = QVBoxLayout(self.tab_dictionaries)
        vlayout.setSpacing(8)

        self.gb_path = QGroupBox(self.tab_dictionaries)

        layout_path = QHBoxLayout(self.gb_path)

        self.txt_path = QLineEdit(self.gb_path)

        self.btn_path = QPushButton(self.gb_path)
        self.btn_path.setText('...')
        self.btn_path.setAutoDefault(False)

        layout_path.addWidget(self.txt_path)
        layout_path.addWidget(self.btn_path)

        vlayout.addWidget(self.gb_path)

        self.tableview = QTableView(self.tab_dictionaries)
        self.tableview.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tableview.setAutoScroll(False)
        self.tableview.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableview.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tableview.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableview.setShowGrid(False)
        self.tableview.setGridStyle(Qt.PenStyle.NoPen)
        self.tableview.setWordWrap(False)
        self.tableview.horizontalHeader().setVisible(False)

        header = self.tableview.verticalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        header.setDefaultSectionSize(26)
        header.setVisible(False)
        
        self.btn_build = QPushButton(self.tab_dictionaries)
        self.btn_build.setAutoDefault(False)

        vlayout.addWidget(self.tableview)
        vlayout.addWidget(self.btn_build)
