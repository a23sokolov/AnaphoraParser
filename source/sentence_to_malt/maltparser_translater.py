import json
import re
from collections import namedtuple
import pymorphy2 # @todo: add in requirements
import sys
import os
sys.path.append('..')
from config import npro_sample


normalize_speech_part = {
    # части речи
    'NOUN': 'S',  # имя существительное	хомяк
    'ADJF': 'A',  # имя прилагательное (полное)	хороший
    'ADJS': 'A',  # имя прилагательное (краткое)	хорош todo: done добавить проставление фичи shrt
    'COMP': 'A', # компаратив	лучше, получше, выше. В СинтагРус такого нету, но есть A + comp(сравнительная форма)todo: done добавить проставление фичи comp
    'VERB': 'V',  # глагол (личная форма)	говорю, говорит, говорил
    'INFN': 'VINF',  # глагол (инфинитив)	говорить
    'PRTF': 'adjp',  # причастие (полное)	прочитавший, прочитанная
    'PRTS': 'adjp',  # причастие (краткое)	прочитана
    'GRND': 'advp',  # деепричастие	прочитав, рассказывая
    'NUMR': 'NUM',  # числительное	три, пятьдесят. NUMR в СинтагРус это будет просто NUM, как и 3, 50 соответсвенно.
    'ADVB': 'ADV',  # наречие
    'NPRO': 'S',  # местоимение-существительное. местоимения ставим для него S - существительное (в спеке syntagRus сказанно, что они игнорят такое)NPRO он, она, кто, который нужно будет переводить в существительные сохраняя все фичи: число, род, падеж
    'PRED': 'ADV',  # предикатив	некогда, в СинтагРус это просто наречие.
    'PREP': 'PR',  # предлог	в
    'CONJ': 'CONJ',  # союз и
    'PRCL': 'PART', # частица	бы, же, лишь проблемы тоже считается в syntagrus частица а в pymorphy2 большее предпочтение наречию
    'INTJ': 'INTJ',  # междометие	ой
}

normalize_features = {
    # одушевленность отображение совпадает мы их не трогаем.
    # 'ОД': 'anim',
    # 'НЕОД': 'inan',
    # род
    'femn': 'f',  # жен
    'masc': 'm',  # муж
    'neut': 'n',  # сред
    'ms-f': 'm',  # общий род (м/ж) пример "сирота" в SyntagRus такого вообще нету.

    # число
    # Некоторые имена существительные употребляются только во множественном/единственном числе; им проставлена пометка Pltm/Sgtm этот параметр игнорим
    # есть ещё Fixd его тоже игнорим.
    'sign': 'sg',  # единственное число
    'plur': 'pl',  # множественное число

    # Падежи
    'nomn': 'nom',  # именительный	Кто? Что?	хомяк ест
    'gent': 'gen',  # родительный	Кого? Чего?	у нас нет хомяка
    'datv': 'dat',  # дательный	Кому? Чему?	сказать хомяку спасибо
    'accs': 'acc',  # винительный	Кого? Что?	хомяк читает книгу
    'ablt': 'ins',  # творительный	Кем? Чем?	зерно съедено хомяком
    'loct': 'prep',  # предложный	О ком? О чём? и т.п.	хомяка несут в корзинке добавочные отображения часть из спецификации, часть из сопоставлений
    'voct': 'nom',  # звательный	Его формы используются при обращении к человеку.	Саш, пойдем в кино.
    'gen2': 'gen', # второй родительный (частичный)	 	ложка сахару (gent - производство сахара); стакан яду (gent - нет яда)
    'acc2': 'acc',  # второй винительный	 	записался в солдаты
    'loc2': 'loc', # второй предложный (местный)	 	я у него в долгу (loct - напоминать о долге); висит в шкафу (loct - монолог о шкафе); весь в снегу (loct - писать о снеге)

    # нестандартные грамемы
    'LATN': '', # Токен состоит из латинских букв (например, “foo-bar” или “Maßstab”)
    'PNCT': '', # Пунктуация (например, , или !? или …)
    'NUMB': 'NUM', # Число (например, “204” или “3.14”)
    'intg': 'NUM', # целое число (например, “204”)
    'real': 'NUM', # вещественное число (например, “3.14”)
    'ROMN': 'NUM', # Римское число (например, XI)
    'UNKN' : '', # Токен не удалось разобрать todo: '' change to fantom. some error.

    # Вид
    'perf' : 'perf', # совершенный вид
    'impf' : 'imperf', # несовершенный вид

    # Переходность игнорится
    # tran переходный
    # intr непереходный

    # Лицо
    '1per': '1p', # 1 лицо (читаю)
    '2per': '2p', # 2 лицо (читаешь)
    '3per': '3p', # 3 лицо (читает)

    # Время
    'pres': 'prs', # настоящее время (читаю)
    'past': 'pst', # прошедшее время (читал)
    'futr': 'npst', # будущее время прочитаю (прочитаю), в синтагрус читаю относится к этой категории, а в pymorphy2 к pres

    # Наклонение
    'indc': 'real', # изъявительное наклонение (прочитаю)
    'impr': 'imp', # повелительное наклонение (прочитай)

    # категория совместимости игнорим
    # incl говорящий включён (идем, идемте)	INvl
    # excl говорящий не включён в действие (иди, идите)	INvl

    # Залог
    'actv': '', # действительный залог, Не проставляется в СинтагРус, мы тоже игнорим
    'pssv': 'pass', # страдательный залог (книга прочитана)

    # степень сравнения
    # сравнительная степени сделана с помощью part of speech COMP.
    'Supr':'supl', #  Превосходная форма есть

}
# todo: add another params in table link https://pymorphy2.readthedocs.io/en/latest/user/grammemes.html#grammeme-docs
# NPRO will be used only for anphora classifier.
word_t = namedtuple('word_t', [ 'lemma', 'pos', 'feat', 'NPRO'])
END_LINE = '\n'

