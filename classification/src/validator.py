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
Entry point for validating a model on a data set in a k-fold loop. Creates a json file with the results and metrics.
For a smooth performance, make sure that the root of the repository is the working directory when running the script and use absolute paths as the arguments.

Example:
    $ python validator.py C:\\comment_data.txt C:\\result.json
"""
import argparse
import logging
import os.path
import sys

import numpy as np
from numpy import array
from sklearn.model_selection import KFold
import json
from datetime import datetime
from joblib import parallel_backend

from classifiers.fasttext_classifier import FasttextClassifier
from classifiers.random_forest_classifier import RFClassifier
from classifiers.naive_bayes_classifier import NBClassifier
from classifiers.logistic_regression_classifier import LRClassifier
from classifiers.j48_classifier import J48Classifier
from classifiers.lsvc_classifier import LSVCClassifier
from classification.src.classifiers.binary_classifier import calculate_metrics

models = {
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


def get_common_prediction(predictions):
    """
    Returns prediction with highest probability
    """
    return max(predictions, key=predictions.get)


def k_fold_validation(d_in, f_out, model_name, oversampling, kfolds, representation):
    """
    Main k-fold loop. Exports results to json file.
    Args:
        d_in: Path to comment data.
        f_out: Output file.
        model_name: Which model should be used for validation.
        oversampling: The oversampling target.
        kfolds: How many folds to loop.
        representation: Minimum representation of any label in the data set to be considered for training.
    """
    start_time = datetime.now()
    classifiers = []
    # read data
    f = open(d_in, 'r+', encoding="UTF-8")
    data = array(f.readlines())
    f.close()
    # get set of labels in data
    labels = np.unique(np.array(list(map(lambda x: x.partition(' ')[0], data))))
    # init classifiers for each label
    for label in labels:
        classifiers.append(models[model_name](label, d_in))

    # track fold count
    fold = 0
    # init Kfold
    kfold = KFold(kfolds, shuffle=True, random_state=1)
    # calculate oversampling target based on highest representation among labels and the number of folds
    # target = -1 disables oversampling
    oversampling_target = round(
        max(classifier.amount for classifier in classifiers) * ((kfolds - 1) / kfolds)) \
        if oversampling else -1
    # split data into parts for folds
    for train, test in kfold.split(data):
        print("New tenfold iteration:", str(fold), "-----------------------------------------")
        # get test data
        test_data = list(map(lambda x: (x.partition(' ')[0], x.partition(' ')[2]), data[test]))
        # get labels in test data
        tested_labels = np.unique(np.array(list(map(lambda x: (x[0]), test_data))))
        # create training data set
        for classifier in classifiers:
            classifier.create_train_dataset(train, oversampling_target)
            if classifier.label not in tested_labels:
                classifier.enabled = False

        # disable classifiers that are not part of test or training data set
        enabled_classifiers = list(filter(lambda x: x.enabled, classifiers))

        print("start training...")
        # create threads for training all classifiers
        for classifier in enabled_classifiers:
            with parallel_backend('threading', n_jobs=-1):
                classifier.train_model()
        print("start testing for tenfold iteration...")
        # predict on test data using trained models
        for i, line in enumerate(test_data):
            comment_text = test_data[i][1].replace('\n', '').replace('\r', '')
            correct_answer = test_data[i][0]
            predictions = {}
            # predict
            for classifier in enabled_classifiers:
                with parallel_backend('threading', n_jobs=-1):
                    predictions[classifier.label] = classifier.predict(comment_text)
            common_prediction = get_common_prediction(predictions)
            # check if prediction correct and record positives/negatives
            for classifier in enabled_classifiers:
                classifier.assess_result(common_prediction, correct_answer, fold)
        # calculate metrics
        for classifier in classifiers:
            classifier.get_benchmarks(fold)
        # increase fold
        fold += 1
    # filter based on too low representation
    relevant_classifiers = list(filter(lambda x: x.amount >= representation, classifiers))

    details = []
    agg_TP = 0
    agg_TP_FP = 0
    agg_TP_FN = 0
    # aggregate all positives/negatives of all folds
    for classifier in relevant_classifiers:
        agg_TP += sum(classifier.TP)
        agg_TP_FP += sum(classifier.TP_FP)
        agg_TP_FN += sum(classifier.TP_FN)
        details.append(classifier.__str__())
    # calculate aggregated metrics
    agg_recall, agg_precision, agg_f1 = calculate_metrics(agg_TP, agg_TP_FN, agg_TP_FP)
    end_time = datetime.now()
    # write results to json
    dump = {
        "Metadata": {
            "Model": model_name,
            "Data set": os.path.splitext(os.path.basename(d_in))[0],
            "Total data": len(data),
            "Total labels": len(labels),
            "Relevant labels": len(relevant_classifiers),
            "Minimum n for relevance": representation,
            "Start time": start_time.strftime("%d/%m/%Y, %H:%M:%S"),
            "Processing time in seconds": (end_time - start_time).total_seconds(),
            "K-Fold amount": kfolds,
            "Oversampling target": oversampling_target
        },
        "Results": {
            "Aggregated Metrics over all labels": {
                "Recall": agg_recall,
                "Precision": agg_precision,
                "F1": agg_f1,
            }},
        "Details": details
    }
    # export to file
    o = open(f_out, 'w+', encoding='UTF-8')
    o.write(json.dumps(dump, indent=4))
    o.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='10 fold validate from data-set')

    parser.add_argument('data', metavar='Data', type=str,
                        help='Path to your data-set in fasttext format: Every line is a data entry formatted as '
                             '"__label__summary  this is a summary comment."')
    parser.add_argument('output', metavar='Output', type=str,
                        help='Path to the outputted results file.')

    parser.add_argument("-os", "--oversampling", type=int, help="Oversample under represented labels [0, 1 (default)].",
                        choices=[0, 1], default=1)
    parser.add_argument("-m", "--model", type=str, help="Select which model implementation to use. [fasttext, "
                                                        "naive_bayes, logistic_regression, lsvc, random_forest, "
                                                        "j48]", choices=models.keys(), default="fasttext")

    parser.add_argument("-r", "--representation", type=int,
                        help="The minimum representation of a label in the data-set. Default is 50.", default=50)

    parser.add_argument("-k", "--kfolds", type=int,
                        help="The amount of folds in the k-fold validation. Default is 10.", default=10)
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
    k_fold_validation(args.data, args.output, args.model, args.oversampling > 0, args.kfolds, args.representation)
    exit()
