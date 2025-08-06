# -*- coding: utf-8 -*-

from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtWidgets import QLabel, QMenu, QMenuBar, QProgressBar, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit
from PySide6.QtGui import QAction, QIcon

from widgets.colorbar import QColorBar
from widgets.tableview import QMainTableView
from widgets.toolbar import QToolBar

from utils.constants import APP_VERSION, APP_RELEASE_CANDITATE


class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        MainWindow.resize(1125, 723)
        MainWindow.setMinimumSize(935, 620)

        title = f'The Sims 4 Translator {APP_VERSION}'
        if APP_RELEASE_CANDITATE:
            title += ' RC'

        MainWindow.setWindowTitle(title)
        MainWindow.setWindowIcon(QIcon(':/logo.ico'))
        
        self.action_load_file = QAction(MainWindow)
        self.action_load_file.setIcon(QIcon(':/images/load.png'))
        self.action_load_file.setShortcut('Ctrl+O')

        self.action_save_as = QAction(MainWindow)
        self.action_save_as.setEnabled(False)
        self.action_save_as.setIcon(QIcon(':/images/dict.png'))

        self.action_close = QAction(MainWindow)
        self.action_close.setEnabled(False)
        self.action_close.setIcon(QIcon(':/images/close.png'))

        self.action_save = QAction(MainWindow)
        self.action_save.setEnabled(False)
        self.action_save.setIcon(QIcon(':/images/dict.png'))
        self.action_save.setShortcut('Ctrl+S')

        self.action_save_dictionary = QAction(MainWindow)
        self.action_save_dictionary.setEnabled(False)
        self.action_save_dictionary.setIcon(QIcon(':/images/export.png'))

        self.action_replace = QAction(MainWindow)
        self.action_replace.setEnabled(False)
        self.action_replace.setIcon(QIcon(':/images/replace.png'))
        self.action_replace.setShortcut('Ctrl+R')

        self.action_validate_all_translations = QAction(MainWindow)
        self.action_validate_all_translations.setEnabled(False)
        self.action_validate_all_translations.setIcon(QIcon(':/images/validate_2.png'))
        self.action_validate_all_translations.setShortcut('Ctrl+F1')

        self.action_reset_all_translations = QAction(MainWindow)
        self.action_reset_all_translations.setEnabled(False)
        self.action_reset_all_translations.setIcon(QIcon(':/images/validate_0.png'))
        self.action_reset_all_translations.setShortcut('Ctrl+F4')

        self.action_add_file = QAction(MainWindow)
        self.action_add_file.setEnabled(False)
        self.action_add_file.setIcon(QIcon(':/images/load.png'))

        self.action_exit = QAction(MainWindow)

        self.action_undo = QAction(MainWindow)
        self.action_undo.setEnabled(False)
        self.action_undo.setIcon(QIcon(':/images/undo.png'))
        self.action_undo.setShortcut('Ctrl+Z')

        self.action_about_qt = QAction(MainWindow)

        self.action_options = QAction(MainWindow)
        self.action_options.setIcon(QIcon(':/images/options.png'))

        self.action_translate_from_dictionaries = QAction(MainWindow)
        self.action_translate_from_dictionaries.setEnabled(False)
        self.action_translate_from_dictionaries.setIcon(QIcon(':/images/translate.png'))

        self.action_translate = QAction(MainWindow)
        self.action_translate.setEnabled(False)
        self.action_translate.setIcon(QIcon(':/images/api.png'))

        self.action_import_translation = QAction(MainWindow)
        self.action_import_translation.setEnabled(False)
        self.action_import_translation.setIcon(QIcon(':/images/import.png'))

        self.action_save_bundle = QAction(MainWindow)
        self.action_save_bundle.setEnabled(False)
        self.action_save_bundle.setIcon(QIcon(':/images/export_xml.png'))

        self.action_load_bundle = QAction(MainWindow)
        self.action_load_bundle.setIcon(QIcon(':/images/import.png'))

        self.action_finalize = QAction(MainWindow)
        self.action_finalize.setEnabled(False)
        self.action_finalize.setIcon(QIcon(':/images/dict.png'))

        self.action_finalize_as = QAction(MainWindow)
        self.action_finalize_as.setEnabled(False)
        self.action_finalize_as.setIcon(QIcon(':/images/dict.png'))

        self.action_export_xml = QAction(MainWindow)
        self.action_export_xml.setIcon(QIcon(':/images/export_xml.png'))

        self.action_export_xml_dp = QAction(MainWindow)
        self.action_export_xml_dp.setIcon(QIcon(':/images/export_xml.png'))

        self.action_export_stbl = QAction(MainWindow)
        self.action_export_stbl.setIcon(QIcon(':/images/export.png'))

        self.action_export_json_s4s = QAction(MainWindow)
        self.action_export_json_s4s.setIcon(QIcon(':/images/export_xml.png'))

        self.action_export_binary_s4s = QAction(MainWindow)
        self.action_export_binary_s4s.setIcon(QIcon(':/images/export.png'))

        self.action_group_original = QAction(MainWindow)
        self.action_group_original.setCheckable(True)
        self.action_group_highbit = QAction(MainWindow)
        self.action_group_highbit.setCheckable(True)
        self.action_group_lowbit = QAction(MainWindow)
        self.action_group_lowbit.setCheckable(True)

        self.action_num_standart = QAction(MainWindow)
        self.action_num_standart.setCheckable(True)
        self.action_num_source = QAction(MainWindow)
        self.action_num_source.setCheckable(True)
        self.action_num_xml = QAction(MainWindow)
        self.action_num_xml.setCheckable(True)
        self.action_num_xml_dp = QAction(MainWindow)
        self.action_num_xml_dp.setCheckable(True)

        self.action_insert = QAction(MainWindow)

        self.action_colorbar = QAction(MainWindow)
        self.action_colorbar.setCheckable(True)

        self.menubar = QMenuBar(MainWindow)

        self.menu_file = QMenu(self.menubar)
        self.menu_export_translation = QMenu(self.menu_file)
        self.menu_export_translation.setEnabled(False)
        self.menu_export_translation.setIcon(QIcon(':/images/export_xml.png'))
        self.menu_translation = QMenu(self.menubar)
        self.menu_view = QMenu(self.menubar)
        self.menu_numeration = QMenu(self.menu_view)
        self.menu_options = QMenu(self.menubar)
        self.menu_group = QMenu(self.menu_options)
        self.menu_help = QMenu(self.menubar)

        self.menubar.addAction(self.menu_file.menuAction())
        self.menubar.addAction(self.menu_translation.menuAction())
        self.menubar.addAction(self.menu_view.menuAction())
        self.menubar.addAction(self.menu_options.menuAction())
        self.menubar.addAction(self.menu_help.menuAction())
        self.menu_file.addAction(self.action_load_file)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_add_file)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_save)
        self.menu_file.addAction(self.action_save_as)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_finalize)
        self.menu_file.addAction(self.action_finalize_as)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_load_bundle)
        self.menu_file.addAction(self.action_save_bundle)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_import_translation)
        self.menu_file.addAction(self.menu_export_translation.menuAction())
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_save_dictionary)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_close)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_exit)
        self.menu_export_translation.addAction(self.action_export_stbl)
        self.menu_export_translation.addAction(self.action_export_xml)
        self.menu_export_translation.addAction(self.action_export_xml_dp)
        self.menu_export_translation.addAction(self.action_export_json_s4s)
        self.menu_export_translation.addAction(self.action_export_binary_s4s)
        self.menu_translation.addAction(self.action_replace)
        self.menu_translation.addSeparator()
        self.menu_translation.addAction(self.action_translate_from_dictionaries)
        self.menu_translation.addSeparator()
        self.menu_translation.addAction(self.action_validate_all_translations)
        self.menu_translation.addAction(self.action_reset_all_translations)
        self.menu_translation.addSeparator()
        self.menu_translation.addAction(self.action_translate)
        self.menu_translation.addSeparator()
        self.menu_translation.addAction(self.action_undo)
        self.menu_view.addAction(self.action_insert)
        self.menu_view.addAction(self.action_colorbar)
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.menu_numeration.menuAction())
        self.menu_numeration.addAction(self.action_num_standart)
        self.menu_numeration.addAction(self.action_num_source)
        self.menu_numeration.addAction(self.action_num_xml_dp)
        self.menu_options.addAction(self.action_options)
        self.menu_options.addSeparator()
        self.menu_options.addAction(self.menu_group.menuAction())
        self.menu_group.addAction(self.action_group_original)
        self.menu_group.addAction(self.action_group_highbit)
        self.menu_group.addAction(self.action_group_lowbit)
        self.menu_help.addAction(self.action_about_qt)

        MainWindow.setMenuBar(self.menubar)

        centralwidget = QWidget(MainWindow)
        MainWindow.setCentralWidget(centralwidget)

        self.toolbar = QToolBar(MainWindow)
        self.tableview = QMainTableView(MainWindow)
        self.colorbar = QColorBar(MainWindow)

        self.colorbar.setVisible(False)

        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        layout = QVBoxLayout(centralwidget)
        layout.setSpacing(8)
        layout.addWidget(self.colorbar)
        layout.addWidget(self.tableview)

        self.monospace = QLineEdit(MainWindow)
        self.monospace.setObjectName('monospace')
        self.monospace.setVisible(False)

        layout.addWidget(self.monospace)

        self.progress_widget = QWidget(MainWindow)
        self.progress_widget.setVisible(False)

        layout_progress = QVBoxLayout(self.progress_widget)
        layout_progress.setContentsMargins(0, 0, 0, 0)

        layout_progress_percent = QHBoxLayout()

        self.progress_label = QLabel(self.progress_widget)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QProgressBar(self.progress_widget)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setValue(-1)

        self.percent_label = QLabel(self.progress_widget)
        self.percent_label.setStyleSheet('padding: 0 5px;')

        layout_progress_percent.addWidget(self.progress_bar)
        layout_progress_percent.addWidget(self.percent_label)

        layout_progress.addWidget(self.progress_label)
        layout_progress.addLayout(layout_progress_percent)

        layout.addWidget(self.progress_widget)

        QMetaObject.connectSlotsByName(MainWindow)
