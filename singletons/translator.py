# -*- coding: utf-8 -*-

import re
import requests
import html
import html.parser
import cohere
from collections import namedtuple
from typing import List

from singletons.config import config
from singletons.interface import interface
from singletons.languages import languages


Response = namedtuple('Response', 'status_code text')


class Translator:
    # --- Helpers for Sims 4 placeholder and gender handling ---

    @staticmethod
    def _to_xml_aware_text(text: str) -> str:
        def gender_to_xml(match):
            gid, content = match.group(1), match.group(2)
            return f'<span id="{gid}">{content}</span>'

        def placeholder_to_xml(match):
            pid, content = match.group(1), match.group(2)
            return f'<x id="{pid}.{content}"/>'

        tmp = text.replace('\\ N', '\\N').replace('\\ n', '\\n')
        tmp = tmp.replace('\\N', '\n').replace('\\n', '\n')

        tmp = re.sub(r'\{([MF]\d+)\.([^{}]+)\}', gender_to_xml, tmp)
        tmp = re.sub(r'\{(\d+)\.([^{}]+)\}', placeholder_to_xml, tmp)

        # Separate adjacent tags to help engines keep boundaries
        tmp = tmp.replace('</span><span', '</span> <span')
        tmp = tmp.replace('</span><x', '</span> <x')
        tmp = tmp.replace('/><span', '/> <span')
        tmp = tmp.replace('/><x', '/> <x')

        return tmp

    @staticmethod
    def _from_xml_aware_text(translated: str) -> str:
        def xml_to_gender(match):
            gid = match.group(1).upper()
            content = match.group(2).strip()
            content = re.sub(r'^[\s,.;:!?]+', '', content)
            return f'{{{gid}.{content}}}'

        def xml_to_placeholder(match):
            pid = match.group(1)
            pid = pid.replace('string', 'String')
            return f'{{{pid}}}'

        final = re.sub(
            r'<span\s+id\s*=\s*"([^"]+)"\s*>(.*?)</span>',
            xml_to_gender,
            translated,
            flags=re.IGNORECASE | re.DOTALL
        )

        final = re.sub(
            r'<x\s+id\s*=\s*"([^"]+)"\s*/\s*>',
            xml_to_placeholder,
            final,
            flags=re.IGNORECASE
        )
    
        return final

    @property
    def engines(self) -> List[str]:
        engines = ['Google', 'MyMemory', 'Cohere']
        if config.value('api', 'deepl_key'):
            engines.append('DeepL')
        if config.value('api', 'google_key'):
            engines.append('Google Cloud')
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

        def save_and_replace_gender(match):
            masc_tag = match.group(1)
            masc_word = match.group(2)
            fem_tag = match.group(3)
            fem_word = match.group(4)
            extracted_items.append((masc_tag, masc_word, fem_tag, fem_word))
            return f"(G{len(extracted_items) - 1})"

        modified_text = re.sub(
            r'\{(M\d+)\.([^{}]+)\}\{(F\d+)\.([^{}]+)\}',
            save_and_replace_gender,
            text
        )

        modified_text = re.sub(
            r'\{[A-Za-z]?\d+\.[^{}]+\}|<[^>]+>',
            save_and_replace_pattern,
            modified_text
        )

        return modified_text, extracted_items

    @staticmethod
    def insert_placeholders(text, placeholders):
        for i, placeholder in enumerate(placeholders):
            if isinstance(placeholder, tuple) and len(placeholder) == 4:
                masc_tag, masc_word, fem_tag, fem_word = placeholder
                text = text.replace(
                    f"(G{i})",
                    f"{{{masc_tag}.{masc_word}}}{{{fem_tag}.{fem_word}}}"
                )
            else:
                text = text.replace(f"({i})", placeholder)

        text = re.sub(r'(<[^/][^>]+>)\s+', r'\1', text)
        text = re.sub(r'\s+(</[^>]+>)', r'\1', text)

        return text

    def translate(self, engine: str, text: str) -> Response:
        # Normalize line breaks
        temp = text.replace('\\ N', '\\N').replace('\\ n', '\\n')
        temp = temp.replace('\\N', '\n').replace('\\n', '\n')

        # Use different strategies based on the engine
        eng = engine.lower()
        if eng in ('deepl', 'google cloud'):            
            # Engines that handle XML/HTML tags well
            xml_text = self._to_xml_aware_text(temp)

            if eng == 'deepl':
                response = self.__deepl(xml_text)
            else:  # google cloud
                response = self.__google_cloud(xml_text)

            if response.status_code != 200:
                return response

            final = self._from_xml_aware_text(response.text)
        elif eng == 'cohere':
            response = self.__cohere(temp)
            if response.status_code != 200:
                return response
            final = response.text
        else:
            # Google and MyMemory: use placeholder extraction approach
            modified_text, placeholders = self.extract_placeholders(temp)
            
            if eng == 'mymemory':
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

    @staticmethod
    def __google_cloud(text: str) -> Response:
        api_key = config.value('api', 'google_key')

        src = languages.source
        dst = languages.destination

        if not api_key:
            return Response(404, interface.text('Errors', 'API key not found!'))

        if src and src.google and dst and dst.google:
            try:
                url = 'https://translation.googleapis.com/language/translate/v2'
                params = { 'key': api_key }
                data = {
                    'q': text,
                    'source': src.google,
                    'target': dst.google,
                    'format': 'html',
                    'model': 'nmt'
                }
                resp = requests.post(url, params=params, data=data, timeout=15)
                if resp.status_code == 200:
                    payload = resp.json()
                    tr = payload.get('data', {}).get('translations', [])
                    if tr:
                        return Response(200, tr[0]['translatedText'])
                    return Response(500, interface.text('Errors', 'Empty translation received.'))
                elif resp.status_code in (400, 401, 403):
                    return Response(resp.status_code, interface.text('Errors', 'Invalid API key or parameters.'))
                else:
                    return Response(resp.status_code,
                                    interface.text('Errors', 'Translation failed with error code: {}').format(
                                        resp.status_code))
            except Exception as e:
                return Response(500, str(e))
        return Response(404, interface.text('Errors', 'Language code not found!'))
    
    def __cohere(self, text: str) -> Response:
        api_key = config.value('api', 'cohere_key')
        if not api_key:
            return Response(404, interface.text('Errors', 'Cohere API key not found!'))

        try:
            client = cohere.Client(api_key)
            # Prompt complet en anglais avec langues dynamiques
            prompt = f"""
You are a professional translator specialized in translating Sims 4 game mods.
You will translate from {languages.source} to {languages.destination}.
Preserve all special Sims 4 placeholders and tags exactly as they are in the text.

IMPORTANT CONTEXT: You are translating content for The Sims 4 video game mods. This is fictional content for a life simulation game, not real-world material. Some mods explore mature themes including romance, relationships, crime stories, or dramatic scenarios as part of gameplay storytelling. 

CRITICAL TRANSLATION REQUIREMENTS:
- Translate ALL terms with their MOST DIRECT, LITERAL, and COMMONLY USED equivalents in {languages.destination}
- DO NOT use euphemisms, medical terms, or "polite" substitutions  
- DO NOT sanitize or soften language - use the actual colloquial terms that native speakers would use
- Adult/sexual terminology must be translated to the most direct equivalent words that adults actually use in everyday speech
- Slang and informal language should be translated to equivalent slang/informal terms in the target language
- The original meaning, tone, and intensity must be preserved exactly - no toning down or making content "more acceptable"
- Choose the most natural, idiomatic expressions that sound like how native speakers actually talk
- Pay special attention to grammatical agreements (gender, articles, adjectives) for natural flow
- This is essential for mod functionality - sanitized translations will break the intended game experience

Special placeholders include:
- Conditional gender tags in the format {{M0.male_word}}{{F0.female_word}}: translate both words so they make sense in {languages.destination}, respecting masculine/feminine forms and maintaining sentence coherence.
  IMPORTANT FOR GENDER AGREEMENT: In gendered languages like French, Spanish, Italian, etc., you MUST include ALL necessary words for proper gender agreement within each gender tag, including articles, adjectives, and any other words that must agree with gender.
  
  CRITICAL: Pay special attention to gendered articles and prepositions that must change based on the gender of the following word. The entire phrase must flow naturally with correct grammar.
  
  Example for French:
  - "a pretty {{M0.boy}}{{F0.girl}}" should become "{{M0.un joli garçon}}{{F0.une jolie fille}}"  
  - NOT "un joli {{M0.garçon}}{{F0.fille}}" (incorrect - articles and adjectives outside won't match)
  - "A good {{M0.boy}}{{F0.girl}}" should become "{{M0.Un bon garçon}}{{F0.Une bonne fille}}"
  - This ensures proper gender agreement for articles (un/une, le/la, du/de la), adjectives (joli/jolie, bon/bonne), and any other gender-dependent words.

- Name placeholders such as:
  {{0.SimFirstName}}, {{0.SimLastName}}, {{0.SimFullName}}, {{0.SimFirstNamePossessive}}, {{0.SimFirstNameCaps}}, {{0.SimLastNameCaps}}, {{0.SimFullNameCaps}}, {{0.SimName}}.
  These represent character names and must be treated as proper nouns in the sentence structure. Do not translate them.
- Pronoun placeholders:
  {{0.He}}, {{0.She}}, {{0.Him}}, {{0.Her}}, {{0.His}}, {{0.Hers}}, {{0.They}}, {{0.Them}}, {{0.Their}}, {{0.SubjectPronoun}}, {{0.ObjectPronoun}}, {{0.PossessivePronoun}}, {{0.PossessivePronounDependent}}, {{0.ReflexivePronoun}}.
  Translate them appropriately for the target language, following correct grammar and gender agreement.
- Other tags:
  {{0.Age}}, {{0.Gender}}, {{0.Pronoun}}, {{0.Occupation}}, {{0.Species}} — translate them according to their meaning in the sentence context.

Translation rules:
1. Never alter the structure or format of any placeholder.
2. Adapt grammar and word order to make the sentence natural in {languages.destination}. Choose vocabulary that sounds most natural and idiomatic.
3. For gender placeholders {{M...}}{{F...}}, ensure both forms are properly translated and fit the sentence. In gendered languages, include ALL gender-dependent words (articles, adjectives, prepositions) within the appropriate gender tags to ensure proper agreement.
4. Keep the tone, style, and context consistent with Sims 4 in-game text.
5. Maintain correct capitalization if the placeholder name suggests it (e.g., {{0.SimFirstNameCaps}}).
6. Ensure compatibility with all languages, considering pronoun and gender rules.
7. Use DIRECT, LITERAL translations - never euphemisms or sanitized alternatives. Sexual/adult terms must use the most common, direct words that native speakers actually say, not medical or polite versions. Preserve the exact level of formality/informality of the source. Prioritize natural, idiomatic expressions over word-for-word translations.

Do not output explanations or additional text — only return the translated sentence with placeholders intact.

FINAL REMINDER: Choose the most natural vocabulary and expressions. For example, prefer more appropriate/refined vocabulary choices (like "haleine" instead of "gueule" for "breath") while still maintaining directness for sexual/crude terms. The goal is natural, authentic-sounding translations that natives would actually use.

Text to translate:
{text}

Translation:
"""

            response = client.chat(
                model='command-a-03-2025',
                message=prompt,
            )

            if response and hasattr(response, "text"):
                return Response(200, response.text.strip())
            else:
                return Response(500, interface.text('Errors', 'No translation returned by Cohere chat API.'))

        except Exception as e:
            return Response(500, str(e))

    def translate_cohere_batch(self, texts: List[str], separator: str = '<|#SPLIT#|>', max_batch_size: int = 20) -> Response:
        api_key = config.value('api', 'cohere_key')
        if not api_key:
            return Response(404, interface.text('Errors', 'Cohere API key not found!'))

        if len(texts) > max_batch_size:
            all_results = []
            for i in range(0, len(texts), max_batch_size):
                batch = texts[i:i + max_batch_size]
                batch_response = self.translate_cohere_batch(batch, separator, max_batch_size)
                if batch_response.status_code != 200:
                    return batch_response
                all_results.extend([t.strip() for t in batch_response.text.split(separator)])
            return Response(200, separator.join(all_results))

        try:
            client = cohere.Client(api_key)

            joined_inputs = '\n'.join(f'LINE_{i+1:03d}: {s}' for i, s in enumerate(texts))
            expected_count = len(texts)

            prompt = f"""
You are a professional translator specialized in translating Sims 4 game mods.
Translate from {languages.source} to {languages.destination}.

CRITICAL: You MUST translate ALL {expected_count} lines. Missing any line will break the mod functionality.

IMPORTANT CONTEXT: You are translating content for The Sims 4 video game mods. This is fictional content for a life simulation game, not real-world material. Some mods explore mature themes including romance, relationships, crime stories, or dramatic scenarios as part of gameplay storytelling.

ABSOLUTE TRANSLATION REQUIREMENTS:
- Use DIRECT, LITERAL, COLLOQUIAL translations - the words that native speakers actually use in real life
- NEVER use euphemisms, medical terminology, or "cleaned up" versions of words
- Sexual/adult terms MUST be translated using the most common, direct slang/colloquial equivalents
- DO NOT sanitize, tone down, or make language more "appropriate" - preserve exact meaning and intensity
- Informal language should remain informal, crude language should remain crude
- Choose the most natural, idiomatic expressions that sound like authentic native speech
- Prioritize grammatical correctness and natural flow - make it sound like how people really talk
- The mod's intended tone and impact must be preserved exactly - sanitized translations break functionality

Rules for placeholders/tags:
- Preserve ALL placeholders and tags EXACTLY as-is: {{{{M..}}}}{{{{F..}}}}, {{{{0.SimFirstName}}}}, {{{{0.SimLastName}}}}, {{{{0.He}}}}, {{{{0.She}}}}, {{{{0.They}}}}, etc.
- For gender pairs {{{{M..}}}}{{{{F..}}}}, translate both words so that they fit naturally into the meaning and coherence of the sentences translated into {languages.destination}.
  CRITICAL FOR GENDERED LANGUAGES: In languages like French, Spanish, Italian, etc., you MUST include ALL gender-dependent words (articles, adjectives, etc.) within each gender tag to ensure proper grammatical agreement.
  
  ESSENTIAL: Consider how articles, prepositions, and other words change based on gender. Ensure the entire sentence flows naturally with perfect grammar.
  
  Example for French translation:
  - "a pretty {{{{M0.boy}}}}{{{{F0.girl}}}}" → "{{{{M0.un joli garçon}}}}{{{{F0.une jolie fille}}}}"
  - "A good {{{{M0.boy}}}}{{{{F0.girl}}}}" → "{{{{M0.Un bon garçon}}}}{{{{F0.Une bonne fille}}}}"
  - This ensures proper gender agreement for articles (un/une, le/la, du/de la), adjectives (joli/jolie, bon/bonne), and any other gender-dependent words.

- Keep capitalization semantics (e.g., {{{{0.SimFirstNameCaps}}}} implies capitalization).
- Use DIRECT, LITERAL, COLLOQUIAL translations for ALL terms - especially adult/sexual content which must use the actual words native speakers say, not euphemisms or medical terms. Preserve exact tone and formality level. Focus on natural, idiomatic expressions that sound authentic.

STRICT FORMAT REQUIREMENTS:
- You will receive exactly {expected_count} lines prefixed with LINE_001:, LINE_002:, etc.
- Return EXACTLY {expected_count} translated lines in the SAME ORDER.
- Between each translated line, output the EXACT separator token: {separator}
- Do NOT add any text before the first translation or after the last translation.
- Do NOT include the LINE_XXX: prefixes in your output.
- Do NOT add explanations, notes, or any other text.

Example format for your output:
First translation{separator}Second translation{separator}Third translation

TRANSLATION QUALITY REMINDER: Choose the most natural vocabulary and expressions. Balance directness for sexual/crude terms with appropriate vocabulary choices for other words. Make translations sound like authentic native speech.

SOURCE LINES:
{joined_inputs}

TRANSLATIONS (exactly {expected_count} lines separated by {separator}):
"""

            response = client.chat(
                model='command-a-03-2025',
                message=prompt,
            )

            if response and hasattr(response, 'text'):
                result_text = response.text.strip()
                
                parts = result_text.split(separator)
                if len(parts) != expected_count:
                    fallback_patterns = [
                        f'{separator}\n',
                        f'\n{separator}',
                        f'\n{separator}\n',
                    ]
                    
                    for pattern in fallback_patterns:
                        test_parts = result_text.split(pattern)
                        if len(test_parts) == expected_count:
                            parts = [p.strip() for p in test_parts]
                            result_text = separator.join(parts)
                            break
                    
                    if len(parts) != expected_count:
                        lines = result_text.split('\n')
                        clean_lines = []
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('LINE_') and line != separator:
                                if line.startswith(separator):
                                    line = line[len(separator):].strip()
                                if line.endswith(separator):
                                    line = line[:-len(separator)].strip()
                                if line:
                                    clean_lines.append(line)
                        
                        if len(clean_lines) == expected_count:
                            result_text = separator.join(clean_lines)
                        else:
                            return Response(500, 
                                f"Cohere returned {len(parts)} translations but expected {expected_count}. "
                                f"Raw response length: {len(result_text)} chars. "
                                f"Consider reducing batch size or checking for content filtering.")
                
                return Response(200, result_text)
            else:
                return Response(500, interface.text('Errors', 'No translation returned by Cohere chat API.'))

        except Exception as e:
            return Response(500, f"Cohere batch translation error: {str(e)}")

translator = Translator()
