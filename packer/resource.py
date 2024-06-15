# -*- coding: utf-8 -*-

import re
from collections import namedtuple

from singletons.config import config
from singletons.language import language


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

    def __str__(self):
        return FORMATTERS[self.DEFAULT_FMT].format(id=self)

    @property
    def filename(self):
        return str(self)

    @classmethod
    def from_string(cls, string):
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
    def str_group(self):
        return '{group:08x}'.format(group=self.group)

    @property
    def str_instance(self):
        return '{instance:016x}'.format(instance=self.instance)

    @property
    def hex_instance(self):
        return '0x{instance:016X}'.format(instance=self.instance)

    @property
    def is_stbl(self):
        return self.type == 0x220557DA

    @property
    def language(self):
        if self.type == 0x220557DA:
            code = '0x{id:016X}'.format(id=self.instance)[:4]
            lang = language.by_code(code)
            return lang.locale if lang else None
        return None

    @property
    def language_code(self):
        if self.type == 0x220557DA:
            return '0x{id:016X}'.format(id=self.instance)[:4]
        return None

    def convert_group(self, highbit: bool = False):
        group = ('8' if highbit else '0') + self.str_group[1:]
        return self._replace(group=int(group, 16))

    def convert_instance(self, locale=None):
        if not locale:
            locale = config.value('translation', 'destination')
        lang = language.by_locale(locale)
        instance = int(lang.code + self.str_instance[2:], 16)
        return self._replace(instance=instance)
