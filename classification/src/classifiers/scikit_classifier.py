import pickle

from classification.src.classifiers.binary_classifier import *
from sklearn.feature_extraction.text import TfidfVectorizer


class ScikitClassifier(BinaryClassifier):

    def __init__(self, label, data_set_path):
        self.train_dataset = None
        # TODO ask which values for max_features=1000
        self.data_vectorizer = TfidfVectorizer(max_features=1000, min_df=1, max_df=1.0)
        super().__init__(label, data_set_path)

    def create_train_dataset(self, i_train, oversampling_target):
        print("Creating " + self.label + " train dataset")

        if i_train >= 0:
            matches = [s for s in self.data_array[i_train] if self.label in s.split(" ")[0]]
            others = [s for s in self.data_array[i_train] if "__label__other" in s.split(" ")[0]]
        else:
            matches = [s for s in self.data_array if self.label in s.split(" ")[0]]
            others = [s for s in self.data_array if "__label__other" in s.split(" ")[0]]

        matches = oversample(matches, oversampling_target)

        x = list(matches) + list(others)
        y = [1] * len(matches) + [0] * len(others)

        x = self.data_vectorizer.fit_transform(x).toarray()
        self.train_dataset = (x, y)

    def train_model(self):
        raise Exception("Implementation missing")
        pass

    def predict(self, text):
        raise Exception("Implementation missing")
        pass

    def save_model(self, f):
        path = os.path.join(f, self.label + ".model")
        with open(path, 'wb') as f:
            pickle.dump(self, f)
