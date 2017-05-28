# -*- coding: utf-8 -*-
import json
import glob, os
import random

from collections import defaultdict

# get file with parsed anaphora and translate this to features format
import sys
sys.path.append('../sentence_to_malt')
from maltparser_translater import SentenceParser
sys.path.append('..')
from config import npro_sample, PATH_REFTEXTS, PATH_ARTICLES, syntax_list, word_to_ignore
import script_maltparser
import numpy as np
import main_classifier
from nltk.tokenize import sent_tokenize,word_tokenize

morph_case_list = ['nom', 'gen', 'dat', 'acc', 'ins', 'prep', 'loc']
distance_list = [10, 30, 1000]
FEATURES_SIZE = 79

# WORK_WITH_PLAIN_TEXT
WORK_WITH_PLAIN_TEXT = False
PATH_TO_FILE = PATH_ARTICLES if WORK_WITH_PLAIN_TEXT else PATH_REFTEXTS
EXTENSION = '*.txt' if WORK_WITH_PLAIN_TEXT else '*.json'

class RefTextSentenceParser:

    def __init__(self, data_to_learn, output_package):
        self._package_path = output_package
        self.data_to_learn = data_to_learn

    def parse(self, opened_file):
        data = json.load(opened_file)
        sentences = data.get('docInfo') if data else []
        relation_info = data.get('relInfo') if data else []

        # todo: maybe should be add feautures depends on Signs : {',';'!';etc.};
        # position => column index
        self._parse_sentences(sentences, (lambda sentence: sentence.get('Words')), (lambda word: word.get('Value')))
        self._parse_marked_info(relation_info)
        self._find_cadidates()
        self.data_to_learn.vectorize_data(noun_candidate=self.noun_candidate, anaphora_relationship=self._anaphora_relationship)

    def parse_plain_text(self, opened_file):
        data = json.load(opened_file)

        self._sentences = []
        self._pronounces = []
        # array with sentence offset, will be used for save anaphora position.
        self._sentence_offset = {}
        sentences = []
        for article in data:
            _sentences = article.get('text')
            sentences.extend(sent_tokenize(_sentences))

        self._parse_sentences(sentences, (lambda sentence: word_tokenize(sentence)), (lambda word: word))
        self._find_cadidates()
        self.data_to_learn.vectorize_data(noun_candidate=self.noun_candidate, anaphora_relationship=defaultdict(list), file_name=self._file_name_txt)

    # prepare data to maltparser, write in file package ./tmp/maltparser/{file_name}
    # also take all pronounces with anaphora True
    def _parse_sentences(self, sentences, get_words, get_word):
        self._sentences = []
        self._pronounces = []
        # array with sentence offset, will be used for save anaphora position.
        self._sentence_offset = {}
        sentence_index = 0
        previous_offset = 0
        for sentence in sentences:
            self._sentence = []
            words_in_sentence = get_words(sentence)
            word_index = 0
            for word in words_in_sentence:
                if word in word_to_ignore:
                    continue
                _parsed_word = self.sentence_parser.morph_analyze_malt_tab(get_word(word))
                _pronounce = {}
                if _parsed_word.NPRO:
                    _pronounce['position'] = previous_offset + len(self._sentence)
                    _pronounce['sent_id'] = sentence_index
                    _pronounce['word_id'] = word_index
                    self._pronounces.append(_pronounce)
                self._sentence.append(_parsed_word)
                word_index += 1
            self._sentences.append(self._sentence)

            self._sentence_offset[sentence_index] = previous_offset
            previous_offset = previous_offset + len(self._sentence) + 1
            sentence_index += 1

        package_path = self._package_path + '/tmp/maltparser'

        self.sentence_parser.write_data(self._sentences, self._file_name_txt, package_path)
        self.write_pronounces()

    # It is used in following calculations:
    #   self._marked_pronounces
    # used only for human read:
    #   parse info about anafora, write in file package ./tmp/anaphora/{file_name}
    #   example exit data [{"x":["y","z"]}]
    #   x is antecedent y and z is pronoun that could be change by antecedent
    def _parse_marked_info(self, relation_info):
        self._anaphora_relationship = defaultdict(list)
        self._marked_pronounces = []
        for relation in relation_info:
            #----------------------------HEAD----------------------------
            _rel_head = relation.get('RelationHead')
            # FIXME: take only one world array Example: 'Михаил Леонович Гаспаров' => take first word in chain
            head_word = _rel_head.get('Words')[0]
            anaphora_offset = self._sentence_offset[head_word.get('SentIndex')] + head_word.get('WordIndex')

            #----------------------------RelInfo----------------------------
            _rel_part_array = relation.get('RelationParts')
            _anaphora_rel = {}
            _anaphora_rel['head'] = anaphora_offset
            _anaphora_rel['values'] = []
            for pretender in _rel_part_array:
                _word_pretenders = pretender.get('Words')
                # FIXME: work only with one anaphora word, and ignore not correct data.
                if not _word_pretenders:
                    print(pretender)
                    continue

                word_pretender = _word_pretenders[0]
                _is_appropriate_pronoun = self._sentences[word_pretender.get('SentIndex')][word_pretender.get('WordIndex')][0]
                if not pretender.get('IsAnaphor') or not (_is_appropriate_pronoun in npro_sample):
                    continue

                if len(_word_pretenders) > 1:
                    print('WARNING: more than one word in pretender')

                _anaphora_position = self._sentence_offset[word_pretender.get('SentIndex')] + word_pretender.get('WordIndex')
                self._anaphora_relationship[anaphora_offset].append(_anaphora_position)
                _anaphora_rel['values'].append(_anaphora_position)
                self._marked_pronounces.append(_anaphora_position)

        #----------------------------WriteInFile----------------------------
        self.write_anaphora()

    # parse info about candidate after maltparser parse.
    def _find_cadidates(self):
        script_maltparser.prepare_to_parse(self._package_path, self._file_name_txt)
        input_file = open(self._package_path + '/tmp/res_maltparser/' + self._file_name_txt)
        self._malt_sentences = self.sentence_parser.read_malttab(input_file)
        print('sentences.start_pos = ' + str(list(map(lambda x: x.get_start_pos(), self._malt_sentences))))
        self.noun_candidate = []
        for pronoun in self._pronounces:
            # working only with anaphora marked pronounces from dictionary in @file:config.py.
            if not hasattr(self, '_marked_pronounces') or pronoun.get('position') in self._marked_pronounces:
                self._filter_candidate(pronoun)

    # find candidate:
    #  +   * in distance not more than 3 sentence
    #  +   * different root group, trouble большое количество ошибок из-за этого, могут отбрасываться кандидаты правильные
    #  +   * same gender, quantity *right now ignored plural nouns*
    def _filter_candidate(self, pronoun):
        _pronoun_sentence = self._malt_sentences[pronoun.get('sent_id')]
        _pronoun = _pronoun_sentence.get_word(pronoun.get('word_id'))
        _pronoun_position = _pronoun_sentence.get_start_pos() + pronoun.get('word_id')
        _pronoun_gender = _pronoun.get('morph').split('.')[1] if len(_pronoun.get('morph').split('.')) == 4 else None
        _pronoun_quantity = _pronoun.get('morph').split('.')[3 if len(_pronoun.get('morph').split('.')) == 4 else 2]

        #  *DEBUG*
        # print(pronoun)
        # print('founded pronoun = ' + str(_pronoun) + ', _pronoun_gender = ' + str(_pronoun_gender) + ', _pronoun_quantity = ' + str(_pronoun_quantity))
        # print('========================================================================')

        pronoun_sentence_id = pronoun.get('sent_id') + 1
        pronoun_parent = self._find_parent_syntax_tree(_pronoun_sentence, _pronoun)

        start_sentence_search = max(pronoun_sentence_id - 3, 0)
        _candidate_list = []
        for sentence in self._malt_sentences[start_sentence_search: pronoun_sentence_id]:
            _current_word_position_in_sentence = -1
            for word in sentence.get_words():
                _current_word_position_in_sentence += 1
                _current_word_morph = word.get('morph')

                _current_word_is_not_pronoun = not word.get('word') in npro_sample
                _current_word_morph_check = _current_word_morph and _current_word_morph.split('.')[0] == 'S'
                _current_word_syntax_check = (self._find_parent_syntax_tree(sentence, word) != pronoun_parent)
                _current_word_gender_quantity = _current_word_morph_check \
                                                and (not _pronoun_gender or _current_word_morph.split('.')[1] == _pronoun_gender)\
                                                and _current_word_morph.split('.')[3 if len(_current_word_morph.split('.')) == 4 else 2] == _pronoun_quantity
                _current_word_position = sentence.get_start_pos() + _current_word_position_in_sentence
                _distance = _pronoun_position - _current_word_position
                if _current_word_is_not_pronoun and _current_word_morph_check and _current_word_syntax_check and _current_word_gender_quantity and _distance > 0 \
                        or (hasattr(self, '_anaphora_relationship') and _current_word_position - 1 in self._anaphora_relationship): # FIXME: HACK to take right candidate ignoring filter result.
                    _word = dict(word)
                    _word['distance'] = _distance
                    _word['position'] = _current_word_position
                    _candidate_list.append(_word)

        # *DEBUG*
        # print('------------------------_candidate_list---------------------------------')
        # print('\n'.join(map(lambda x: str(x), _candidate_list)))
        # print('------------------------------------------------------------------------')

        # add only 2 candidates: right and not_right. Else would be added only not_right.
        # selected_candidate_r - random candidate not right
        # selected_candidate_real - right candidate
        # @TODO: sould be optimized
        # comment when work with plain text

        if not WORK_WITH_PLAIN_TEXT and _candidate_list:
            # ==============
            current_candidate_list = _candidate_list
            selected_candidate_r = random.choice(current_candidate_list)
            while selected_candidate_r.get('position') - 1 in self._anaphora_relationship and len(current_candidate_list) > 1:
                current_candidate_list.remove(selected_candidate_r)
                selected_candidate_r = random.choice(current_candidate_list)
            real_ana = None
            for selected_candidate_real in _candidate_list:
                if not selected_candidate_real.get('position') - 1 in self._anaphora_relationship:
                    continue
                else:
                    real_ana = selected_candidate_real
                    break
            new_list = [real_ana, selected_candidate_r] if real_ana and len(current_candidate_list) > 1 else [selected_candidate_r]
            self.noun_candidate.extend(new_list)
            # ==============
        else:
            # ==============
            self.noun_candidate.extend(_candidate_list)
            # ==============


    # find verb group for word
    def _find_parent_syntax_tree(self, sentence, word):
        word_parent = word
        # usually it is equal word_parent.get('syntax') != 'ROOT'
        while int(word_parent.get('id')) != 0:
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
        print('pronoun = ' + out_file_package + self._file_name_json)
        out_file = open(out_file_package + self._file_name_json, 'w')
        json.dump(self._pronounces, out_file)
        out_file.close()

    def read(self, folder_path, file_name):
        self.sentence_parser = SentenceParser()
        self._file_name_json = file_name
        input_file = open(folder_path + '/' + file_name)
        self._file_name_txt = file_name.replace('.json', '.txt')
        if WORK_WITH_PLAIN_TEXT:
            self.parse_plain_text(input_file)
        else:
            self.parse(input_file)
        input_file.close()

