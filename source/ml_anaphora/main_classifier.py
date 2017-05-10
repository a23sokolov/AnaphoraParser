# -*- coding: utf-8 -*-
from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.ensemble import RandomForestClassifier
import _pickle as pickle
import numpy as np
from sklearn import preprocessing
import os, glob

N_ITER = 7
RANDOM_STATE = 42

REDUCE_DIM = TruncatedSVD # or PCA
CLASSIFIER = RandomForestClassifier
N_ESTIMATORS = 10

class SparseClassifier():
    def __init__(self, n_components=None, reduce_dim=None, classifier=None):
        self.n_components = n_components
        self.reduce_dim = reduce_dim
        self.classifier = classifier
        pass

    def fit(self, X_train, y_true):
        def unique_rows(a):
            b = np.ascontiguousarray(a).view(np.dtype((np.void, a.dtype.itemsize * a.shape[1])))
            _, idx = np.unique(b, return_index=True)
            return a[idx]

        if not self.reduce_dim:
            self.reduce_dim = REDUCE_DIM(n_components=self.n_components, n_iter=N_ITER, random_state=RANDOM_STATE)

        self.reduce_dim.fit(unique_rows(X_train))
        X_train = preprocessing.scale(self.reduce_dim.transform(X_train))
        if not self.classifier:
            self.classifier = CLASSIFIER(n_estimators=N_ESTIMATORS)
        self.classifier.fit(X_train, y_true)

    def predict(self, X):
        return self.classifier.predict(preprocessing.scale(self.reduce_dim.transform(X)))

    def dump(self, folder, filename):
        if not os.path.exists(folder):
            os.makedirs(folder)
        pickle.dump((self.reduce_dim, self.classifier, self.n_components),
                    open('{}/{}'.format(folder, filename), 'wb'))

    @staticmethod
    def load(folder, filename):
        result = SparseClassifier()
        result.reduce_dim, \
        result.classifier, \
        result.n_components = pickle.load(open('{}/{}'.format(folder, filename), 'rb'))
        return result

def main():
    # example of using..
    from sklearn.random_projection import sparse_random_matrix
    from sklearn import metrics
    import random

    N_samples = 1000
    N_feats = 100
    N_class_feats = 5
    y_true = np.array([random.randint(a=0, b=1) for _ in range(N_samples)], dtype='float32')
    X_train = np.random.randint(2, size=(N_samples, N_feats))
    sparse_classifier = SparseClassifier(n_components=N_class_feats)
    sparse_classifier.fit(X_train, y_true)
    print ('Precision on train: {}'.format(metrics.accuracy_score(y_true, sparse_classifier.predict(X_train))))
    sparse_classifier.dump('model', 'sparse_classifier1.pkl')
    sparse_classifier2 = SparseClassifier.load('model', 'sparse_classifier1.pkl')
    print('[DUMP] Precision on train: {}'.format(metrics.accuracy_score(y_true, sparse_classifier2.predict(X_train))))


def predict(y_test, X_test, sparse_classifier, dump=False):
    from sklearn import metrics
    y_predict = sparse_classifier.predict(X_test)
    print('predict.len = ' + str(len(y_predict)))
    print('test.len = ' + str(len(y_test)))

    print('=======================')
    print('predict Y = ' + str(y_predict))
    print('test Y = ' + str(y_test))
    print('=======================')
    accuracy = metrics.accuracy_score(y_test, y_predict)
    f_meas = metrics.f1_score(y_test, y_predict)
    print('accuracy_score on train: {}'.format(accuracy))
    print('f1_score on train: {}'.format(f_meas))
    print('precision_score on train: {}'.format(metrics.precision_score(y_test, y_predict)))
    print('recall_score on train: {}'.format(metrics.recall_score(y_test, y_predict)))

    # dump model
    if dump:
        sparse_classifier.dump('model', 'model_{}.pkl'.format('acc-{0:.2f}'.format(accuracy) + '_fmeas-{0:.2f}'.format(f_meas)))
        print('model dumped')

def train_predict(X_MATRIX, y_true, N_class_feats):
    sparse_classifier = SparseClassifier(n_components=N_class_feats)

    range = int(len(y_true) * 0.75)

    X_train = X_MATRIX[:range]
    y_train = y_true[:range]

    X_test = X_MATRIX[range:]
    y_test = y_true[range:]

    sparse_classifier.fit(X_train, y_train)
    predict(y_test, X_test, sparse_classifier, dump=True)

def predict_on_created_model(X_MATRIX, y_true):
    # files = glob.glob('model/*.json')
    # sparse_classifier = SparseClassifier.load('model', 'model_acc-0.70_fmeas-0.42.pkl')
    # sparse_classifier = SparseClassifier.load('model', 'model_acc-0.71_fmeas-0.60.pkl')
    sparse_classifier = SparseClassifier.load('model', 'model_acc-0.72_fmeas-0.64.pkl')
    range = int(len(y_true) * 0.75)

    X_test = X_MATRIX[range:]
    y_test = y_true[range:]

    predict(y_test, X_test, sparse_classifier)

if __name__ == '__main__':
    main()