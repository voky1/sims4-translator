# -*- coding: utf-8 -*-

import os
from collections import namedtuple
from typing import List, Dict, Union

from singletons.config import config
from singletons.interface import interface


class Expansion(namedtuple('Expansion', 'names folder')):

    names: Union[str, Dict[str, str]]
    folder: str

    @property
    def status(self) -> str:
        if self.exists:
            if not self.exists_source:
                return interface.text('OptionsDialog', '{} not exist').format(expansions.strings_source)
            elif not self.exists_dest:
                return interface.text('OptionsDialog', '{} not exist').format(expansions.strings_dest)
            else:
                return interface.text('OptionsDialog', 'FOUND')
        else:
            return interface.text('OptionsDialog', 'NOT FOUND')

    @property
    def name(self) -> str:
        if isinstance(self.names, str):
            return interface.text('OptionsDialog', self.names)
        elif isinstance(self.names, dict):
            key = 'name_' + config.value('interface', 'language').lower()
            return self.names.get(key, self.names.get('name_en_us', self.folder))
        else:
            return self.folder

    @property
    def offset(self) -> str:
        return '' if '/' in self.folder else '  '

    @property
    def dictionary(self) -> str:
        return 'BASE' if '/' in self.folder else self.folder

    @property
    def file_source(self) -> str:
        return str(
            os.path.join(config.value('dictionaries', 'gamepath'),
                         self.folder, expansions.strings_source + '.package'))

    @property
    def file_dest(self) -> str:
        return str(os.path.join(config.value('dictionaries', 'gamepath'),
                                self.folder, expansions.strings_dest + '.package'))

    @property
    def exists_source(self) -> bool:
        return os.path.exists(self.file_source)

    @property
    def exists_dest(self) -> bool:
        return os.path.exists(self.file_dest)

    @property
    def exists_strings(self) -> bool:
        return self.exists_source and self.exists_dest

    @property
    def exists(self) -> bool:
        path = config.value('dictionaries', 'gamepath')
        if path:
            return os.path.exists(os.path.join(path, self.folder))
        return False


class Expansions:

    def __init__(self) -> None:
        self.__packs = None

    @property
    def items(self) -> List[Union[str, Expansion]]:
        baseexp = Expansion('BASE GAME', 'Data/Client')

        rows = [baseexp]

        exp = ['', 'Expansion packs']
        game = ['', 'Game packs']
        stuff = ['', 'Stuff packs']

        packs = self._parse_expansion_packs()

        if packs:
            for key, items in packs.items():
                if key.upper().startswith('EP'):
                    exp.append(Expansion(items, key))
                elif key.upper().startswith('GP'):
                    game.append(Expansion(items, key))
                elif key.upper().startswith('SP'):
                    stuff.append(Expansion(items, key))

        elif baseexp.exists_source:
            for dirname in os.listdir(config.value('dictionaries', 'gamepath')):
                if dirname.upper().startswith('EP'):
                    exp.append(Expansion(dirname, dirname))
                elif dirname.upper().startswith('GP'):
                    game.append(Expansion(dirname, dirname))
                elif dirname.upper().startswith('SP'):
                    stuff.append(Expansion(dirname, dirname))

        if len(exp) > 2:
            rows.extend(exp)
        if len(game) > 2:
            rows.extend(game)
        if len(stuff) > 2:
            rows.extend(stuff)

        return rows

    @property
    def strings_source(self) -> str:
        return 'Strings_' + config.value('translation', 'source')

    @property
    def strings_dest(self) -> str:
        return 'Strings_' + config.value('translation', 'destination')

    def exists(self) -> List[Expansion]:
        return [exp for exp in self.items if isinstance(exp, Expansion) and exp.exists_strings]
    
    def _parse_expansion_packs(self) -> Dict[str, Dict[str, str]]:
        if self.__packs is not None:
            return self.__packs

        self.__packs = {}

        try:
            with open('./prefs/dlc.ini', 'r', encoding='utf-8') as fp:
                content = fp.read()
        except FileNotFoundError:
            return {}

        current_pack = None

        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                pack_code = line[1:-1]
                current_pack = {}
                self.__packs[pack_code] = current_pack
            elif '=' in line and current_pack is not None:
                key, value = line.split('=', 1)
                key = key.lower().strip()
                if key.startswith('name_'):
                    current_pack[key] = value.strip()

        return self.__packs


expansions = Expansions()
