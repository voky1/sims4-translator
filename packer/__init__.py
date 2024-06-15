# -*- coding: utf-8 -*-

import io
import contextlib
import struct
import zlib
import json


class Packer:

    def __init__(self, bstr, mode='r'):
        self.writable = (mode == 'w')

        if isinstance(bstr, bytes):
            self.raw_len = len(bstr)
            bstr = io.BytesIO(bstr)
        else:
            bstr.seek(0, io.SEEK_END)
            self.raw_len = bstr.tell()
            bstr.seek(0)

        self.raw = bstr

    @property
    def seek(self):
        return self.raw.tell()

    @seek.setter
    def seek(self, val):
        if self.writable or val <= self.raw_len:
            self.raw.seek(val)

    @contextlib.contextmanager
    def at(self, pos):
        saved = self.seek
        try:
            if pos is not None:
                self.seek = pos
            yield
        finally:
            self.seek = saved

    def _get_int(self, size, signed=False):
        return int.from_bytes(self.raw.read(size), 'little', signed=signed)

    def get_byte(self):
        return self._get_int(1, False)

    def get_float(self):
        return struct.unpack('f', self.get_raw_bytes(4))[0]

    def get_int8(self):
        return self._get_int(1, True)

    def get_int16(self):
        return self._get_int(2, True)

    def get_int32(self):
        return self._get_int(4, True)

    def get_int64(self):
        return self._get_int(8, True)

    def get_uint8(self):
        return self._get_int(1, False)

    def get_uint16(self):
        return self._get_int(2, False)

    def get_uint32(self):
        return self._get_int(4, False)

    def get_uint64(self):
        return self._get_int(8, False)

    def _put_int(self, i, length, signed):
        self.raw.write(i.to_bytes(length, 'little', signed=signed))

    def put_byte(self, i):
        self._put_int(i, 1, False)

    def put_float(self, i):
        self.put_raw_bytes(struct.pack('f', i))

    def put_int8(self, i):
        self._put_int(i, 1, True)

    def put_int16(self, i):
        self._put_int(i, 2, True)

    def put_int32(self, i):
        self._put_int(i, 4, True)

    def put_int64(self, i):
        self._put_int(i, 8, True)

    def put_uint8(self, i):
        self._put_int(i, 1, False)

    def put_uint16(self, i):
        self._put_int(i, 2, False)

    def put_uint32(self, i):
        self._put_int(i, 4, False)

    def put_uint64(self, i):
        self._put_int(i, 8, False)

    def get_raw_bytes(self, count):
        return self.raw.read(count)

    def put_raw_bytes(self, bstr):
        self.raw.write(bstr)

    def get_string(self, length=0, compress=True):
        if not length:
            length = self.get_uint32()
            compress = self.get_byte()
        content = self.get_raw_bytes(length)
        if compress:
            content = zlib.decompress(content)
        return content.decode('utf-8')

    def put_string(self, value):
        value = value.encode('utf-8')
        if len(value) > 50:
            content = zlib.compress(value)
            self.put_uint32(len(content))
            self.put_byte(1)
            self.put_raw_bytes(content)
        else:
            self.put_uint32(len(value))
            self.put_byte(0)
            self.put_raw_bytes(value)

    def get_json(self, length=0):
        return json.loads(self.get_string(length))

    def put_json(self, value):
        self.put_string(json.dumps(value))

    def get_content(self):
        with self.at(0):
            return self.raw.read()

    def close(self):
        self.raw.close()
