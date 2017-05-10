# -*- coding: utf-8 -*-
import os
import sys
from config import PATH_MALTPARSER


def parse_text(input_file, output_file):
    os.chdir(PATH_MALTPARSER)
    result = "java -jar maltparser-1.7.1.jar -c russian -i %s -o %s -m parse" % (input_file, output_file)
    os.system(result)

def prepare_to_parse(package_path, file_name):
    input_file = package_path + '/tmp/maltparser/' + file_name

    output_path = package_path + '/tmp/res_maltparser/'
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    output_file = package_path + '/tmp/res_maltparser/' + file_name
    parse_text(input_file, output_file)


def learn_classifier(input_file):
    os.chdir(PATH_MALTPARSER)
    result = "java -Xmx8000m -jar maltparser-1.7.1.jar -c russian -i %s -if appdata/dataformat/malttab.xml -m learn -l liblinear" % (input_file)
    os.system(result)

def prepare_to_learn(package_path, file_name):
    input_file = package_path + '/tmp/maltparser/' + file_name
    learn_classifier(input_file)


if __name__ == '__main__':
    pass
    # file_name = 'test.txt'
    # exec_command(os.getcwd(), file_name)

    # learn maltparser
    # input_file = os.getcwd() + '/syntag_to_malt/result/model.txt'
    # learn_classifier(input_file)

    # PREPARE DATA FOR TEST
    # output_file = os.getcwd() + '/syntag_to_malt/quality_test/res_model.txt'
    # parse_text(input_file, output_file)