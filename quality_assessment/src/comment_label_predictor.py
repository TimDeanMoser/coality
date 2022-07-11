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
from quality_assessment.src.fasttext_label_predictor import FasttextLabelPredictor

"""
Entry point for predicting a string's label using the models provided. Prints prediction to console.
For a smooth performance, make sure that the root of the repository is the working directory when running the script and use absolute paths as the arguments.

Example:
    $ python predictor.py C:\\my_models "predict this text"
"""
import argparse
import logging
import os
import sys

from joblib import parallel_backend


class Predictor:
    """
    Contains functions and attributes for predicting a string's label using the models provided.

    Args:
        model_dir: Path to comment classification models directory.

    Attributes:
        classifiers: Holds all classifiers, one for each label.
    """
    def __init__(self, model_dir):
        # check path
        if not os.path.isdir(model_dir):
            print("The directory with the models does not exist.")
            exit()
        # load all models and instantiate classifiers
        self.classifiers = []
        for filename in os.listdir(model_dir):
            if filename.endswith(".model"):
                self.classifiers.append(FasttextLabelPredictor(os.path.join(model_dir, filename)))

    def predict(self, text, verbose):
        """
        Predicts label using models.
        Args:
            text: Text that one wants to predict the label of
            verbose: Argument if not only the predicted label should be returned, but also its probability.
        Returns: prediction with or without probability.
        """
        predictions = {}
        for classifier in self.classifiers:
            with parallel_backend('threading', n_jobs=-1):
                predictions[classifier.label] = classifier.predict(text)
        return predictions if verbose > 0 else (max(predictions, key=predictions.get), max(predictions.values()))


def main(models, text, verbose):
    """
    Main function to predict a label.
    """
    p = Predictor(models)
    return p.predict(text, verbose)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Predict the label of a string')

    parser.add_argument('models', metavar='Models', type=str,
                        help='Path to the directory containing the trained models.')
    parser.add_argument('text', metavar='Text', type=str,
                        help='Input text for prediction.')

    parser.add_argument("-v", "--verbose", type=int, help="Get the detailed results of the prediction.",
                        choices=[0, 1], default=0)
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
    print(main(args.models, args.text, args.verbose))
    exit()
