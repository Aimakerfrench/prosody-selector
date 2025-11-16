# core.py

import re
import unicodedata
import sqlite3
from collections import defaultdict

class RuleEngine:
    def __init__(self, replacements):
        self.replacements = replacements

    def remove_alif_after_waw_jamaa(self, line):
        after_alif = r'(?=[\s\.,*:؛!\?()\[\]\"\'«»…]|$)'
        pattern1 = re.compile(r'([\u0621-\u064A][\u064F])\u0648(?![\u064B-\u0652])\u0627' + after_alif)
        pattern2 = re.compile(r'([\u0621-\u064A][\u064E])\u0648\u0652\u0627' + after_alif)
        line = pattern1.sub(r'\1و', line)
        line = pattern2.sub(r'\1وْ', line)
        return line

    def process_final_ha_and_mim(self, line):
        words = line.split()
        processed = []
        for i, w in enumerate(words):
            word, suffix = w, ''
            # فصل العلامات عن نهاية الكلمة
            while word and word[-1] in '*،.:؛!?()[]{}«»"\'…':
                suffix = word[-1] + suffix
                word = word[:-1]
            # تحديد الحرف القاعدي السابق ودوائره
            prevent = False
            j = len(word) - 1
            while j >= 0 and unicodedata.combining(word[j]):
                j -= 1
            k = j - 1
            while k >= 0 and unicodedata.combining(word[k]):
                k -= 1
            prev_base = word[k] if k >= 0 else ''
            prev_diacs = [c for c in word[k+1:j] if unicodedata.combining(c)]
            # شروط منع الإضافة
            if 'ْ' in prev_diacs or (prev_base in 'اوي' and not prev_diacs):
                prevent = True
            if i+1 < len(words) and words[i+1].startswith(('ال','الْ')):
                prevent = True
            # إضافة السكون المناسب
            if not prevent:
                if word.endswith('هِ'):
                    word += 'يْ'
                elif word.endswith('هُ'):
                    word += 'وْ'
                elif word.endswith('مُ'):
                    word += 'وْ'
            processed.append(word + suffix)
        return ' '.join(processed)

    def reorder_shadda_and_haraka(self, line):
        result, i, n = '', 0, len(line)
        while i < n:
            ch = line[i]
            if unicodedata.combining(ch):
                result += ch; i += 1; continue
            base = ch; i += 1
            diacritics = ''
            while i < n and unicodedata.combining(line[i]):
                diacritics += line[i]; i += 1
            if diacritics:
                # الشدة أولاً ثم باقي الحركات
                sorted_diacs = ''.join(sorted(diacritics, key=lambda x: 0 if x=='ّ' else 1))
                result += base + sorted_diacs
            else:
                result += base
        return result

    def replace_specific_words(self, line):
        line = unicodedata.normalize('NFC', line)
        for orig in sorted(self.replacements.keys(), key=len, reverse=True):
            if orig in line:
                line = line.replace(orig, self.replacements[orig])
        # معالجة خاصة للحرف 'آ'
        return line.replace('آ', 'ءَاْ')

    def process_prefix_with_lunar_shamsi(self, line):
        lunar  = 'آإأئءؤبجحخعغفقكمهوي'
        shamsi = 'تثدذرزسشصضطظلن'
        prefixes = ["كَال","فَال","بِال","وَال","وَبِال","فَبِال","أَبِال"]
        words = line.split()
        for i, w in enumerate(words):
            for p in prefixes:
                if w.startswith(p) and len(w)>len(p):
                    har = w[1] if w[1] in 'َُِ' else ''
                    c = w[len(p)]
                    if c in lunar:
                        words[i] = p[0]+har+'لْ'+w[len(p):]
                    elif c in shamsi:
                        words[i] = p[0]+har+w[len(p):]
        return ' '.join(words)

    def process_poetry_line(self, line):
        # حذف ألف الوصل في بداية الشطر
        line = re.sub(r'^(ا)(?!ل)', '', line)
        return ' '.join(re.sub(r'^ا(?!ل)', '', w) for w in line.split())

    def apply_lam_shamsi_lunar_rules(self, line):
        lunar  = 'آإأئءؤبجحخعغفقكمهوي'
        shamsi = 'تثدذرزسشصضطظلن'
        words = line.split()
        for i, w in enumerate(words):
            if w.startswith('ال') and len(w)>2:
                c = w[2]
                words[i] = ('لْ'+w[2:]) if c in lunar else (w[2:] if c in shamsi else w)
        return ' '.join(words)

    def process_tanween(self, line):
        for old, new in {'اً':'ً','ًا':'ً','ىً':'ً','ًى':'ً'}.items():
            line = line.replace(old,new)
        return line

    def convert_tanween_to_haraka_with_n(self, line):
        for old, new in {'ٌ':'ُنْ','ٍ':'ِنْ','ً':'َنْ'}.items():
            line = line.replace(old,new)
        return line

    def convert_ta_marbuta_to_ta(self, line):
        return line.replace('ة','ت')

    def split_shadda_and_repeat(self, line):
        patterns = [
            (r"([ء-ي])\u0651([َُِ])", r"\1ْ\1\2"),
            (r"([ء-ي])([َُِ])\u0651", r"\1ْ\1\2"),
            (r"([ء-ي])\u0651([اوي])",   r"\1ْ\1\2"),
            (r"([ء-ي])\u0651([ًٌٍ])",  r"\1ْ\1\2"),
            (r"([ء-ي])([ًٌٍ])\u0651",  r"\1ْ\1\2"),
            (r"([ء-ي])\u0651",         r"\1ْ\1َ"),
        ]
        for pat, rep in patterns:
            line = re.sub(pat, rep, line)
        return line

    def apply_new_rules(self, line):
        f, d, k, s = 'َ','ُ','ِ','ْ'
        rules = [
            (r'([^ً-ْ\s])َ([اى])(?![ً-ْ])', lambda m: m.group(1)+f+('ا'+s if m.group(2)=='ا' else 'ى'+s)),
            (r'([^ً-ْ\s])ُو(?![ً-ْ])',       lambda m: m.group(1)+d+'و'+s),
            (r'([^ً-ْ\s])ِي(?![ً-ْ])',       lambda m: m.group(1)+k+'ي'+s),
        ]
        for pat, fn in rules:
            line = re.sub(pat, fn, line)
        return line

    def modify_last_character(self, line):
        f, d, k, s = 'َ','ُ','ِ','ْ'
        pat = re.compile(r'([ء-ي])(['+f+d+k+r'])(?=[؟!.,;…]*$)')
        def rep(m):
            b, dia = m.groups()
            if dia==d: return b+dia+'و'+s
            if dia==k: return b+dia+'ي'+s
            if dia==f: return b+dia+'ا'+s
            return m.group(0)
        return pat.sub(rep, line)

    def remove_first_sukun_if_two_sukuns_in_row(self, line):
        pat = re.compile(r'([ء-ي]ْ)(\s*)([ء-ي]ْ)')
        while True:
            new = pat.sub(r'\2\3', line)
            if new==line: break
            line = new
        return line

    def finalize_lal_and_lil(self, line):
        line = re.sub(r'ا(?=ل\u0652ل\u064E)', '', line)
        line = re.sub(r'(لِ)ل(?![\u064B-\u0652])', r'\1', line)
        return line

    def add_initial_alif_to_double(self, line):
        m = re.match(r'^(\s*)([ء-ي])\u0652\2[\u064B-\u0650]', line)
        if m:
            spaces = m.group(1)
            return spaces + 'أَ' + line[len(spaces):]
        return line

    def add_initial_alif_to_sukun(self, line):
        m = re.match(r'^(\s*)([ء-ي]\u0652)', line)
        if m:
            spaces = m.group(1)
            return spaces + 'أَ' + line[len(spaces):]
        return line

    def remove_letter_and_sukun_between_words(self, line):
        return re.sub(r'([ء-ي]\u0652)(?=\s+[ء-ي]\u0652)', '', line)

    def process_final_ha(self, line):
        ws = line.split()
        for i, w in enumerate(ws):
            if w.endswith('هِ') and (len(w)<3 or w[-3]!='ْ'):
                ws[i] += 'يْ'
            elif w.endswith('هُ') and (len(w)<3 or w[-3]!='ْ'):
                ws[i] += 'وْ'
        return ' '.join(ws)

    def process_double_n_clone_with_aleph(self, line: str) -> str:
        out = []
        for token in line.split():
            core, suffix = token, ''
            while core and core[-1] in '،.:؛!?()[]{}*«»"\'…':
                suffix = core[-1] + suffix
                core = core[:-1]
            clusters = []
            i = 0
            while i < len(core):
                base = core[i]; i += 1
                combs = ''
                while i < len(core) and unicodedata.combining(core[i]):
                    combs += core[i]; i += 1
                clusters.append(base + combs)
            # إذا كانت نهاية العنقود نون مشددة وعليها سكون ثم ألف
            if (len(clusters) >= 2 
                and clusters[-2].startswith('ن') 
                and 'ّ' in clusters[-2] 
                and 'ْ' in clusters[-2]
                and clusters[-1] == 'ا'):
                clusters.pop()              # حذف الألف
                clusters[-1] = 'ن' + '\u0652'  # جعل العنقود الأخير نون ساكنة
                # إضافة نون ساكنة من العنقود السابق قبل الأخير
                prev = clusters[-2][0]
                clusters.insert(-2, prev + '\u0652')
            out.append(''.join(clusters) + suffix)
        return ' '.join(out)

    def process_double_n_clone(self, line: str) -> str:
        out = []
        for token in line.split():
            core, suffix = token, ''
            while core and core[-1] in '،.:؛!?()[]{}*«»"\'…':
                suffix = core[-1] + suffix
                core = core[:-1]
            clusters = []
            i = 0
            while i < len(core):
                base = core[i]; i += 1
                combs = ''
                while i < len(core) and unicodedata.combining(core[i]):
                    combs += core[i]; i += 1
                clusters.append(base + combs)
            # إذا كانت نهاية العنقود نون مشددة وعليها سكون
            if clusters and clusters[-1].startswith('ن') and 'ّ' in clusters[-1] and 'ْ' in clusters[-1]:
                clusters[-1] = 'ن' + '\u0652'
                if len(clusters) >= 2:
                    prev_base = clusters[-2][0]
                    clusters.insert(-2, prev_base + '\u0652')
            out.append(''.join(clusters) + suffix)
        return ' '.join(out)

    def apply_all(self, line):
        funcs = [
            self.process_final_ha_and_mim,
            self.reorder_shadda_and_haraka,
            self.replace_specific_words,
            self.process_prefix_with_lunar_shamsi,
            self.process_poetry_line,
            self.apply_lam_shamsi_lunar_rules,
            self.process_tanween,
            self.convert_tanween_to_haraka_with_n,
            self.convert_ta_marbuta_to_ta,
            self.split_shadda_and_repeat,
            self.apply_new_rules,
            self.modify_last_character,
            self.remove_first_sukun_if_two_sukuns_in_row,
            self.finalize_lal_and_lil,
            self.add_initial_alif_to_double,
            self.process_final_ha,
            self.remove_letter_and_sukun_between_words,
            self.add_initial_alif_to_sukun,
            self.process_double_n_clone,
            self.process_double_n_clone_with_aleph,
            self.remove_alif_after_waw_jamaa,
        ]
        for fn in funcs:
            line = fn(line)
        return line


