import os
import os.path
import numpy as np
from numpy import array
import re
from statistics import mean

MINIMUM_AMOUNT = 50


def oversample(matches, oversampling_target):
    return np.random.choice(matches, oversampling_target) if oversampling_target > 0 else matches


# returns consensus of multiple models' predictions
def get_common_prediction(predictions):
    r = {}
    for prediction in predictions:
        r[prediction[0]] = prediction[1]
    return max(r, key=r.get)


def calculate_metrics(tp, tp_fn, tp_fp):
    if tp_fp == 0:
        # no positives
        recall, precision, f1 = 0, 0, 0
    elif tp_fn == 0:
        # no TP n FN
        recall, precision, f1 = 0, 0, 0
    else:
        recall = tp / tp_fn
        precision = tp / tp_fp
        if precision + recall == 0:
            f1 = 0
        else:
            f1 = 2 * ((precision * recall) / (precision + recall))
    return recall, precision, f1


class BinaryClassifier:

    def __init__(self, label, data_set_path):
        self.amount = 0
        self.enabled = False
        self.label = label
        self.data_set_path = data_set_path
        self.binary_data_set_path = self.create_binary_data_set()
        self.data_array = self.text2array()
        self.model = None
        self.TP = [0] * 100
        self.TP_FN = [0] * 100
        self.TP_FP = [0] * 100
        self.recall = [0] * 100
        self.precision = [0] * 100
        self.f1 = [0] * 100
        self.metrics = []

    def __str__(self):

        recall, precision, f1 = calculate_metrics(sum(self.TP), sum(self.TP_FN), sum(self.TP_FP))
        res = {
            "label": self.label,
            "k-fold averages": {
                "recall": recall,
                "precision": precision,
                "f1": f1,
            },
            "k-fold details": self.metrics
        }
        return res

    def text2array(self):
        print("Converting " + self.label + " binary data set to array")
        f = open(self.binary_data_set_path, 'r+', encoding="UTF-8")
        a = array(f.readlines())
        f.close()
        return a

    def create_train_dataset(self, i_train, oversampling_target):
        raise Exception("Implementation missing")
        pass

    def train_model(self):
        raise Exception("Implementation missing")
        pass

    def save_model(self, f):
        raise Exception("Implementation missing")
        pass

    def predict(self, text):
        raise Exception("Implementation missing")
        pass

    def assess_result(self, common_prediction, correct_answer, fold):
        if common_prediction == self.label:
            self.TP_FP[fold] += 1
            if common_prediction == correct_answer:
                self.TP[fold] += 1
        if correct_answer == self.label:
            self.TP_FN[fold] += 1

    def get_benchmarks(self, fold):
        # edge cases by definition
        recall, precision, f1 = calculate_metrics(self.TP[fold], self.TP_FN[fold], self.TP_FP[fold])

        self.metrics.append(
            {
                "10-fold iteration": fold,
                "recall": recall,
                "precision": precision,
                "f1": f1,
                "TP": self.TP[fold],
                "TP_FN": self.TP_FN[fold],
                "TP_FP": self.TP_FP[fold],
            }
        )
        self.recall.append(recall)
        self.precision.append(precision)
        self.f1.append(f1)
        # print(self.label, ": r=", recall, ", p=", precision, ", f1=", f1)
        return recall, precision, f1

    def match_label(self, comment):
        prefix_pattern = re.compile(r'__label__\w+')
        match = prefix_pattern.match(comment)
        prefix_ind = match.span()
        prefix = comment[prefix_ind[0]:prefix_ind[1]]
        postfix = comment[prefix_ind[1]:]

        if prefix == self.label:
            new_prefix = self.label
            self.amount += 1
        else:
            new_prefix = '__label__other'
        return new_prefix + postfix

    def create_binary_data_set(self):
        dir_out = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + "/data/binary_data_sets/"
        data_set_name = os.path.splitext(os.path.basename(self.data_set_path))[0]
        binary_data_set_path = dir_out + self.label + '_' + data_set_name + '_binary.txt'
        binary_data_set = open(binary_data_set_path, mode='w+', encoding="UTF-8")

        with open(self.data_set_path, mode='r', encoding="UTF-8") as f:
            for comment in f:
                data_point = self.match_label(comment)
                binary_data_set.write(data_point)
        binary_data_set.close()
        if self.amount >= MINIMUM_AMOUNT:
            self.enabled = True
        return binary_data_set_path
