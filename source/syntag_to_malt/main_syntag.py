from optparse import OptionParser
from syntagrus import Reader
import glob, os
from clint.textui import progress

selected_feat = {'m', 'f', 'n', 'sg', 'pl', '1p', '2p', '3p', 'nom', 'gen', 'gen2', 'dat', 'acc', 'ins', 'prep',
                 'loc', 'real', 'imp', 'pass', 'comp', 'shrt'}


if __name__ == '__main__':
    """
    # simple example:
    # python3 main_syntag.py -p /path/to/folder -n 10
    # folder should contain another inner folder and in them should be *.tgt files
    # # example:
    #   /..../SyntagRus/*/*.tgt path should be /..../SyntagRus
    #   Directory structure
    #       SyntagRus
    #           + info
    #               test.tgt
    #           + info2
    # # if everything ok, result should be in res directory
    #
    # # Problems:
    # if you have this problem start script in debug mode
    # UnicodeDecodeError: 'utf-8' codec can't decode byte 0xcb in position 95: invalid continuation byte
    # use
    """
    parser = OptionParser()
    parser.add_option('-d', '--debug', action='store_true', dest='debug', help='debug mode', default=False)
    parser.add_option('-p', '--path', action='store', dest='path', type='string', help='path to model')
    parser.add_option('-n', '--number', action='store', dest='number', type='int', help='number of files to process')
    (options, args) = parser.parse_args()

    if not options.path:
        print('Specify path')
        exit()

    out_file = open("../../res/model.txt", "w")
    current_path = os.getcwd()
    os.chdir(options.path)
    files = glob.glob('*/*.tgt')
    limit = options.number if options.number else len(files)

    i = 0
    step = (int)(0.05 * limit)
    step = step if step > 0 else 1

    with progress.Bar(label="Progress", expected_size=limit) as bar:
        for file in files[0:limit]:
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
            out_file.write("\n\n".join(out_sentences))
            del (R)
            del (out_sentences)

    out_file.close()

