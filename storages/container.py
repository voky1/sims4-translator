# -*- coding: utf-8 -*-

import os
import xml.etree.ElementTree as ElementTree
from typing import List

from packer.dbpf import DbpfPackage
from packer.resource import ResourceID
from packer.stbl import Stbl

from singletons.config import config
from singletons.state import app_state
from utils.functions import md5, parsexml


class Container:

    def __init__(self, path: str) -> None:
        self.path = path
        self.directory = os.path.dirname(path)
        self.fullname = os.path.basename(path)
        self.name = os.path.splitext(self.fullname)[0]

        self.key = '[' + md5(path)[0:8] + '] ' + self.fullname

        self.instances = []
        self.modified = False

        self.__len = 0

    @property
    def is_package(self) -> bool:
        return self.fullname.lower().endswith('.package')

    @property
    def is_stbl(self) -> bool:
        return self.fullname.lower().endswith('.stbl')

    @property
    def is_xml(self) -> bool:
        return self.fullname.lower().endswith('.xml')

    @property
    def filename(self) -> str:
        language_source = config.value('translation', 'source')
        language_dest = config.value('translation', 'destination')
        template_conflict = config.value('template', 'conflict')
        template_non_conflict = config.value('template', 'non_conflict')
        template = template_non_conflict if config.value('save', 'experemental') else template_conflict
        return template.format(name=self.name, lang_s=language_source, lang_d=language_dest)

    def open(self) -> List[tuple]:
        filename = os.path.join(self.directory, self.fullname)

        if not os.path.exists(filename):
            return []

        items = []

        if self.is_package:
            items = self.open_package(filename)
        if self.is_stbl:
            items = self.open_stbl(filename)
        elif self.is_xml:
            items = self.open_xml(filename)

        self.__len = len(items)

        return items

    def open_package(self, filename: str) -> List[tuple]:
        language_source = config.value('translation', 'source')
        language_dest = config.value('translation', 'destination')

        items = []

        _from = {}
        _to = {}
        _tmp = {}

        flag = None

        with DbpfPackage.read(filename) as dbfile:
            for rid in dbfile.search_stbl():
                stbl = Stbl(rid=rid, value=dbfile[rid].content)
                language = rid.language
                if language == language_source:
                    _from[rid] = stbl.strings
                elif language == language_dest:
                    _to[rid] = stbl.strings
                else:
                    if flag is None:
                        flag = language
                    if language == flag:
                        _tmp[rid] = stbl.strings

        if not _from and not _to:
            if _tmp:
                _from = _tmp
            else:
                return []

        if not _from and _to:
            _from = _to
            merge = False
        elif _from and not _to:
            merge = False
        else:
            merge = True

        if merge:
            __to = {}

            for rid, strings in _to.items():
                for sid, dest in strings.items():
                    key = f'{rid.base_instance}_{sid}'
                    __to[key] = (rid, dest)

            for rid, strings in _from.items():
                line = 0
                for sid, source in strings.items():
                    if source:
                        key = f'{rid.base_instance}_{sid}'
                        dest = source
                        if key in __to:
                            rid = __to[key][0]
                            dest = __to[key][1]

                        if rid.hex_instance not in self.instances:
                            self.instances.append(rid.hex_instance)

                        line += 1
                        items.append((rid, sid, source, dest, '', line, line))

        else:
            for rid, strings in _from.items():
                line = 0
                for sid, source in strings.items():
                    if source:
                        if rid.hex_instance not in self.instances:
                            self.instances.append(rid.hex_instance)
                        line += 1
                        items.append((rid, sid, source, source, '', line, line))

        return items

    def open_stbl(self, filename: str) -> List[tuple]:
        items = []

        rid = ResourceID.from_string(self.name)
        self.instances.append(rid.hex_instance)
        with open(filename, 'rb') as fp:
            stbl = Stbl(rid, fp.read())
            line = 0
            for sid, source in stbl.strings.items():
                line += 1
                items.append((rid, sid, source, source, '', line, line))

        return items

    def open_xml(self, filename: str) -> List[tuple]:
        items = []

        with open(filename, 'r', encoding='utf-8') as fp:
            content = parsexml(fp.readlines())

        try:
            parser = ElementTree.XMLParser(encoding='utf-8')
            tree = ElementTree.fromstring(content, parser=parser)
        except ElementTree.ParseError:
            return []

        if tree.findall('TextStringDefinitions/TextStringDefinition'):
            rid = ResourceID.from_string(self.name)
            self.instances.append(rid.hex_instance)
            i = 1
            for s in tree.findall('TextStringDefinitions/TextStringDefinition'):
                sid = int(s.get('InstanceID'), 16)
                source = s.get('TextString')
                line = int(s.get('DUMMY_LINE'))
                items.append((rid, sid, source, source, '', line, i))
                i += 1

        else:
            resources = {}

            for table in tree.findall('Content/Table'):
                instance = table.get('instance')
                if instance:
                    group = table.get('group')
                    if not group:
                        group = '80000000' if config.value('group', 'highbit') else '00000000'

                    key = md5(instance + group)
                    if key not in resources:
                        resources[key] = ResourceID(group=int(group, 16),
                                                    instance=int(instance, 16),
                                                    type=0x220557DA)
                        if resources[key].hex_instance not in self.instances:
                            self.instances.append(resources[key].hex_instance)

                    i = 1
                    for s in table.findall('String'):
                        sid = int(s.get('id'), 16)
                        source = s.find('Source').text
                        dest = s.find('Dest').text
                        comment = s.find('Comment').text if s.find('Comment') is not None else ''
                        line = int(s.get('DUMMY_LINE'))
                        items.append((resources[key], sid, source, dest, comment, line, i))
                        i += 1

        return items

    def save(self, path: str = None) -> None:
        if not path:
            path = os.path.join(self.directory, self.filename + '.package')
        app_state.packages_storage.save(path)

    def finalize(self, path: str = None) -> None:
        if not path:
            path = os.path.join(self.directory, self.name + '.package')
        app_state.packages_storage.finalize(self.path, path)

    def backup(self, path: str = None) -> str:
        backup = (path if path else self.path) + '.backup'
        os.rename(self.path, backup)
        return backup

    def modify(self, state: bool = True) -> None:
        self.modified = state

    def __len__(self) -> int:
        return self.__len
