"""
Copyright (c) 2021 Tim Moser.

This file is part of coality
(see https://github.com/TimDeanMoser/coality).

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

"""
Entry point for training a set of binary classification models on a data set. Creates one .model file for each label represented in the data.
For a smooth performance, make sure that the root of the repository is the working directory when running the script and use absolute paths as the arguments.

Example:
    $ python trainer.py C:\\comment_data.txt C:\\my_models
"""
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
"""Dictionary of all implemented Classifiers' constructors"""


class Trainer:
    """
    Contains functions and attributes for training a set of binary classification models on a data set.

    Args:
        d_in: Path to comment data in fasttext format.
        model_init: constructor for the desired classifier
        oversampling: Argument if oversampling should be applied
        representation: Minimum representation of any label in the data set to be considered for training.
    """
    def __init__(self, d_in, model_init, oversampling, representation):
        self.classifiers = []
        self.data = d_in
        self.oversampling = oversampling

        # read data into array
        print("Converting dataset to array")
        f = open(d_in, 'r+', encoding="UTF-8")
        data = np.array(f.readlines())
        f.close()
        # get set of labels represented in data
        labels = np.unique(np.array(list(map(lambda x: x.partition(' ')[0], data))))
        print("Parsed labels:", labels)
        for label in labels:
            # label "__label__other" is reserved for non-matches in the binary data set.
            if label == "__label__other":
                logging.error("The label '__label__other' cannot be used, please rename it.")
                exit()
            # init classifier for each label
            self.classifiers.append(model_init(label, d_in))
        # filter if too small representation
        self.classifiers = list(filter(lambda x: x.amount >= representation, self.classifiers))
        # error if no classifiers remain after filter
        if len(self.classifiers) < 1:
            print("No label reached the minimum representation of " + str(representation))
            exit()

    def train(self, out):
        """
        Oversample and train. Export models to directory.
        """
        oversampling_target = max(classifier.amount for classifier in self.classifiers) if self.oversampling > 0 else -1
        for classifier in self.classifiers:
            classifier.create_train_dataset(-1, oversampling_target)
            with parallel_backend('threading', n_jobs=-1):
                classifier.train_model()
                classifier.save_model(out)


def main(data, output, oversampling, model, representation):
    """
    Main function for training.
    """
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
