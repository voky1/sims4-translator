# -*- coding: utf-8 -*-

import re
import requests
import html.parser
from collections import namedtuple
from typing import List

from singletons.config import config
from singletons.interface import interface
from singletons.languages import languages


Response = namedtuple('Response', 'status_code text')


class Translator:

    @property
    def engines(self) -> List[str]:
        engines = ['Google', 'MyMemory']
        if config.value('api', 'deepl_key'):
            engines.append('DeepL')
        return engines

    @property
    def available(self) -> bool:
        return len(self.engines) > 0

    @staticmethod
    def extract_placeholders(text):
        extracted_items = []

        def save_and_replace_pattern(match):
            extracted_items.append(match.group(0))
            return f"({len(extracted_items) - 1})"

        modified_text = re.sub(r'{[A-Za-z]?\d+\.[^{}]+}|<[^>]+>', save_and_replace_pattern, text)
        return modified_text, extracted_items

    @staticmethod
    def insert_placeholders(text, placeholders):
        for i, placeholder in enumerate(placeholders):
            text = text.replace(f"({i})", placeholder)

        text = re.sub(r'(<[^/][^>]+>)\s+', r'\1', text)
        text = re.sub(r'\s+(</[^>]+>)', r'\1', text)

        return text

    def translate(self, engine: str, text: str) -> Response:
        modified_text, placeholders = self.extract_placeholders(text)

        # placeholder_spaces = []
        # for ph in re.finditer(r'\(\d+\)', modified_text):
        #     before = modified_text[:ph.start()].rstrip()
        #     after = modified_text[ph.end():].lstrip()
        #     has_space_before = len(before) != ph.start()
        #     has_space_after = len(after) != len(modified_text) - ph.end()
        #     placeholder_spaces.append((has_space_before, has_space_after))

        modified_text = modified_text.replace('\\n', "\n")

        if engine.lower() == 'mymemory':
            response = Translator.__mymemory(modified_text)
        elif engine.lower() == 'deepl':
            response = Translator.__deepl(modified_text)
        else:
            response = Translator.__google(modified_text)

        if response.status_code != 200:
            return response

        translated_text = response.text

        # parts = re.split(r'(\(\d+\))', translated_text)
        # for i in range(1, len(parts), 2):
        #     ph_num = int(parts[i][1:-1])
        #     if ph_num < len(placeholder_spaces):
        #         has_space_before, has_space_after = placeholder_spaces[ph_num]
        #         if not has_space_before and parts[i - 1].endswith(' '):
        #             parts[i - 1] = parts[i - 1].rstrip()
        #         if not has_space_after and parts[i + 1].startswith(' '):
        #             parts[i + 1] = parts[i + 1].lstrip()

        # translated_text = ''.join(parts)
        translated_text = translated_text.replace("\n", '\\n')

        translated_text = self.insert_placeholders(translated_text, placeholders)

        return Response(response.status_code, translated_text)

    @staticmethod
    def __google(text: str) -> Response:
        language = languages.destination

        if language and language.google:
            payload = {
                'sl': 'auto',
                'tl': language.google,
                'q': text
            }

            url = 'http://translate.google.com/m?sl=auto'
            ua = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/122.0.0.0 Safari/537.36')

            try:
                req = requests.get(url, params=payload, headers={'User-Agent': ua}, timeout=10)
                if req.status_code == 200:
                    content = req.content.decode('utf-8')
                    expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
                    return Response(200, html.unescape(re.findall(expr, content)[0]))
                else:
                    return Response(req.status_code,
                                    interface.text('Errors', 'Translation failed with error code: {}').format(
                                        req.status_code))
            except Exception as e:
                return Response(500, str(e))

        return Response(404, interface.text('Errors', 'Language code not found!'))

    @staticmethod
    def __mymemory(text: str) -> Response:
        if len(text) > 500:
            return Response(404, interface.text('Errors', 'A maximum of 500 characters is allowed.'))

        src = languages.source
        dst = languages.destination

        if src and src.google and dst and dst.google:
            payload = {
                'langpair': '{}|{}'.format(src.google, dst.google),
                'q': text
            }

            url = 'https://api.mymemory.translated.net/get'
            ua = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/122.0.0.0 Safari/537.36')

            try:
                req = requests.get(url, params=payload, headers={'User-Agent': ua}, timeout=10)
                if req.status_code == 200:
                    content = req.json()
                    return Response(200, content['responseData']['translatedText'])
                else:
                    return Response(req.status_code,
                                    interface.text('Errors', 'Translation failed with error code: {}').format(
                                        req.status_code))
            except Exception as e:
                return Response(500, str(e))

        return Response(404, interface.text('Errors', 'Language code not found!'))

    @staticmethod
    def __deepl(text: str, xml_mode=True) -> Response:
        api_key = config.value('api', 'deepl_key')

        src = languages.source
        dst = languages.destination

        if src and src.deepl and dst and dst.deepl:
            payload = {
                'text': text,
                'source_lang': src.deepl,
                'target_lang': dst.deepl,
                'split_sentences': 1,
                'tag_handling': 'xml' if xml_mode else 'plain'
            }

            url = 'https://api.deepl.com/v2/translate'
            url_free = 'https://api-free.deepl.com/v2/translate'
            api_url = url_free if ':fx' in api_key else url

            try:
                resp = requests.post(
                    api_url,
                    data=payload,
                    headers={'Authorization': f'DeepL-Auth-Key {api_key}'},
                    timeout=10
                )

                if resp.status_code == 200:
                    txt = resp.json()['translations'][0]['text']
                    return Response(200, txt)
                elif resp.status_code == 403:
                    return Response(403, interface.text('Errors', 'Invalid API key.'))
                elif resp.status_code == 456:
                    return Response(456, interface.text('Errors', 'Your quota has exceeded!'))
                elif resp.status_code == 500:
                    return Response(500,
                                    interface.text('Errors', 'There was a temporary problem with the DeepL Service.'))
                else:
                    return Response(resp.status_code,
                                    interface.text('Errors', 'Translation failed with error code: {}').format(
                                        resp.status_code))
            except Exception as e:
                return Response(500, str(e))

        return Response(404, interface.text('Errors', 'Language code not found!'))


translator = Translator()
