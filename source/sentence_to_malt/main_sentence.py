from maltparser_translater import SentenceParser

# get file with default readeable format and translate it to malttab format to be parsed by classifier

if __name__ == '__main__':
    sentence_parser = SentenceParser()
    sentence_parser.read('test.txt')