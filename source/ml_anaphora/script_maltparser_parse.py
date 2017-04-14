import os
import sys
sys.path.append('..')
from config import PATH_MALTPARSER


def parse_text(input_file, output_file, path_maltparser):
    os.chdir(path_maltparser)
    result = "java -jar maltparser-1.7.1.jar -c russian -i %s -o %s -m parse" % (input_file, output_file)
    os.system(result)

def exec_command(package_path, file_name):
    input_file = package_path + '/tmp/maltparser/' + file_name

    output_path = package_path + '/tmp/res_maltparser/'
    print('$$$$ output_file = ' + output_path)
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    output_file = package_path + '/tmp/res_maltparser/' + file_name
    parse_text(input_file, output_file, PATH_MALTPARSER)

if __name__ == '__main__':
    file_name = 'test.txt'
    exec_command(os.getcwd(), file_name)