class SentenceParser:
    def __init__(self, input_package='articles', out_package='result'):
        self._morphAnalyzer = pymorphy2.MorphAnalyzer()
        self._input_package = input_package
        self._output_package = os.getcwd() +'/tmp/' + out_package

    def parse(self, opened_file):
        data = json.load(opened_file)

        self._sentences = []
        self._sentence = []

        for article in data:
            self._article_name_short = article.get('title') if article.get('title') else ''
            self._article_date = article.get('date') if article.get('date') else ''
            self._article_time = article.get('time') if article.get('time') else ''
            self._article_url = article.get('url') if article.get('url') else ''

            self._split_article(article)
            self._write_external_file()

    def _split_article(self, article):
        # TODO: simple regex splitter. may be should use nltk splitter.
        sentences = article.get('text')
        sentences = re.split("(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\!)\s", sentences)
        for sentence in sentences:
            sentence_words = sentence.split(' ')
            for word in sentence_words:
                self._sentence.append(self.morph_analyze_malt_tab(word))
            self._sentences.append(self._sentence)
            self._sentence = []

    def morph_analyze_malt_tab(self, word):
        self._word = self._morphAnalyzer.parse(word)
        feat = re.split('[\s,]',str(self._word[0].tag))
        lemma = self._word[0].word
        pos = feat[0]
        features = feat[1:]
        npro = False

        # rule exceptions
        if pos == 'ADJS':
            features.append('shrt')

        # return comp form
        if pos == 'COMP':
            features.append('comp')

        # will be used only for anaphora, else will be ignored.
        if pos =='NPRO' and word in npro_sample:
            npro = True

        # change pos to normalized part of speech
        if pos in normalize_speech_part:
            pos = normalize_speech_part[pos]

        # change features to normal names and ignore another
        normalized_features = []
        for i in range(0, len(features)):
            if features[i] in normalize_features:
                normalized_features.append(normalize_features[features[i]])

        return word_t(lemma=lemma, pos=pos, feat=normalized_features, NPRO=npro)

    def read(self, filename):
        self._file_name = filename

        input_file = open(self._input_package + '/' +filename)
        self.parse(input_file)
        input_file.close()

    # write data in appropriate format
    def write_data(self, sentences, filename, out_package):
        self._sentences = sentences
        self._file_name = filename
        self._output_package = out_package

        self._write_external_file()


    def _write_external_file(self):
        if not os.path.exists(self._output_package):
            os.makedirs(self._output_package)
        out_file = open(self._output_package + '/' + self._file_name, 'w')

        out_sentences = []
        for sentence in self._sentences:
            _out_sentence = []
            for word in sentence:
                _out_sentence.append(self._format_data(word))
            out_sentences.append('\n'.join(_out_sentence))
        out_file.write("\n\n".join(out_sentences))
        out_file.close()

    def _format_data(self, word):
        w = word[0] or 'FANTOM'
        p = '.'.join([word.pos] + word.feat)
        return ('\t'.join([w, p]))

    def read_malttab(self, opened_file):

        _content = opened_file.readlines()
        _sentences = []
        _sentence = []
        position = 0
        start_pos = 0
        for word in _content:
            position += 1
            if '\n' == word:
                sent_obj = ParsedSentence(_sentence, start_pos, position - 1)
                start_pos = position + 1
                _sentences.append(sent_obj)
                _sentence = []
                continue
            res_word = (self._parse_word_malt_tab(word))
            _sentence.append(res_word)
        return _sentences

    def _parse_word_malt_tab(self, word_malt_tab):
        word = {}
        _word = word_malt_tab.strip().split('\t')
        word['word'] = _word[0]
        word['morph'] = _word[1]
        word['id'] = _word[2]
        word['syntax'] = _word[3]
        return word

class ParsedSentence:
    def __init__(self, words, start_pos, end_pos):
        self._words = words
        self._start_pos = start_pos
        self._end_pos = end_pos

    def get_words(self):
        return self._words

    def get_start_pos(self):
        return self._start_pos

    def get_end_pos(self):
        return self._end_pos

    def __repr__(self):
        return '{\n_start_pos=' + str(self._start_pos) + ',\n' + '_end_pos=' + str(self._end_pos) +',\n' + str(self._words) + '\n}'

    def get_word(self, index):
        return self._words[index]