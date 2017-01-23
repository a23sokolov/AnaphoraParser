import xml.parsers.expat
from collections import namedtuple

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

feat_ru_en = {
	'ЕД': 'sg',
	'МН': 'pl',
	'ЖЕН': 'f',
	'МУЖ': 'm',
	'СРЕД': 'n',
	'ИМ': 'nom',
	'РОД': 'gen',
	'ДАТ': 'dat',
	'ВИН': 'acc',
	'ТВОР': 'ins',
	'ПР': 'prep',
	'ПАРТ': 'gen2',
	'МЕСТН': 'loc',
	'ОД': 'anim',
	'НЕОД': 'inan',
	'ИНФ': 'inf',
	'ПРИЧ': 'adjp',
	'ДЕЕПР': 'advp',
	'ПРОШ': 'pst',
	'НЕПРОШ': 'npst',
	'НАСТ': 'prs',
	'1-Л': '1p',
	'2-Л': '2p',
	'3-Л': '3p',
	'ИЗЪЯВ': 'real',
	'ПОВ': 'imp',
	'КР': 'shrt',
	'НЕСОВ': 'imperf',
	'СОВ': 'perf',
	'СТРАД': 'pass',
	'СЛ': 'compl',
	'СМЯГ': 'soft',
	'СРАВ': 'comp',
	'ПРЕВ': 'supl',
}

{
	'огранич': '',      
	'квазиагент': '',       
	'сочин': '',      
	'соч-союзн': '',      
	'атриб': '',      
	'аппоз': '',      
	'подч-союзн': '',      
	'вводн': '',      
	'сент-соч': '',      
	'количест': '',      
	'разъяснит': '',       
	'присвяз': '',      
	'релят': '',      
	'сравн-союзн': '',      
	'примыкат': '',      
	'сравнит': '',      
	'соотнос': '',      
	'эксплет': '',      
	'аналит': '',      
	'пасс-анал': '',      
	'вспом': '',      
	'агент': '',      
	'кратн': '',      
	'инф-союзн': '',      
	'электив': '',      
	'композ': '',      
	'колич-огран': '',      
	'неакт-компл': '',      
	'пролепт': '',       
	'суб-копр': '',       
	'дат-субъект': '',      
	'длительн': '',      
	'об-аппоз': '',      
	'изъясн': '',      
	'компл-аппоз': '',      
	'оп-опред': '',      
	'1-несобст-компл': '',      
	'распред': '',      
	'уточн': '',      
	'нум-аппоз': '',      
	'ном-аппоз': '',      
	'2-несобст-компл': '',      
	'аппрокс-колич': '',      
	'колич-вспом': '',      
	'колич-копред': '',      
	'кратно-длительн': '',      
	'об-копр': '',      
	'эллипт': '',      
	'3-несобст-компл': '',       
	'4-несобст-компл': '',       
	'fictit': '',       
	'авт-аппоз': '',       
	'аддит': '',       
	'адр-присв': '',       
	'дистанц': '',       
	'несобст-агент': '',       
	'об-обст': '',       
	'обст-тавт': '',       
	'презентат': '',       
	'сент-предик': '',       
	'суб-обст': '',       
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