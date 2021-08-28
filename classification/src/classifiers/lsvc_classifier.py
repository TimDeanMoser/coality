"""
Linear svc scikit learn classifier and its train and predict implementations
"""
from sklearn.svm import LinearSVC
from classification.src.classifiers.scikit_classifier import *


class LSVCClassifier(ScikitClassifier):

    def __init__(self, label, data_set_path):
        super().__init__(label, data_set_path)

    def train_model(self):
        # train model here
        print("Fitting model for", self.label)
        self.model = LinearSVC()
        self.model.fit(self.train_dataset[0], self.train_dataset[1])

    def predict(self, text):
        prediction = self.model.decision_function(self.data_vectorizer.transform([text]).toarray())
        return prediction[0]

