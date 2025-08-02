# -*- coding: utf-8 -*-
import re
import requests
import html
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
        def gender_to_xml(match):
            gid, content = match.group(1), match.group(2)
            return f'<span id="{gid}">{content}</span>'

        def placeholder_to_xml(match):
            pid, content = match.group(1), match.group(2)
            return f'<x id="{pid}.{content}"/>'

        temp = re.sub(r'{([MF]\d+)\.([^{}]+)}', gender_to_xml, text)
        temp = re.sub(r'{(\d+)\.([^{}]+)}', placeholder_to_xml, temp)

        temp = temp.replace('\\ N', '\\N').replace('\\ n', '\\n')
        temp = temp.replace('\\N', '\n').replace('\\n', '\n')

        temp = temp.replace('</span><span', '</span> <span')
        temp = temp.replace('</span><x', '</span> <x')
        temp = temp.replace('/><span', '/> <span')
        temp = temp.replace('/><x', '/> <x')

        if engine.lower() == 'deepl':
            response = self.__deepl(temp)
        else:
            response = self.__google(temp)

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
        
        final = html.unescape(final)

        return Response(200, final)

    @staticmethod
    def __google(text: str) -> Response:
        language = languages.destination
        if language and language.google:
            url = 'http://translate.google.com/m?sl=auto&tl=%s&q=%s'
            link = url % (language.google, urllib.parse.quote(text))
            ua = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/122.0.0.0 Safari/537.36')
            try:
                request = urllib.request.Request(link, headers={'User-Agent': ua})
                data = urllib.request.urlopen(request, timeout=10).read().decode('utf-8')
                expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
                translated = html.unescape(re.findall(expr, data)[0])
                return Response(200, translated)
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
                    headers={'Authorization': f'DeepL-Auth-Key {api_key}'},
                    data=payload,
                    timeout=10
                )
                if resp.status_code == 200:
                    txt = resp.json()['translations'][0]['text']
                    return Response(200, txt)
                elif resp.status_code == 403:
                    return Response(403, interface.text('Errors', 'Invalid API key.'))
                elif resp.status_code == 456:
                    return Response(456, interface.text('Errors', 'Your quota has exceeded!'))
                else:
                    return Response(resp.status_code,
                                    interface.text('Errors', 'Translation failed: {}').format(resp.status_code))
            except Exception as e:
                return Response(500, str(e))
        return Response(404, interface.text('Errors', 'Language code not found!'))

translator = Translator()