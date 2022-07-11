"""
Fasttext binary classifier, overrides functions that differ between different classifiers
"""
import os

import fasttext

# don't print fasttext's warnings
fasttext.FastText.eprint = lambda x: None

# labels = {
#     "summary": "__label__summary",
#     "expand": "__label__expand",
#     "rational": "__label__rational",
#     "usage": "__label__usage",
#     "warning": "__label__warning"
# }


def get_common_prediction(predictions):
    """
    Calculates the consensus of all the models' predictions
    Args:
        predictions: the list containing all predictions
    Returns:
        The consensus of all the models' predictions
    """
    r = {}
    for prediction in predictions:
        r[prediction[0]] = prediction[1]
    return max(r, key=r.get)


class FasttextLabelPredictor:

    def __init__(self, model_path):
        self.label = os.path.basename(model_path).split('.')[0]
        self.model = fasttext.load_model(model_path)

    def predict(self, text):
        """
        Predicts the label and probability of a string being of the dedicated label
        """
        # predict
        p = self.model.predict(text, k=-1)
        labels = p[0]
        j = 0
        if labels[0] == '__label__other':
            j = 1
        # return prediction
        return p[1][j]


