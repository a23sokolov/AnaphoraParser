# -*- coding: utf-8 -*-
from maltparser_translater import SentenceParser
import sys

import os, glob
sys.path.append('..')
from config import PATH_ARTICLES

# get file with default readeable format and translate it to malttab format to be parsed by classifier

if __name__ == '__main__':
    sentence_parser = SentenceParser(input_package=PATH_ARTICLES)
    os.chdir(PATH_ARTICLES)
    files = glob.glob('*.txt')
    for file in files:
        sentence_parser.read(file)