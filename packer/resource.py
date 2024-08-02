# -*- coding: utf-8 -*-

import re
from collections import namedtuple
from typing import Union

from singletons.config import config
from singletons.languages import languages


FORMATTERS = {
    's4pe': 'S4_{id.type:08X}_{id.group:08X}_{id.instance:016X}',
    'colon': '{id.group:08x}:{id.instance:016x}:{id.type:08x}',
    'maxis': '{id.group:08x}!{id.instance:016x}.{id.type:08x}',
}

PARSERS = {
    's4pe': '^S4_{type}_{group}_{instance}(?:%%.*)?$',
    'colon': '^{group}:{instance}:{type}$',
    'maxis': '^{group}!{instance}.{type}$',
}

for fmt, value in PARSERS.items():
    PARSERS[fmt] = re.compile(value.format(type="(?P<type>[0-9A-Fa-f]{,8})",
                                           group="(?P<group>[0-9A-Fa-f]{,8})",
                                           instance="(?P<instance>[0-9A-Fa-f]{,16})"))


class Resource(namedtuple('Resource', 'id locator size package')):

    __slots__ = ()

    @property
    def content(self):
        return self.package.content(self)

    def __eq__(self, other):
        return (self.id == other.id and
                self.locator == other.locator and
                self.size == other.size and
                self.package is other.package)

    def __ne__(self, other):
        return not (self == other)


class ResourceID(namedtuple('ResourceID', 'group instance type')):

    __slots__ = ()

    DEFAULT_FMT = 's4pe'

    def __str__(self) -> str:
        return FORMATTERS[self.DEFAULT_FMT].format(id=self)

    @property
    def filename(self) -> str:
        return str(self)

    @classmethod
    def from_string(cls, string: str):
        for parser in PARSERS.values():
            m = parser.match(string)
            if m:
                return cls(
                    int(m.group('group'), 16),
                    int(m.group('instance'), 16),
                    int(m.group('type'), 16),
                )
        else:
            return cls(group=0x80000000 if config.value('group', 'highbit') else 0,
                       instance=0,
                       type=0x220557DA)

    @property
    def str_group(self) -> str:
        return '{group:08x}'.format(group=self.group)

    @property
    def str_instance(self) -> str:
        return '{instance:016x}'.format(instance=self.instance)

    @property
    def hex_instance(self) -> str:
        return '0x{instance:016X}'.format(instance=self.instance)

    @property
    def base_instance(self) -> int:
        hex_inst = self.hex_instance
        return int(hex_inst[4:], 16)

    @property
    def is_stbl(self) -> bool:
        return self.type == 0x220557DA

    @property
    def language(self) -> Union[str, None]:
        if self.type == 0x220557DA:
            code = '0x{id:016X}'.format(id=self.instance)[:4]
            language = languages.by_code(code)
            return language.locale if language else None
        return None

    @property
    def language_code(self) -> Union[str, None]:
        if self.type == 0x220557DA:
            return '0x{id:016X}'.format(id=self.instance)[:4]
        return None

    def convert_group(self, highbit: bool = False):
        group = ('8' if highbit else '0') + self.str_group[1:]
        return self._replace(group=int(group, 16))

    def convert_instance(self, locale: str = None):
        if not locale:
            locale = config.value('translation', 'destination')
        language = languages.by_locale(locale)
        instance = int(language.code + self.str_instance[2:], 16)
        return self._replace(instance=instance)
