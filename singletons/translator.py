# -*- coding: utf-8 -*-

import re
import requests
import html.parser
import urllib.request
import urllib.parse
from collections import namedtuple
from typing import List

from singletons.config import config
from singletons.interface import interface
from singletons.languages import languages


Response = namedtuple('Response', 'status_code text')


class Translator:

    @property
    def engines(self) -> List[str]:
        engines = ['Google']
        if config.value('api', 'deepl_key'):
            engines.append('DeepL')
        return engines

    @property
    def available(self) -> bool:
        return len(self.engines) > 0

    def translate(self, engine: str, text: str) -> Response:
        placeholders = re.findall(r'{\d+\.[^{}]+}', text)
        modified_text = text

        temp_placeholders = {}
        for i, placeholder in enumerate(placeholders):
            temp_placeholder = f'__PH_{i}__'
            modified_text = modified_text.replace(placeholder, temp_placeholder)
            temp_placeholders[temp_placeholder] = placeholder

        if engine.lower() == 'deepl':
            response = self.__deepl(modified_text)
        else:
            response = self.__google(modified_text)

        if response.status_code != 200:
            return response

        translated_text = response.text

        for temp_placeholder, placeholder in temp_placeholders.items():
            translated_text = translated_text.replace(temp_placeholder, placeholder)
  
        return Response(response.status_code, translated_text)

    @staticmethod
    def __google(text: str) -> Response:
        url = 'http://translate.google.com/m?sl=auto&tl=%s&q=%s'

        language = languages.destination

        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

        if language and language.google:
            link = url % (language.google, urllib.parse.quote(text))
            request = urllib.request.Request(link, headers={'User-Agent': ua})
            data = urllib.request.urlopen(request).read()

            data = data.decode('utf-8')
            expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
            return Response(200, html.unescape(re.findall(expr, data)[0]))

        return Response(404, interface.text('Errors', 'Language code not found!'))

    @staticmethod
    def __deepl(text: str) -> Response:
        url = 'https://api.deepl.com/v2/translate'
        url_free = 'https://api-free.deepl.com/v2/translate'

        api_key = config.value('api', 'deepl_key')
        api_url = url_free if ":fx" in api_key else url

        language_source = languages.source
        language_dest = languages.destination

        if language_source and language_source.deepl and language_dest and language_dest.deepl:
            payload = {
                'text': text,
                'source_lang': language_source.deepl,
                'target_lang': language_dest.deepl,
                'split_sentences': 1,
                'tag_handling': 'xml'
            }

            response = requests.post(
                api_url,
                headers={'Authorization': f'DeepL-Auth-Key {api_key}'},
                data=payload
            )

            if response.status_code == 200:
                translated_text = response.json()['translations'][0]['text']
                return Response(response.status_code, translated_text)
            elif response.status_code == 403:
                return Response(response.status_code, interface.text('Errors', 'Invalid API key.'))
            elif response.status_code == 456:
                return Response(response.status_code, interface.text('Errors', 'Your quota has exceeded!'))
            elif response.status_code == 500:
                return Response(response.status_code,
                                interface.text('Errors', 'There was a temporary problem with the DeepL Service.'))
            else:
                return Response(response.status_code,
                                interface.text('Errors', 'Translation failed with error code: {}').format(
                                    response.status_code))

        return Response(404, interface.text('Errors', 'Language code not found!'))


translator = Translator()
