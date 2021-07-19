import logging
import os
import sys

from classifiers.fasttext_classifier import FasttextClassifier
from classifiers.random_forest_classifier import RFClassifier
from classifiers.naive_bayes_classifier import NBClassifier
from classifiers.logistic_regression_classifier import LRClassifier
from classifiers.j48_classifier import J48Classifier
from classifiers.lsvc_classifier import LSVCClassifier
import numpy as np
from joblib import parallel_backend
import argparse

MODELS = {
    'naive_bayes': NBClassifier
    ,
    'logistic_regression': LRClassifier
    ,
    'lsvc': LSVCClassifier
    ,
    'fasttext': FasttextClassifier
    ,
    'random_forest': RFClassifier
    ,
    'j48': J48Classifier
}


class Trainer:
    def __init__(self, d_in, model_init, oversampling, representation):
        self.classifiers = []
        self.data = d_in
        self.oversampling = oversampling

        print("Converting dataset to array")
        f = open(d_in, 'r+', encoding="UTF-8")
        data = np.array(f.readlines())
        f.close()

        labels = np.unique(np.array(list(map(lambda x: x.partition(' ')[0], data))))
        print("Parsed labels:", labels)
        for label in labels:
            if label == "__label__other":
                logging.error("The label '__label__other' cannot be used, please rename it.")
                exit()
            self.classifiers.append(model_init(label, d_in))
        self.classifiers = list(filter(lambda x: x.amount >= representation, self.classifiers))
        if len(self.classifiers) < 1:
            print("No label reached the minimum representation of " + str(representation))
            exit()

    def train(self, out):
        oversampling_target = max(classifier.amount for classifier in self.classifiers) if self.oversampling > 0 else -1
        for classifier in self.classifiers:
            classifier.create_train_dataset(-1, oversampling_target)
            with parallel_backend('threading', n_jobs=-1):
                classifier.train_model()
                classifier.save_model(out)


def main(data, output, oversampling, model, representation):
    if not os.path.isdir(output):
        logging.error("The output directory does not exist.")
        exit()
    model = MODELS[model]
    t = Trainer(data, model, oversampling, representation)
    t.train(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train a model on a data-set')
    parser.add_argument('data', metavar='Data', type=str,
                        help='Path to your data-set in fasttext format: Every line is a data entry formatted as '
                             '"__label__summary  this is a summary comment."')

    parser.add_argument('output', metavar='Output', type=str,
                        help='Models output directory path. Here your trained models are saved as bin files, one for '
                             'each label in the data-set. Must be an existing directory.')

    parser.add_argument("-os", "--oversampling", type=int, help="Oversample under represented labels [0, 1 (default)].",
                        choices=[0, 1], default=1)
    parser.add_argument("-m", "--model", type=str, help="Select which model implementation to use. Default is "
                                                        "Fasttext. [fasttext, "
                                                        "naive_bayes, logistic_regression, lsvc, random_forest, "
                                                        "j48]", choices=MODELS.keys(), default="fasttext")

    parser.add_argument("-r", "--representation", type=int,
                        help="The minimum representation of a label in the data-set. Default is 50.", default=50)
    levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }
    parser.add_argument("-log", "--log", default="info",
                        help=("Provide logging level. Example --log debug', default='info'"), choices=levels.keys())
    args = parser.parse_args()
    level = levels.get(args.log.lower())
    logging.basicConfig(format='%(asctime)s -%(levelname)s- [%(filename)s:%(lineno)d] \n \t %(message)s',
                        level=level, stream=sys.stdout)
    main(args.data, args.output, args.oversampling, args.model, args.representation)

    exit()
