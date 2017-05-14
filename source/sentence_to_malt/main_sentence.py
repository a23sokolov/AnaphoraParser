# -*- coding: utf-8 -*-
from maltparser_translater import SentenceParser
import sys

import os, glob
sys.path.append('..')
from config import PATH_ARTICLES
import script_maltparser

# get file with default readeable format and translate it to malttab format to be parsed by classifier

if __name__ == '__main__':
    current_path = os.getcwd()
    sentence_parser = SentenceParser(input_package=PATH_ARTICLES)
    os.chdir(PATH_ARTICLES)
    files = glob.glob('*.txt')
    os.chdir(current_path)
    for file in files[1:2]:
        sentence_parser.read(file)
        script_maltparser.prepare_to_parse(os.getcwd(), file)