class TextCleaner:
    def __init__(self):
        self.punc = re.compile(r'[:()\-_؟!\."“”\[\]،؛*،،«»]+')
        self.tatw = '\u0640'

    def clean(self, text):
        t = self.punc.sub('', text).replace(self.tatw, '')
        return re.sub(r'\s+', ' ', t).strip()


class UnitExtractor:
    def __init__(self):
        self.harakat = {'\u064E','\u064F','\u0650','\u064B','\u064C','\u064D','\u0651'}
        self.sukoon  = '\u0652'

    def extract(self, text):
        units, i = [], 0
        while i < len(text):
            c = text[i]
            if unicodedata.combining(c):
                i += 1; continue
            u = c; i += 1
            while i < len(text) and unicodedata.combining(text[i]):
                u += text[i]; i += 1
            if self.sukoon in u:
                units.append('sukoon')
            elif any(h in u for h in self.harakat):
                units.append('haraka')
            else:
                units.append('no_diacritic')
        return tuple(units)


class LineSplitter:
    def __init__(self, delim='***'):
        self.delim = delim

    def split(self, line):
        return [p.strip() for p in line.split(self.delim)]


class Processor:
    def __init__(self, cleaner, extractor, splitter):
        self.cleaner   = cleaner
        self.extractor = extractor
        self.splitter  = splitter

    def process_line(self, line):
        parts = self.splitter.split(line)
        return tuple(
            self.extractor.extract(
                self.cleaner.clean(p).replace(' ', '')
            )
            for p in parts
        )


