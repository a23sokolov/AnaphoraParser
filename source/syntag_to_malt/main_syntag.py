from optparse import OptionParser # @todo: add in requirements
from syntagrus import Reader
import glob, os
import sys
sys.path.append('..')
from config import PATH_SYNTAGRUS
from clint.textui import progress # @todo: add in requirements

# в скобочках указываются параметры которые определены по определению для русского языка.
# * те параметры которые по каким либо причинам не являются важными хотя они есть в SyntagRus.
# ** те параметры которые просто не учитываются в SyntagRus, но они есть pymorphy2.
selected_feat = {'m', 'f', 'n', # род(муж, жен, средний, общий**)
				 'sg', 'pl', # число(ед, мн)
				 '1p', '2p', '3p', # лицо(1-ое, 2-ое, 3-ье)
				 'nom', 'gen', 'gen2', 'dat', 'acc', 'ins', 'prep', 'loc', # падежи. gen2 партитивный падеж, loc - местный падеж более подробно pamjatka.
				 'real', 'imp', # наклонение (изъяв, пов)
				 'pass', # залог (страдательный)
				 'comp', # степень(сравнительная, превосходная) сравнения только сравнительная
				 'shrt' # краткость (прилагательные, причастия)
				 }

# get file with SyntagRus format and translate it to malttab format for training classifier
if __name__ == '__main__':
    """
    # simple example:
    # ================================================
    #   python3 main_syntag.py -p /path/to/folder -n 10
    # ================================================
    # folder should contain another inner folder and in them should be *.tgt files
    # # example:
    #   /..../SyntagRus/*/*.tgt path should be /..../SyntagRus/
    #   Directory structure
    #   .....
    #       SyntagRus
    #           + info
    #               test.tgt
    #           + info2
    # # if everything ok, result should be in res directory file model.txt
    #
    # # Problems:
    # if you have this problem
    # UnicodeDecodeError: 'utf-8' codec can't decode byte 0xcb in position 95: invalid continuation byte
    # start script in debug mode
    """
    parser = OptionParser()
    parser.add_option('-d', '--debug', action='store_true', dest='debug', help='debug mode', default=False)
    parser.add_option('-p', '--path', action='store', dest='path', type='string', help='path to model')
    parser.add_option('-n', '--number', action='store', dest='number', type='int', help='number of files to process')
    (options, args) = parser.parse_args()

    path = options.path
    if not options.path:
        print('Will be used path from config')
        path = PATH_SYNTAGRUS

    out_file = open("result/model.txt", "w")
    current_path = os.getcwd()
    os.chdir(path + '/news')
    print(str(path + '/news/'))
    files = glob.glob('*.tgt')
    limit = options.number if options.number else len(files)
    print(len(files))

    i = 0
    step = (int)(0.05 * limit)
    step = step if step > 0 else 1

    with progress.Bar(label="Progress", expected_size=limit) as bar:
        for file in files[: limit]:
            if not options.debug:
                if i % step or i + 1 == limit:
                    bar.show(i + 1)
                i += 1
            else:
                print(file)
            out_sentences = []
            R = Reader()
            sentences = R.read(file)
            for sentence in sentences:
                _out_sentence = []
                for word in sentence:
                    w = word[0] or 'FANTOM'
                    p = '.'.join([word[1].pos] + sorted(word[1].feat & selected_feat))
                    l = word[1].link if word[1].dom else 'ROOT'
                    d = str(word[1].dom)
                    _out_sentence.append('\t'.join([w, p, d, l]))
                out_sentences.append('\n'.join(_out_sentence))
            end_file = "\n\n"
            if i == limit or i == len(files):
                end_file = ""
            out_file.write("\n\n".join(out_sentences) + end_file)
            del (R)
            del (out_sentences)

    out_file.close()

