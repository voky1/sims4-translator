# -*- coding: utf-8 -*

class AppState:

    def __init__(self):
        self.packages_storage = None
        self.dictionaries_storage = None

        self.current_package = None
        self.current_instance = 0

        self.tableview = None
        self.monospace = None

    def set_monospace(self, monospace):
        self.monospace = monospace

    def set_tableview(self, tableview):
        self.tableview = tableview

    def set_packages_storage(self, packages_storage):
        self.packages_storage = packages_storage

    def set_dictionaries_storage(self, dictionaries_storage):
        self.dictionaries_storage = dictionaries_storage

    def set_current_package(self, current_package):
        self.current_package = current_package

    def set_current_instance(self, current_instance):
        self.current_instance = current_instance


app_state = AppState()
