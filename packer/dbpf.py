# -*- coding: utf-8 -*-

import io
import zlib
import contextlib
from collections import namedtuple

from packer.resource import Resource, ResourceID
from packer import Packer


_Header = namedtuple('_Header', 'file_version user_version ctime mtime index_count index_pos index_size')


class DbpfLocator(namedtuple('DbpfLocator', 'offset length compression')):

    @property
    def deleted(self):
        return self.compression[0] == 0xFFE0


class _DbpfReader:

    def __init__(self, fstream):
        self.f = Packer(fstream, mode='r')
        self.header = None

    def get_header(self):
        if self.header is not None:
            return self.header

        with self.f.at(0):
            if self.f.get_raw_bytes(4) != b'DBPF':
                return None

            file_version = (self.f.get_uint32(), self.f.get_uint32())
            if file_version != (2, 1):
                return None

            user_version = (self.f.get_uint32(), self.f.get_uint32())
            _unused = self.f.get_uint32()
            creation_time = self.f.get_uint32()
            updated_time = self.f.get_uint32()
            _unused = self.f.get_uint32()
            index_entry_count = self.f.get_uint32()
            index_pos_low = self.f.get_uint32()
            index_size = self.f.get_uint32()
            self.f.seek += 16
            index_pos_high = self.f.get_uint32()
            self.f.seek += 24

            if index_pos_high != 0:
                index_pos = index_pos_high
            else:
                index_pos = index_pos_low

            self.header = _Header(file_version,
                                  user_version,
                                  creation_time,
                                  updated_time,
                                  index_entry_count,
                                  index_pos,
                                  index_size)

            return self.header

    def get_index(self, package=None):
        _CONST_TYPE = 1
        _CONST_GROUP = 2
        _CONST_INSTANCE_EX = 4

        header = self.get_header()

        if not header:
            return []

        if header.index_pos == 0:
            if header.index_count != 0:
                # raise Exception('Package contains entries but no index')
                pass
            return []

        with self.f.at(header.index_pos):
            flags = self.f.get_uint32()

            if flags & _CONST_TYPE:
                entry_type = self.f.get_uint32()
            if flags & _CONST_GROUP:
                entry_group = self.f.get_uint32()
            if flags & _CONST_INSTANCE_EX:
                entry_inst_ex = self.f.get_uint32()

            for _ in range(header.index_count):
                if not flags & _CONST_TYPE:
                    entry_type = self.f.get_uint32()
                if not flags & _CONST_GROUP:
                    entry_group = self.f.get_uint32()
                if not flags & _CONST_INSTANCE_EX:
                    entry_inst_ex = self.f.get_uint32()

                entry_inst = self.f.get_uint32()
                entry_pos = self.f.get_uint32()
                entry_size = self.f.get_uint32()

                entry_size_decompressed = self.f.get_uint32()
                if entry_size & 0x80000000:
                    entry_compressed = (self.f.get_uint16(), self.f.get_uint16())
                else:
                    entry_compressed = (0, 1)
                entry_size &= 0x7FFFFFFF

                with self.f.at(None):
                    yield Resource(id=ResourceID(entry_group, entry_inst_ex << 32 | entry_inst, entry_type),
                                   locator=DbpfLocator(entry_pos, entry_size, entry_compressed),
                                   size=entry_size_decompressed,
                                   package=package)

    def write_index(self, idx):
        pass

    def put_rsrc(self, content):
        pass


class _DbpfWriter:

    def __init__(self, fstream):
        self.stream = fstream
        self.f = Packer(fstream, mode='w')
        self.f.seek = 96

    def put_rsrc(self, content):
        seek = self.f.seek
        zcontent = zlib.compress(content)
        self.f.put_raw_bytes(zcontent)
        locator = DbpfLocator(seek, len(zcontent), (0x5A42, 1))
        return locator

    def write_index(self, idx):
        with self.f.at(None):
            idx_start = self.f.seek
            idx_count = 0

            self.f.put_uint32(0)

            for rsrc in idx.values():
                if rsrc.locator.length & 0x80000000 != 0:
                    raise Exception('File must be smaller than 2GB')

                idx_count += 1

                self.f.put_uint32(rsrc.id.type)
                self.f.put_uint32(rsrc.id.group)
                self.f.put_uint32(rsrc.id.instance >> 32)
                self.f.put_uint32(rsrc.id.instance & 0xFFFFFFFF)
                self.f.put_uint32(rsrc.locator.offset)
                self.f.put_uint32(rsrc.locator.length | 0x80000000)
                self.f.put_uint32(rsrc.size)
                self.f.put_uint16(rsrc.locator.compression[0])
                self.f.put_uint16(rsrc.locator.compression[1])

            idx_end = self.f.seek

        header = _Header((2, 1), (0, 0), 0, 0, idx_count, idx_start, idx_end - idx_start)
        self.put_header(header)

    def put_header(self, header):
        with self.f.at(0):
            self.f.put_raw_bytes(b'DBPF')
            self.f.put_uint32(header.file_version[0])
            self.f.put_uint32(header.file_version[1])
            self.f.put_uint32(header.user_version[0])
            self.f.put_uint32(header.user_version[1])
            self.f.put_uint32(0)
            self.f.put_uint32(header.ctime)
            self.f.put_uint32(header.mtime)
            self.f.put_uint32(0)
            self.f.put_uint32(header.index_count)
            self.f.put_uint32(0)
            self.f.put_uint32(header.index_size)
            self.f.put_uint32(0)
            self.f.put_uint32(0)
            self.f.put_uint32(0)
            self.f.put_uint32(3)
            self.f.put_uint32(header.index_pos)
            for _ in range(6):
                self.f.put_uint32(0)


