"""
Entry point for predicting a string's label using the models provided. Prints prediction to console.
For a smooth performance, make sure that the root of the repository is the working directory when running the script and use absolute paths as the arguments.

Example:
    $ python predictor.py C:\\my_models "predict this text"
"""
import argparse
import logging
import os
import pickle
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
                with open(os.path.join(model_dir, filename), 'rb') as f:
                    p = pickle.load(f)
                    self.classifiers.append(p)

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
    parser = argparse.ArgumentParser(description='Train a model on a data-set')

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
