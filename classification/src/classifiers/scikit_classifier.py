"""
All scikit-learn classifiers must inherit from this one, as they depend on a vectorization
"""
import pickle

from classification.src.classifiers.binary_classifier import *
from sklearn.feature_extraction.text import TfidfVectorizer


class ScikitClassifier(BinaryClassifier):

    def __init__(self, label, data_set_path):
        # init with vectorizer
        self.train_dataset = None
        self.data_vectorizer = TfidfVectorizer(max_features=1000, min_df=1, max_df=1.0)
        super().__init__(label, data_set_path)

    def create_train_dataset(self, i_train, oversampling_target):
        # sample training data set of fold
        print("Creating " + self.label + " train dataset")
        if i_train >= 0:
            matches = [s for s in self.data_array[i_train] if self.label in s.split(" ")[0]]
            others = [s for s in self.data_array[i_train] if "__label__other" in s.split(" ")[0]]
        else:
            matches = [s for s in self.data_array if self.label in s.split(" ")[0]]
            others = [s for s in self.data_array if "__label__other" in s.split(" ")[0]]
        # over sample
        matches = oversample(matches, oversampling_target)
        # format training data
        x = list(matches) + list(others)
        y = [1] * len(matches) + [0] * len(others)

        x = self.data_vectorizer.fit_transform(x).toarray()
        # write training data
        self.train_dataset = (x, y)

    def save_model(self, f):
        """
        save model with pickle
        """
        path = os.path.join(f, self.label + ".model")
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    #
    # functions to be overridden by sub classes
    #

    def train_model(self):
        raise Exception("Implementation missing")
        pass

    def predict(self, text):
        raise Exception("Implementation missing")
        pass
