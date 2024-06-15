# -*- coding: utf-8 -*-

import os
import glob
import xml.etree.ElementTree as ElementTree
from collections import namedtuple
from typing import Dict, Optional, List

from singletons.config import config
from utils.singleton import Singleton


class Lang(namedtuple('Lang', 'code name items')):

    code: str
    name: str
    items: Dict[str, Dict[str, Optional[str]]]

    def get(self, k: str, v: str) -> str:
        if k in self.items and v in self.items[k]:
            value = self.items[k][v]
            return value.strip() if value is not None else v.strip()
        return v.strip()


class Interface(metaclass=Singleton):

    def __init__(self) -> None:
        self.__languages = {}
        self.__current = None
        self.__load()

    def __load(self) -> None:
        files = glob.glob(os.path.join('./prefs/interface', '*.xml'))

        for f in files:
            with open(f, 'r', encoding='utf-8') as fp:
                content = fp.read()

            try:
                parser = ElementTree.XMLParser(encoding='utf-8')
                root = ElementTree.fromstring(content, parser=parser)
            except ElementTree.ParseError:
                continue

            code = root.get('language')
            name = root.get('name')

            if code and name and root.findall('context'):
                lang_items = {}

                for context in root.findall('context'):
                    key = context.get('name')
                    if key:
                        context_items = {}

                        for s in context.findall('string'):
                            source = s.find('source')
                            translation = s.find('translation')
                            if source is not None and translation is not None:
                                context_items[source.text] = translation.text

                        lang_items[key] = context_items

                self.__languages[code] = Lang(code, name, lang_items)

        self.reload()

    def reload(self) -> None:
        self.__current = self.__languages.get(config.value('interface', 'language'), None)

    def text(self, k: str, v: str) -> str:
        return self.__current.get(k, v) if isinstance(self.__current, Lang) else v
    
    @property
    def languages(self) -> List[Lang]:
        return list(self.__languages.values())

    @property
    def current_index(self) -> int:
        keys = list(self.__languages.keys())
        interface_value = config.value('interface', 'language')
        if interface_value in keys:
            return keys.index(interface_value)
        return 0


interface = Interface()
