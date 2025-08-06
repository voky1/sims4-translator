# -*- coding: utf-8 -*-

import re
import requests
import html
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
        # Normalize line breaks
        temp = text.replace('\\ N', '\\N').replace('\\ n', '\\n')
        temp = temp.replace('\\N', '\n').replace('\\n', '\n')

        # Use different strategies based on the engine
        if engine.lower() == 'deepl':
            # DeepL handles XML tags well, use the XML approach
            def gender_to_xml(match):
                gid, content = match.group(1), match.group(2)
                return f'<span id="{gid}">{content}</span>'

            def placeholder_to_xml(match):
                pid, content = match.group(1), match.group(2)
                return f'<x id="{pid}.{content}"/>'

            temp = re.sub(r'{([MF]\d+)\.([^{}]+)}', gender_to_xml, temp)
            temp = re.sub(r'{(\d+)\.([^{}]+)}', placeholder_to_xml, temp)

            temp = temp.replace('</span><span', '</span> <span')
            temp = temp.replace('</span><x', '</span> <x')
            temp = temp.replace('/><span', '/> <span')
            temp = temp.replace('/><x', '/> <x')

            response = self.__deepl(temp)
            
            if response.status_code != 200:
                return response

            translated = response.text

            def xml_to_gender(match):
                gid = match.group(1)
                gid = gid.upper()
                content = match.group(2).strip()
                content = re.sub(r'^[\s,.;:!?]+', '', content)
                return f'{{{gid}.{content}}}'

            def xml_to_placeholder(match):
                pid = match.group(1)
                pid = pid.replace('string', 'String')
                return f'{{{pid}}}'

            final = re.sub(
                r'<span\s+id\s*=\s*"([^\"]+)"\s*>(.*?)</span>',
                xml_to_gender,
                translated,
                flags=re.IGNORECASE | re.DOTALL
            )

            final = re.sub(
                r'<x\s+id\s*=\s*"([^\"]+)"\s*/\s*>',
                xml_to_placeholder,
                final,
                flags=re.IGNORECASE
            )
        else:
            # Google and MyMemory: use placeholder extraction approach
            modified_text, placeholders = self.extract_placeholders(temp)
            
            if engine.lower() == 'mymemory':
                response = self.__mymemory(modified_text)
            else:
                response = self.__google(modified_text)
                
            if response.status_code != 200:
                return response
            
            final = self.insert_placeholders(response.text, placeholders)

        final = html.unescape(final)
        return Response(200, final)

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
