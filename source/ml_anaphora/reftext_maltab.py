import json
import os

from collections import defaultdict

# get file with parsed anaphora and translate this to features format
import sys
sys.path.append('../sentence_to_malt')
from maltparser_translater import SentenceParser
sys.path.append('..')
from config import npro_sample
import script_maltparser_parse


class RefTextSentenceParser:

    def __init__(self, output_package='tmp', input_package='resource'):
        self._output_package = output_package
        self._input_package = input_package
        self._package_path = os.getcwd()

    def parse(self, opened_file):
        data = json.load(opened_file)
        sentences = data.get('docInfo') if data else []
        relation_info = data.get('relInfo') if data else []

        # todo: maybe should be add feautures depends on Signs : {',';'!';etc.};
        # todo: merge syntax_classifier information and relation_info
        # position => column index
        self._parse_sentences(sentences)
        self._parse_marked_info(relation_info)
        self._find_cadidate_()

    #prepare data to maltparser, write in file package ./tmp/maltparser/{file_name}
    def _parse_sentences(self, sentences):
        self._sentences = []
        self._pronounces = []
        # array with sentence offset, will be used for save anaphora position.
        self._sentence_offset = {}
        sentence_position = 0
        previous_offset = 0
        for sentence in sentences:
            self._sentence = []
            words_in_sentence = sentence.get('Words')
            sentence_index = sentence.get('Index')
            for word in words_in_sentence:
                _parsed_word = self.sentence_parser.morph_analyze_malt_tab(word.get('Value'))
                _pronounce = {}
                if _parsed_word.NPRO:
                    _pronounce['position'] = previous_offset + len(self._sentence)
                    _pronounce['sent_id'] = sentence_index
                    _pronounce['word_id'] = word.get('Index')
                    self._pronounces.append(_pronounce)
                self._sentence.append(_parsed_word)
            self._sentences.append(self._sentence)

            self._sentence_offset[sentence_position] = previous_offset
            previous_offset = previous_offset + len(self._sentence) + 1
            sentence_position += 1

        package_path = self._package_path + '/tmp/maltparser'

        self.sentence_parser.write_data(self._sentences, self._file_name_txt, package_path)
        self.write_pronounces()

    #parse info about anafora, write in file package ./tmp/anaphora/{file_name}
    # example exit data [{"x":["y","z"]}]
    # x is antecedent y and z is pronoun that could be change by antecedent
    def _parse_marked_info(self, relation_info):
        self._anaphora_relationship = defaultdict(list)
        for relation in relation_info:
            #----------------------------HEAD----------------------------
            _rel_head = relation.get('RelationHead')
            # todo: take only one world array Example: 'Михаил Леонович Гаспаров' => take first word in chain
            head_word = _rel_head.get('Words')[0]
            anaphora_offset = self._sentence_offset[head_word.get('SentIndex')] + head_word.get('WordIndex')

            #----------------------------RelInfo----------------------------
            _rel_part_array = relation.get('RelationParts')
            for pretender in _rel_part_array:
                _word_pretenders = pretender.get('Words')
                # todo: work only with one anaphora word
                word_pretender = _word_pretenders[0]
                _is_appropriate_pronoun = self._sentences[word_pretender.get('SentIndex')][word_pretender.get('WordIndex')][0]
                if not pretender.get('IsAnaphor') or not (_is_appropriate_pronoun in npro_sample):
                    continue

                if len(_word_pretenders) > 1:
                    print('WARNING: more than one word in pretender')

                _anaphora_position = self._sentence_offset[word_pretender.get('SentIndex')] + word_pretender.get('WordIndex')
                self._anaphora_relationship[anaphora_offset].append(_anaphora_position)

        #----------------------------WriteInFile----------------------------
        self.write_anaphora()

    #parse info about
    def _find_cadidate_(self):
        script_maltparser_parse.exec_command(self._file_name_txt)
        input_file = open(self._package_path + '/tmp/res_maltparser/' + self._file_name_txt)
        self._malt_sentences = self.sentence_parser.read_malttab(input_file)
        # print('\n'.join(map(lambda x: str(x), self._sentences)))
        for pronoun in self._pronounces:
            self._filter_candidate(pronoun)
        # for anaphora in self._anaphora_relationship:
        #     anaphora.

    # find candidate:
    #     * in distance not more than 3 sentence
    #     * different root group
    #     * same gender, quantity *right now ignored plural nouns*
    def _filter_candidate(self, pronoun):
        _pronoun_sentence = self._malt_sentences[pronoun.get('sent_id')]
        _pronoun = _pronoun_sentence.get_word(pronoun.get('word_id'))
        _pronoun_position = _pronoun_sentence.get_start_pos() + pronoun.get('word_id')
        _pronoun_gender = _pronoun.get('morph').split('.')[1]

        print(pronoun)
        print(_pronoun)
        print('========================================================================')

        pronoun_sentence_id = pronoun.get('sent_id')
        pronoun_parent = self._find_parent_syntax_tree(_pronoun_sentence, _pronoun)

        start_sentence_search = max(pronoun_sentence_id - 3, 0)
        _cadidate_list = []
        for sentence in self._malt_sentences[start_sentence_search: pronoun_sentence_id]:
            _current_word_position_in_sentence = -1
            for word in sentence.get_words():
                _current_word_position_in_sentence += 1
                _current_word_morph = word.get('morph')

                _current_word_morph_check = _current_word_morph and _current_word_morph.split('.')[0] == 'S'
                _current_word_syntax_check = (self._find_parent_syntax_tree(sentence, word) != pronoun_parent)
                _current_word_gender_quantity = _current_word_morph_check and _current_word_morph.split('.')[1] == _pronoun_gender

                if _current_word_morph_check and _current_word_syntax_check and _current_word_gender_quantity:
                    _current_word_position = sentence.get_start_pos() + _current_word_position_in_sentence
                    _distance = _pronoun_position - _current_word_position
                    word['distance'] = _distance
                    word['positon'] = _current_word_position
                    _cadidate_list.append(word)

        print(len(_cadidate_list))
        print('\n'.join(map(lambda x: str(x), _cadidate_list)))
        print('------------------------------------------------------------------------')

    # find verb group for word
    def _find_parent_syntax_tree(self, sentence, word):
        word_parent = word
        while word_parent.get('syntax') != 'ROOT':
            # print(word_parent)
            word_parent = sentence.get_word(int(word_parent.get('id'))-1)
        return word_parent

    def write_anaphora(self):
        out_file_package = self._package_path + '/tmp/anaphora/'
        if not os.path.exists(out_file_package):
            os.makedirs(out_file_package)

        out_file = open(out_file_package + self._file_name_json, 'w')
        json.dump(self._anaphora_relationship, out_file)
        out_file.close()

    def write_pronounces(self):
        out_file_package = self._package_path + '/tmp/pronouns/'
        if not os.path.exists(out_file_package):
            os.makedirs(out_file_package)
        out_file = open(out_file_package + self._file_name_json, 'w')
        json.dump(self._pronounces, out_file)
        out_file.close()

    def read(self, file_name):
        self.sentence_parser = SentenceParser()
        self._file_name_json = file_name
        input_file = open(self._input_package + '/' + self._file_name_json)
        self._file_name_txt = file_name.replace('.json', '.txt')
        self.parse(input_file)
        input_file.close()

if __name__ == '__main__':
    sentence_parser = RefTextSentenceParser()
    sentence_parser.read('test.json')