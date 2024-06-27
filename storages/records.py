# -*- coding: utf-8 -*-

from packer.resource import ResourceID
from utils.functions import compare
from utils.constants import *


class AbstractRecord(list):

    def __init__(self, *args):
        super().__init__(args)


class MainRecord(AbstractRecord):

    @property
    def idx(self) -> int:
        return self[RECORD_MAIN_INDEX]

    @idx.setter
    def idx(self, value: int) -> None:
        self[RECORD_MAIN_INDEX] = value

    @property
    def idx_standart(self) -> int:
        return self[RECORD_MAIN_INDEX_ALT][0]

    @property
    def idx_source(self) -> int:
        return self[RECORD_MAIN_INDEX_ALT][1]

    @property
    def idx_dp(self) -> int:
        return self[RECORD_MAIN_INDEX_ALT][1]

    @property
    def id(self) -> int:
        return self[RECORD_MAIN_ID]

    @property
    def id_hex(self) -> str:
        return '0x{sid:08X}'.format(sid=self[RECORD_MAIN_ID])

    @property
    def instance(self) -> int:
        return self[RECORD_MAIN_INSTANCE]

    @property
    def instance_hex(self) -> str:
        return '0x{instance:016X}'.format(instance=self[RECORD_MAIN_INSTANCE])

    @property
    def group(self) -> int:
        return self[RECORD_MAIN_GROUP]

    @property
    def group_hex(self) -> str:
        return '0x{group:08X}'.format(group=self[RECORD_MAIN_GROUP])

    @property
    def source(self) -> str:
        return self[RECORD_MAIN_SOURCE]

    @property
    def source_old(self) -> str:
        return self[RECORD_MAIN_SOURCE_OLD]

    @source_old.setter
    def source_old(self, value: str) -> None:
        self[RECORD_MAIN_SOURCE_OLD] = value

    @property
    def translate(self) -> str:
        return self[RECORD_MAIN_TRANSLATE]

    @translate.setter
    def translate(self, value: str) -> None:
        self[RECORD_MAIN_TRANSLATE] = value

    @property
    def translate_old(self) -> str:
        return self[RECORD_MAIN_TRANSLATE_OLD]

    @translate_old.setter
    def translate_old(self, value: str) -> None:
        self[RECORD_MAIN_TRANSLATE_OLD] = value

    @property
    def flag(self) -> int:
        return self[RECORD_MAIN_FLAG]

    @flag.setter
    def flag(self, value: int) -> None:
        self[RECORD_MAIN_FLAG] = value

    @property
    def resource(self) -> ResourceID:
        return self[RECORD_MAIN_RESOURCE]

    @property
    def resource_original(self) -> ResourceID:
        return self[RECORD_MAIN_RESOURCE_ORIGINAL]

    @property
    def package(self) -> str:
        return self[RECORD_MAIN_PACKAGE]

    @property
    def comment(self) -> str:
        return self[RECORD_MAIN_COMMENT]

    @comment.setter
    def comment(self, value: str) -> None:
        self[RECORD_MAIN_COMMENT] = value

    def compare(self) -> bool:
        return compare(self[RECORD_MAIN_SOURCE], self[RECORD_MAIN_TRANSLATE])
