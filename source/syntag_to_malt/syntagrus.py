# -*- coding: utf-8 -*-
import xml.parsers.expat
from collections import namedtuple
# в скобочках указываются параметры которые определены по определению для русского языка.
# * те параметры которые по каким либо причинам не являются важными хотя они есть в SyntagRus.
# ** те параметры которые просто не учитываются в SyntagRus, но они есть pymorphy2.
selected_feat = {'m', 'f', 'n', # род(муж, жен, средний, общий**)
				 'sg', 'pl', # число(ед, мн)
				 '1p', '2p', '3p', # лицо(1-ое, 2-ое, 3-ье)
				 'nom', 'gen', 'gen2', 'dat', 'acc', 'ins', 'prep', 'loc', # падежи. gen2 партитивный падеж, loc - местный падеж более подробно pamjatka.
				 'real', 'imp', # наклонение (изъяв, пов)
				 'pass', # залог (страдательный)
				 'comp', # степень(сравнительная, превосходная) сравнения только сравнительная
				 'shrt' # краткость (прилагательные, причастия)
				 #21
				 }

word_t = namedtuple('word_t', ['lemma', 'pos', 'feat', 'id', 'dom', 'link'])
link_ru_en = {
	'предик': 'subj',
	'1-компл': 'obj',
	'2-компл': 'obj',
	'3-компл': 'obj',
	'4-компл': 'obj',
	'5-компл': 'obj',
	'опред': 'amod',
	'предл': 'prep',
	'обст': 'pobj',
}
# общие моменты
# # Although head and deprel are optional, they must either both be included or both be omitted. (Normally, all four columns are present in the input when training the parser and in the output when parsing,
# # while only form and postag are present in the input when parsing.) Please note also that the id attribute is not represented explicitly at all. Words in a sentence are separated by one newline; sentences
# # are separated by one additional newline.
# для причастия, деепричастий, инфинитива вытаскиваем часть речи из фич и ставим в postag и вытаскиваем из фич. Синтагрус для них выставляет V
feat_ru_en = {
	'ЖЕН': 'f',
	'МУЖ': 'm',
	'СРЕД': 'n',

	'ЕД': 'sg',
	'МН': 'pl',

	'1-Л': '1p',
	'2-Л': '2p',
	'3-Л': '3p',

	'ИМ': 'nom',
	'РОД': 'gen',
	'ДАТ': 'dat',
	'ВИН': 'acc',
	'ТВОР': 'ins',
	'ПР': 'prep',
	'ПАРТ': 'gen2',
	'МЕСТН': 'loc',

	'ИЗЪЯВ': 'real',
	'ПОВ': 'imp',

	'СТРАД': 'pass',

	'СРАВ': 'comp',
	'ПРЕВ': 'supl', #*

	'КР': 'shrt',

	# ignored
	'НЕСОВ': 'imperf', #*
	'СОВ': 'perf', #*
	'СЛ': 'compl', #*
	'СМЯГ': 'soft', #*
	'ОД': 'anim', #*
	'НЕОД': 'inan', #*
	'ИНФ': 'inf', #* part of speech
	'ПРИЧ': 'adjp', #* part of speech
	'ДЕЕПР': 'advp', #* part of speech
	'ПРОШ': 'pst', #*
	'НЕПРОШ': 'npst', #*
	'НАСТ': 'prs', #*
}

class Reader:
	def __init__(self):
		self._parser = xml.parsers.expat.ParserCreate()
		self._parser.StartElementHandler = self.start_element
		self._parser.EndElementHandler = self.end_element
		self._parser.CharacterDataHandler = self.char_data

	
	def start_element(self, name, attr):
		if name == 'W':
			features = attr['FEAT'].split(' ') if 'FEAT' in attr else ['UNK']
			for i in range(0, len(features)):
				if features[i] in feat_ru_en:
					features[i] = feat_ru_en[features[i]]
					
			lemma = lemma=attr['LEMMA'].lower() if 'LEMMA' in attr else ''
			link = attr['LINK'] if 'LINK' in attr else None
#			if link in link_ru_en:
#				link = link_ru_en[link]
				
			dom = int(attr['DOM']) if attr['DOM'] != '_root' else 0
			pos = features[0]
			feat = set(features[1:])

			if 'adjp' in feat:
				pos = 'VADJ'
				feat -= {'adjp'}
				
			if 'advp' in feat:
				pos = 'VADV'
				feat -= {'advp'}
			
			if 'inf' in feat:
				pos = 'VINF'
				feat -= {'inf'}
			
			self._info = word_t(lemma=lemma, pos=pos, feat=feat, id=int(attr['ID']), dom=dom, link=link)
			self._cdata = ''
	
	def end_element(self, name):
		if name == 'S':
			self._sentences.append(self._sentence)
			self._sentence = []
		elif name == 'W':
			self._sentence.append((self._cdata, self._info))
			self._cdata = ''
	
	def char_data(self, content):
		self._cdata += content
		
	def read(self, filename):
		f = open(filename, encoding='utf-8')
		content = f.read()
		f.close()
		# content = content.replace('encoding="windows-1251"', 'encoding="utf-8"')
		
		self._sentences = []
		self._sentence = []
		self._cdata = ''
		self._info = ''
		
		self._parser.Parse(content)		
		
		return self._sentences