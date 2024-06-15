# -*- coding: utf-8 -*-

import os
from collections import namedtuple
import xml.etree.ElementTree as ElementTree

from singletons.config import config
from utils.singleton import Singleton


Lang = namedtuple('Lang', 'locale code google deepl')


class Language(metaclass=Singleton):

    def __init__(self) -> None:
        self.__locales = {}
        self.__codes = {}
        self.__load()

    def __load(self):
        languages_file = os.path.abspath('./prefs/languages.xml')

        if not os.path.exists(languages_file):
            return

        with open(languages_file, 'r', encoding='utf-8') as fp:
            content = fp.read()

        try:
            parser = ElementTree.XMLParser(encoding='utf-8')
            root = ElementTree.fromstring(content, parser=parser)
        except ElementTree.ParseError:
            return

        for item in root.findall('language'):
            locale = item.get('locale')
            code = item.get('code')
            if locale and code:
                lang = Lang(locale.upper(), code, item.get('google-code'), item.get('deepl-code'))
                self.__locales[lang.locale] = lang
                self.__codes[lang.code] = lang

    @property
    def locales(self) -> list:
        return list(self.__locales.keys())
    
    @property
    def source(self) -> Lang:
        return self.by_locale(config.value('translation', 'source'))

    @property
    def destination(self) -> Lang:
        return self.by_locale(config.value('translation', 'destination'))

    def by_locale(self, locale: str) -> Lang:
        return self.__locales.get(locale)

    def by_code(self, code: str) -> Lang:
        return self.__codes.get(code)


language = Language()
