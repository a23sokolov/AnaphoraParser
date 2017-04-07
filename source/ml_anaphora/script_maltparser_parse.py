import os
import sys
sys.path.append('..')
from config import PATH_MALTPARSER


def parse_text(input_file, output_file, path_maltparser):
    os.chdir(path_maltparser)
    result = "java -jar maltparser-1.7.1.jar -c russian -i %s -o %s -m parse" % (input_file, output_file)
    os.system(result)

def exec_command(file_name):
    input_file = os.getcwd() + '/tmp/maltparser/' + file_name
    output_file = os.getcwd() + '/tmp/res_maltparser/' + file_name
    parse_text(input_file, output_file, PATH_MALTPARSER)

if __name__ == '__main__':
    file_name = 'test.txt'
    exec_command(file_name)