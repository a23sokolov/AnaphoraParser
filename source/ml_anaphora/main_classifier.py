from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import RandomForestClassifier
from sklearn.random_projection import sparse_random_matrix
from sklearn import preprocessing, metrics

import random
import numpy as np

N_samples = 1000
N_feats = 100
N_class_feats = 5



y_true = np.array([random.randint(a=0, b=1) for i in range(N_samples)], dtype='float32')
X_train = sparse_random_matrix(N_samples, N_feats, density=0.01, random_state=42)
#print(X_train.todense().tolist())
#print(X_train)
svd = TruncatedSVD(n_components=N_class_feats, n_iter=7, random_state=42)
X_train = preprocessing.scale(svd.fit_transform(X_train))
# print(X_train)

classifier = RandomForestClassifier(n_estimators=10)
classifier.fit(X_train, y_true)

y_pred = classifier.predict(X_train)
print(y_pred)
# print(metrics.accuracy_score(y_true, y_pred))
print(metrics.f1_score(y_true, y_pred))


X_test = sparse_random_matrix(10, N_feats, density=0.01, random_state=42)
y_test = classifier.predict(preprocessing.scale(svd.fit_transform(X_test)))

# print(y_test)