class MeterIndexer:
    def __init__(self, db_path, processor):
        self.full_line_index = defaultdict(list)
        self.db_path         = db_path
        self.processor       = processor
        self._index()

    def _index(self):
        conn = sqlite3.connect(self.db_path)
        for name, line in conn.execute('SELECT bahr_name, line_text FROM meters'):
            units = self.processor.process_line(line.strip())
            if len(units) == 2:
                self.full_line_index[units].append((name, line))
        conn.close()


class PoetryMatcher:
    def __init__(self, db_path, reps):
        self.rule      = RuleEngine(reps)
        self.cleaner   = TextCleaner()
        self.extractor = UnitExtractor()
        self.splitter  = LineSplitter()
        self.processor = Processor(self.cleaner, self.extractor, self.splitter)
        self.indexer   = MeterIndexer(db_path, self.processor)

    def process_poem(self, inp):
        # تطبيق القواعد على الشطرين
        if '***' in inp:
            a, b = inp.split('***', 1)
            pr = f"{self.rule.apply_all(a.strip())} *** {self.rule.apply_all(b.strip())}"
        else:
            pr = self.rule.apply_all(inp)
        u = self.processor.process_line(pr)
        full = {}
        if len(u) == 2 and u in self.indexer.full_line_index:
            for sea, line in self.indexer.full_line_index[u]:
                full[sea] = line
        return pr, full