class DataToLearn:
    def __init__(self, path):
        self.train_matrix = np.zeros(shape=(0, FEATURES_SIZE), dtype='float32')
        self.y_vector = np.zeros(shape=(0, 0), dtype='float32')
        if not os.path.exists(path + '/tmp'):
            os.makedirs(path + '/tmp')
        self.vectorize_data_file = open(path + '/tmp/vectorize.txt', 'w')

    # syntax all relationship
    # distance range
    #       [1,0,0] distance less 10
    #       [0,1,0] distance less 30
    #       [0,0,1] another
    # morph
    #       [1] is S ignore because filter decide this problem
    #       [1,0,0] is m, [0,1,0] is f, [0,0,1] is n ignore because filter decide this problem
    #       [1,0,0,0,0,0] nom, [0,1,0,0,0,0] gen, [0,0,1,0,0,0] dat,
    #       [0,0,0,1,0,0] acc, [0,0,0,0,1,0] ins, [0,0,0,0,0,1] prep
    # syntax
    #       vector of 69 positions
    # vector size 3 + 6 + 69 = 78 = FEATURES_SIZE
    def vectorize_data(self, noun_candidate, anaphora_relationship, file_name=None):
        offset_distance = 0
        offset_case = 3
        offset_syntax = offset_case

        # DEBUG
        # print('==================================')
        # print('\n'.join(map(lambda x: str(x), noun_candidate)))
        # print('==================================')

        # create empty matrix to concatenate in future.
        y_vector = np.zeros(shape=(1, len(noun_candidate)), dtype='float32')

        print('======================')
        if file_name:
            self.vectorize_data_file.write(file_name + '\n')
            self.vectorize_data_file.write('\n'.join(map(lambda x: str(x), noun_candidate)))
        print('\n'.join(map(lambda x: str(x), noun_candidate)))
        print('======================')
        print(anaphora_relationship)

        for candidate in noun_candidate:
            candidate_vector = np.zeros(shape=(1, FEATURES_SIZE), dtype='float32')

            # supervised vector value for learn
            if candidate.get('position') - 1 in anaphora_relationship:
                y_vector[0][noun_candidate.index(candidate)] = 1

            # distance features set
            distance = list(filter(lambda x: candidate.get('distance') < x, distance_list))[0]
            if distance in distance_list:
                candidate_vector[0][offset_distance + distance_list.index(distance)] = 1

            # case features set
            # morph_list = candidate.get('morph').split('.')
            # morph_case = morph_list[len(morph_list) - 2] if len(morph_list) > 0 else ''
            # if morph_case in morph_case_list:
            #     candidate_vector[0][offset_case + morph_case_list.index(morph_case)] = 1

            # syntax features set
            syntax = candidate.get('syntax')
            if syntax in syntax_list:
                candidate_vector[0][offset_syntax + syntax_list.index(syntax)] = 1

            self.train_matrix = np.concatenate((self.train_matrix, candidate_vector), axis=0)
        self.y_vector = np.append(self.y_vector, y_vector)


    def print_vector(self):
        print('-------------- y_vector = ' + str(len(self.y_vector)) + ' --------------')
        print('-------------- x_matrix_height = ' + str(len(self.train_matrix)) + ' --------------')
        print('-------------- x_matrix_features = ' + str(len(self.train_matrix[0])) + ' --------------')
        print(self.train_matrix)
        print(self.y_vector)


def main(path, extention):
    current_path = os.getcwd()
    print (current_path)
    os.chdir(path)
    files = glob.glob(extention)
    print('files to learn = ' + str(len(files)))
    os.chdir(current_path)

    data_to_learn = DataToLearn(current_path)
    for file in files[3:4]:
        print(file)
        sentence_parser = RefTextSentenceParser(data_to_learn, output_package=current_path)
        sentence_parser.read(path, file)
    print(os.getcwd())
    os.chdir(current_path)
    data_to_learn.print_vector()
    # main_classifier.train_predict(data_to_learn.train_matrix, data_to_learn.y_vector, 5)

    main_classifier.predict_on_created_model(data_to_learn.train_matrix, data_to_learn.y_vector, 0)


if __name__ == '__main__':
    main(PATH_TO_FILE, EXTENSION)