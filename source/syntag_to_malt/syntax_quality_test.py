# -*- coding: utf-8 -*-
import os, sys
from sklearn import metrics
import numpy as np
sys.path.append('../sentence_to_malt')
from maltparser_translater import SentenceParser
sys.path.append('..')
import script_maltparser
from config import syntax_list

# HOW TO USE:
# 1) first of all train MaltParser.
# 2) Prepare data for test, start main_syntag with package or part of SyntagRus. Right data set.
# 3) Start this script. with
#                       test_pure: clear test SyntagRus result maltparser classifier.
#                       test_morph_analyze: test with pymorphy2 morph description words.
# Script will create predicted data set in folder "quality_test".

#TODO create morphological test, it will be compare SyntagRus and pymorphy2 res.
def _vectorize_data(sentences):
    '''
    :param sentences: list of maltparser_translate.ParsedSentence
    :return: numpy matrix
    '''
    syntax_matrix = np.zeros(shape=(0, len(syntax_list)), dtype='float32')
    print('_vectorize_data sentences.len = ' + str(len(sentences)))
    count = 0
    words = 0
    sentence_parser = SentenceParser()
    for sentence in sentences:
        count += 1
        if count % 500 == 0:
            print('_vectorize_data position = ' + str(count))
        words += len(sentence.get_words())
        for word in sentence.get_words():
            syntax = word.get('syntax')
            if syntax in syntax_list:
                syntax_vector = np.zeros(shape=(1, len(syntax_list)), dtype='float32')
                syntax_vector[0][syntax_list.index(syntax)] = 1
                syntax_matrix = np.concatenate((syntax_matrix, syntax_vector), axis=0)

    return syntax_matrix, words, len(sentences)

def _prepare_morph_mark():
    current_path = os.getcwd()
    _file_name_txt = 'morph_res.txt'
    package_path = current_path + '/quality_test'
    input_file = open(current_path + '/result/model.txt')
    sentence_parser = SentenceParser()

    _new_sentences = []
    sentences = sentence_parser.read_malttab(input_file)
    for sentence in sentences:
        _new_sentence = []
        for word in sentence.get_words():
            word = sentence_parser.morph_analyze_malt_tab(word.get('word'))
            _new_sentence.append(word)
        _new_sentences.append(_new_sentence)
    sentence_parser.write_data(_new_sentences, _file_name_txt, package_path)

def test_body(test_file_path, input_file_path, output_file_path):
    n_times = 1
    n_samples = []
    sentence_parser = SentenceParser()
    print('---------- create right_matrix ----------')
    input_file = open(test_file_path)
    input_matrix,\
        words,\
        sentences = _vectorize_data(sentence_parser.read_malttab(input_file))

    for i in range(n_times):
        print('============= test iteration number = {} ============='.format(i))
        script_maltparser.parse_text(input_file_path, output_file_path)

        output_file = open(output_file_path)
        print('---------- create predict_matrix ----------')
        output_matrix,\
            words,\
            sentences = _vectorize_data(sentence_parser.read_malttab(output_file))
        # 0.75 average delay
        accuracy = metrics.accuracy_score(input_matrix, output_matrix)
        test_obj = {'accuracy': accuracy, 'words': words, 'sentences': sentences}
        n_samples.append(test_obj)
        print('accuracy ' + str(accuracy))

    print('|============ samples ============|')
    print('\n'.join(map(lambda x: str(x), n_samples)))

def test_pure():
    current_path = os.getcwd()
    test_file_path = current_path + '/result/model.txt'
    input_file_path = current_path + '/result/model.txt'
    output_file_path = current_path + '/quality_test/res_model.txt'
    test_body(test_file_path, input_file_path, output_file_path)

def test_morph_analyze():
    current_path = os.getcwd()
    test_file_path = current_path + '/result/model.txt'
    input_file_path = current_path + '/quality_test/morph_res.txt'
    output_file_path = current_path + '/quality_test/res_model.txt'
    # useless iterate each time in test. data will be the same.
    _prepare_morph_mark()
    test_body(test_file_path, input_file_path, output_file_path)

if __name__ == '__main__':
    output_folder_path = os.getcwd() + '/quality_test'
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)
    test_morph_analyze()
    # test_pure()