class DbpfPackage:

    def __init__(self, name, mode='r'):
        super().__init__()

        if isinstance(name, io.RawIOBase):
            self.package = _DbpfReader(name)
        else:
            if mode == 'w':
                self.package = _DbpfWriter(open(name, 'w+b'))
                self._index_cache = {}
                self.writable = True
            else:
                self.package = _DbpfReader(open(name, 'rb'))
                self._index_cache = None
                self.writable = False

    def __getitem__(self, rid):
        if isinstance(rid, ResourceID):
            if self._index_cache is None:
                self.search()
            return self._index_cache[rid] if rid in self._index_cache else None
        return None

    def search(self, code=None):
        if self._index_cache is None:
            self._index_cache = {}
            for entry in self.package.get_index(self):
                if entry.locator.deleted or code and entry.id.type != code:
                    continue
                self._index_cache[entry.id] = entry
        return self._index_cache.keys()

    def search_stbl(self):
        return self.search(0x220557DA)

    def content(self, resource):
        assert isinstance(resource, Resource)
        assert resource.package is self

        with self.package.f.at(resource.locator.offset):
            ibuf = self.package.f.get_raw_bytes(resource.locator.length)

        if resource.locator.compression[0] == 0:
            return ibuf
        elif resource.locator.compression[0] == 0xFFFE:
            return decode_ref_pack(ibuf)
        elif resource.locator.compression[0] == 0xFFFF:
            return decode_ref_pack(ibuf)
        elif resource.locator.compression[0] == 0x5A42:
            return zlib.decompress(ibuf, 15, resource.size)

    def commit(self):
        if self.writable:
            self.package.write_index(self._index_cache)
            self.close()

    def put(self, rid, content):
        if self.writable:
            self._index_cache[rid] = Resource(id=rid,
                                              locator=self.package.put_rsrc(content),
                                              size=len(content),
                                              package=self)

    def close(self):
        self.package.f.close()

    @staticmethod
    @contextlib.contextmanager
    def read(name):
        dbfile = DbpfPackage(name, mode='r')
        try:
            yield dbfile
        finally:
            dbfile.close()

    @staticmethod
    @contextlib.contextmanager
    def write(name):
        dbfile = DbpfPackage(name, mode='w')
        try:
            yield dbfile
        finally:
            dbfile.commit()


def decode_ref_pack(ibuf):
    if ibuf[1] != 0xFB:
        raise Exception('Invalid compressed data')

    iptr = 2
    optr = 0
    flags = ibuf[0]
    osize = 0

    for _ in range(4 if flags & 0x80 else 3):
        osize = (osize << 8) | ibuf[iptr]
        iptr += 1

    obuf = bytearray(osize)
    while iptr < len(ibuf):
        copy_offset = 0
        cc0 = ibuf[iptr]
        iptr += 1
        if cc0 <= 0x7F:
            cc1 = ibuf[iptr]
            iptr += 1
            _cc = (cc0, cc1)
            num_plaintext = cc0 & 0x03
            num_to_copy = ((cc0 & 0x1C) >> 2) + 3
            copy_offset = ((cc0 & 0x60) << 3) + cc1
        elif cc0 <= 0xBF:
            cc1 = ibuf[iptr]
            iptr += 1
            cc2 = ibuf[iptr]
            iptr += 1
            _cc = (cc0, cc1, cc2)
            num_plaintext = (cc1 & 0xC0) >> 6
            num_to_copy = (cc0 & 0x3F) + 4
            copy_offset = ((cc1 & 0x3F) << 8) + cc2
        elif cc0 <= 0xDF:
            cc1 = ibuf[iptr]
            iptr += 1
            cc2 = ibuf[iptr]
            iptr += 1
            cc3 = ibuf[iptr]
            iptr += 1
            _cc = (cc0, cc1, cc2, cc3)
            num_plaintext = cc0 & 0x03
            num_to_copy = ((cc0 & 0x0C) << 6) + cc3 + 5
            copy_offset = ((cc0 & 0x10) << 12) + (cc1 << 8) + cc2
        elif cc0 <= 0xFB:
            _cc = (cc0,)
            num_plaintext = ((cc0 & 0x1F) << 2) + 4
            num_to_copy = 0
        else:
            _cc = (cc0,)
            num_plaintext = cc0 & 3
            num_to_copy = 0

        obuf[optr:optr + num_plaintext] = ibuf[iptr:iptr + num_plaintext]
        iptr += num_plaintext
        optr += num_plaintext

        for _ in range(num_to_copy):
            obuf[optr] = obuf[optr - 1 - copy_offset]
            optr += 1

    return bytes(obuf)
