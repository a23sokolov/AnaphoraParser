import json
import re
from collections import namedtuple
import pymorphy2

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

word_t = namedtuple('word_t', [ 'lemma', 'pos', 'feat'])
END_LINE = '\n'

class SentenceParser:
    def __init__(self):
        pass

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
            self._write_external_file('test.txt')

    def _split_article(self, article):
        # TODO: simple regex splitter. may be should use nltk splitter.
        sentences = article.get('text')
        sentences = re.split("(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\!)\s", sentences)
        for sentence in sentences:
            sentence_words = sentence.split(' ')
            for word in sentence_words:
                self._sentence.append(self._morph_analyze_malt_tab(word))
            self._sentences.append(self._sentence)
            self._sentence = []


    def _morph_analyze_malt_tab(self, word):
        self._word = self._morphAnalyzer.parse(word)
        feat = re.split('[\s,]',str(self._word[0].tag))
        lemma = self._word[0].word
        pos = feat[0]
        features = feat[1:]

        # rule exceptions
        if pos == 'ADJS':
            features.append('shrt')

        # return comp form
        if pos == 'COMP':
            features.append('comp')

        # change pos to normalized part of speech
        if pos in normalize_speech_part:
            pos = normalize_speech_part[pos]

        # change features to normal names
        for i in range(0, len(features)):
            if features[i] in normalize_features:
                features[i] = normalize_features[features[i]]

        return word_t(lemma=lemma, pos=pos, feat=features)
        # return '\t'.join([lemma, '.'.join([pos] + features)])


    def read(self, filename):
        self._morphAnalyzer = pymorphy2.MorphAnalyzer()

        input_file = open(filename)
        self.parse(input_file)
        input_file.close()

    def _write_external_file(self, file_name):
        out_file = open('result/' + file_name, 'w')

        out_sentences = []
        for sentence in self._sentences:
            _out_sentence = []
            for word in sentence:
                w = word[0] or 'FANTOM'
                p = '.'.join([word.pos] + word.feat)
                _out_sentence.append('\t'.join([w, p]))
            out_sentences.append('\n'.join(_out_sentence))
        out_file.write("\n\n".join(out_sentences))
        out_file.close()




if __name__ == '__main__':
    sentence_parser = SentenceParser()
    sentence_parser.read('articles/test.txt')