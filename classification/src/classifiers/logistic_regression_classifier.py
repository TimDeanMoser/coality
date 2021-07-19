from sklearn.linear_model import LogisticRegression
from classification.src.classifiers.scikit_classifier import *


class LRClassifier(ScikitClassifier):

    def __init__(self, label, data_set_path):
        super().__init__(label, data_set_path)

    def train_model(self):
        # train model here
        print("Fitting model for", self.label)
        self.model = LogisticRegression(random_state=0)
        self.model.fit(self.train_dataset[0], self.train_dataset[1])

    def predict(self, text):
        prediction = self.model.predict_proba(self.data_vectorizer.transform([text]).toarray())
        return prediction[0][1]
