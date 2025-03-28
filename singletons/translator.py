# -*- coding: utf-8 -*-

import re
import requests
import html.parser
import urllib.request
import urllib.parse
from collections import namedtuple
from typing import List
import time
import random

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
        parts = re.split(r'({.*?})', text)
        translated_parts = []
        for part in parts:
            if part.startswith('{') and part.endswith('}'):
                translated_parts.append(part)
            else:
                if engine.lower() == 'deepl':
                    response = self.__deepl(part)
                else:
                    response = self.__google(part)

                if response.status_code != 200:
                    return response

                translated_parts.append(response.text)

        translated_text = ''.join(translated_parts)
        return Response(200, translated_text)

    @staticmethod
    def __google(text: str, retry_count=0) -> Response:
        print(f"Traduciendo: {text}")  # Registro del texto a traducir
        url = 'http://translate.google.com/m?sl=auto&tl=%s&q=%s'

        language = languages.destination

        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

        if language and language.google:
            link = url % (language.google, urllib.parse.quote(text))
            request = urllib.request.Request(link, headers={'User-Agent': ua})

            try:
                print(f"Enviando solicitud a: {link}")  # Registro de la URL de la solicitud
                data = urllib.request.urlopen(request).read()
                data = data.decode('utf-8')
                expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
                result = re.findall(expr, data)[0]
                print(f"Resultado de la traducción: {result}")  # Registro del resultado de la traducción
                return Response(200, html.unescape(result))
            except urllib.error.HTTPError as e:
                print(f"Error HTTP: {e.code}")  # Registro del código de error HTTP
                if e.code == 429:
                    if retry_count < 5:  # Aumenta el número de reintentos
                        wait_time = (2 ** retry_count) + random.uniform(10, 30)  # Retraso exponencial con aleatoriedad
                        time.sleep(wait_time)
                        return Translator.__google(text, retry_count + 1)
                    else:
                        return Response(e.code, interface.text('Errors', 'Too Many Requests after multiple retries.'))
                else:
                    return Response(e.code, interface.text('Errors', 'Google Translate error: {}').format(e.code))

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
