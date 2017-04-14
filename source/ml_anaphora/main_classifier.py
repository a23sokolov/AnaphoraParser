# -*- coding: utf-8 -*-
from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.ensemble import RandomForestClassifier
import _pickle as pickle
import numpy as np
from sklearn import preprocessing

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

    def dump(self, folder):
        pickle.dump((self.reduce_dim, self.classifier, self.n_components),
                    open('{}/sparse_classifier.pkl'.format(folder), 'wb'))

    @staticmethod
    def load(folder):
        result = SparseClassifier()
        result.reduce_dim, \
        result.classifier, \
        result.n_components = pickle.load(open('{}/sparse_classifier.pkl'.format(folder)))
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
    sparse_classifier.dump('./')
    # sparse_classifier2 = SparseClassifier.load(u'.')

def simple_check(X_MATRRIX, y_true, N_class_feats):
    from sklearn import metrics
    sparse_classifier = SparseClassifier(n_components=N_class_feats)

    range = int(len(y_true) * 0.75)

    X_train = X_MATRRIX[:range]
    y_train = y_true[:range]

    X_test = X_MATRRIX[range:]
    y_test = y_true[range:]

    sparse_classifier.fit(X_train, y_train)
    y_predict = sparse_classifier.predict(X_test)
    print('X_MATRRIX.height = ' + str(len(X_MATRRIX)))
    print('predict.len = ' + str(len(y_predict)))
    print('test.len = ' + str(len(y_test)))

    print('=======================')
    print('predict Y = ' + str(y_predict))
    print('test Y = ' + str(y_test))
    print('=======================')
    print('accuracy_score on train: {}'.format(metrics.accuracy_score(y_test, y_predict)))
    print ('f1_score on train: {}'.format(metrics.f1_score(y_test, y_predict)))
    print('precision_score on train: {}'.format(metrics.precision_score(y_test, y_predict)))

if __name__ == '__main__':
    main()