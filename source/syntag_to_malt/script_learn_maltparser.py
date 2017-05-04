# -*- coding: utf-8 -*-
import os
import sys
sys.path.append('..')
from config import PATH_MALTPARSER


def parse_text(input_file, path_maltparser):
    os.chdir(path_maltparser)
    result = "java -Xmx8000m -jar maltparser-1.7.1.jar -c russian -i %s -if appdata/dataformat/malttab.xml -m learn -l liblinear" % (input_file)
    os.system(result)

if __name__ == '__main__':
    input_file = os.getcwd() + '/result/model.txt'
    parse_text(input_file, PATH_MALTPARSER)