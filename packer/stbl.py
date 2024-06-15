# -*- coding: utf-8 -*-

from packer import Packer


class Stbl:

    def __init__(self, rid, value=None):
        self.rid = rid
        self.value = value

        self._strings = {}

    @property
    def language(self):
        return self.rid.language

    @property
    def strings(self):
        if self.value is None:
            return {}

        f = Packer(self.value, mode='r')

        if f.get_raw_bytes(4) != b'STBL':
            return {}

        version = f.get_uint16()
        if version != 5:
            return {}

        _compressed = f.get_uint8()
        num_entries = f.get_uint64()

        f.seek += 2

        _strings_length = f.get_uint32()

        _strings = {}

        get_uint32 = f.get_uint32

        for i in range(num_entries):
            key = get_uint32()
            _flags = f.get_uint8()
            length = f.get_uint16()
            val = f.get_raw_bytes(length).decode('utf-8')
            _strings[key] = val

        return _strings

    @property
    def binary(self):
        f = Packer(b'', mode='w')

        f.put_raw_bytes(b'STBL')
        f.put_uint16(5)
        f.put_uint8(0)

        num_entries = len(self._strings)
        f.put_uint64(num_entries)

        f.seek += 2

        strings_length = num_entries
        for key, value in self._strings.items():
            strings_length += len(value.encode('utf-8'))

        f.put_uint32(strings_length)

        for key, value in self._strings.items():
            f.put_uint32(key)
            f.put_int8(0)
            _value = value.encode('utf-8')
            f.put_uint16(len(_value))
            f.put_raw_bytes(_value)

        return f.get_content()

    def add(self, key, value):
        self._strings[key] = value.replace("\r", '').replace("\n", '\\n') if value else ''
