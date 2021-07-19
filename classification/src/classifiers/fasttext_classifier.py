import pickle

import fasttext
fasttext.FastText.eprint = lambda x: None

from classification.src.classifiers.binary_classifier import *

HOME = os.path.dirname(__file__)
labels = {
    "summary": "__label__summary",
    "expand": "__label__expand",
    "rational": "__label__rational",
    "usage": "__label__usage",
    "warning": "__label__warning"
}


class FasttextClassifier(BinaryClassifier):

    def __init__(self, label, data_set_path):
        self.train_path = os.path.normpath(os.path.join(HOME, '../tmp/' + label + '_tmp_train.txt'))
        super().__init__(label, data_set_path)

    def create_train_dataset(self, i_train, oversampling_target):
        print("Creating " + self.label + " tmp train file")
        tmp_train = open(self.train_path, "w+", encoding="UTF-8")
        if type(i_train) is np.ndarray:
            matches = [s for s in self.data_array[i_train] if self.label in s.split(" ")[0]]
            others = [s for s in self.data_array[i_train] if "__label__other" in s.split(" ")[0]]
        else:
            matches = [s for s in self.data_array if self.label in s.split(" ")[0]]
            others = [s for s in self.data_array if "__label__other" in s.split(" ")[0]]

        # Oversample matches to reach target
        matches = oversample(matches, oversampling_target)
        joined = list(matches) + list(others)

        for line in joined:
            tmp_train.write("".join(line))
        tmp_train.close()

    def train_model(self):
        self.model = fasttext.train_supervised(input=self.train_path)

    def predict(self, text):
        if type(self.model) == bytes:
            self.load_model()
        p = self.model.predict(text, k=-1)
        labels = p[0]
        j = 0
        if labels[0] == '__label__other':
            j = 1
        return p[1][j]

    def save_model(self, f):
        path = os.path.join(f, self.label + ".model")
        self.model.save_model(path)
        with open(path, mode='rb') as file:
            self.model = file.read()
        os.remove(path)
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    def load_model(self):
        with open('ft.tmp', mode='wb') as file:
            file.write(self.model)
        self.model = fasttext.load_model('ft.tmp')
        os.remove('ft.tmp')

