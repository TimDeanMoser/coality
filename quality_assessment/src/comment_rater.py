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
Scrape a project directory for comments and rate their contents/data. Creates a .csv file for found comments and one for missing comments.
For a smooth performance, make sure that the root of the repository is the working directory when running the script and use absolute paths as the arguments.

Example:
    $ python comment_rater.py C:\\my_project comments.csv C:\\my_models -log warning
"""

import argparse
import csv
import datetime
import logging
import os
import re
import sys
import fasttext
from Levenshtein import distance as levenshtein_distance
from stemming.porter2 import stem

sys.path.append('classification/src/classifiers')
sys.path.append('classification/src/')

from quality_assessment.src.comment_scraper import CommentScraper
from quality_assessment.src.comment_exporter import CommentExporter
from quality_assessment.src.tokenizer import Tokenizer
from classification.src.predictor import Predictor
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords


class Rater:
    """
    Contains functions and attributes for rating all comments in a directory and generates 2 output .csv files

    Args:
        models: Path to comment classification models directory.

    Attributes:
        abbreviations: Detected abbreviations.
        tokenizer: Tokenizer instance for NLP.
        language_model: Fasttext Model for classifying natural language (e.g. english).
        sw: Set of Stopwords for SWR.
        predictor: Predictor instance for comment label classification.
    """

    def __init__(self, models: str):
        self.abbreviations = {}
        # read abbreviations list and save in a more accessible format
        reader = csv.reader(
            open(r'quality_assessment\data\abbreviations.csv', 'r'))
        for row in reader:
            self.abbreviations[row[0]] = row[1]
        self.tokenizer = None
        # load the natural language classification model
        self.language_model = fasttext.load_model(r'quality_assessment/data/lid.176.ftz')
        # save stopwords as a set
        self.sw = set(stopwords.words('english'))
        # instantiate predictor with the given models
        self.predictor = Predictor(models)

    def rate(self, comments: list):
        """
        Rate comments and write values into comment objects.

        Args:
            comments: list of comment objects to rate.
        """
        # iterate over all comments
        for comment in comments:
            # save start_time for calculating processing time later
            start_time = datetime.datetime.now()
            # set abbreviations as the intersection of the words and the abbreviation set
            comment.abbreviations = set(re.split(r"\s+", comment.text)).intersection(self.abbreviations.keys())
            # preprocess comment
            preprocess(comment)
            # predict label of comment
            t = self.predictor.predict(comment.processed_text, 0)
            # write label and probability
            comment.label = t[0]
            comment.label_probability = t[1]
            # count question and exclamation marks in text
            comment.question_marks = comment.text.count("?")
            comment.exclamation_marks = comment.text.count("!")
            # instantiate a tokenizer and get the stats
            self.tokenizer = Tokenizer()
            self.tokenizer.get_stats(comment)
            # get readability metrics
            comment.coherence_coefficient = get_coherence_coefficient(comment.words, comment.handle)
            comment.fog_index = self.get_fog_index()
            comment.flesch_kincaid_grade_level = self.get_flesch_kincaid_grade_level()
            comment.flesch_reading_ease_level = self.get_flesch_reading_ease_level()
            comment.language = self.get_language(comment.processed_text)
            comment.unique_words_swr = self.get_unique_words_swr()
            comment.synonyms = get_synonyms(comment.unique_words_swr)
            comment.is_code = is_commented_code(comment)
            # calculate and write processing time in milliseconds
            comment.time_millis = (datetime.datetime.now() - start_time).total_seconds() * 1000

    def get_flesch_kincaid_grade_level(self) -> float:
        """
        Calculates the Flesch-Kincaid grade level, which returns a U.S. grade school level of difficulty to read.
        A 8.0 means that the document can be understood by an eighth grader.
        A score of 7.0 to 8.0 is considered to be optimal.

        (11.8 * syllables_per_word) + (0.39 * words_per_sentence) - 15.59

        Returns: Flesch-Kincaid grade level score.
        """
        syl = self.tokenizer.syllables
        sen = self.tokenizer.sentences
        words = self.tokenizer.words
        return 0 if len(sen) == 0 or len(words) == 0 else (11.8 * (len(syl) / len(words))) + (
                0.39 * (len(words) / len(sen))) - 15.59

    def get_flesch_reading_ease_level(self) -> float:
        """
        Calculates the Flesch reading ease test rates text on a 100 point scale.
        The higher the score, the easier it is to understand the text.
        A score of 60 to 70 is considered to be optimal.

        206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)
        Returns: Flesch reading ease level.
        """
        syl = self.tokenizer.syllables
        sen = self.tokenizer.sentences
        words = self.tokenizer.words
        return 0 if len(sen) == 0 or len(words) == 0 else 206.835 - (1.015 * (len(words) / len(sen))) - (
                84.6 * len(syl) / len(words))

    def get_fog_index(self) -> float:
        """
        Calculates the Fog Index, which indicates the number of years of formal education a reader .
        would need to understand the text on the first reading.

        ( words_per_sentence + percent_complex_words ) * 0.4

        Returns: Fog Index.
        """
        sen = self.tokenizer.sentences
        words = self.tokenizer.words
        com = self.tokenizer.complex_words
        return 0 if len(sen) == 0 or len(words) == 0 else ((len(words) / len(sen)) + (
                (len(com) / len(words)) * 100)) * 0.41

    def get_language(self, text: str) -> tuple:
        """
        Helper function to predict natural language of text.

        Args:
            text: Text of comment to evaluate.

        Returns:
            tuple of ('language', 'probability').

        """
        prediction = self.language_model.predict(text)
        return prediction[0][0].split('__label__')[1], prediction[1][0]

    def get_unique_words_swr(self):
        """
        Helper function to create a list of unique words without stopwords for the synonym analysis.

        Returns: List of unique words in comment minus stopwords.
        """
        unique = list(set(self.tokenizer.words))
        return [w for w in unique if w not in self.sw]


def get_synonyms(words: list) -> dict:
    """
    Creates a list of synonyms for each word in a list of words using wordnet.

    Args:
        words: List of words to evaluate.

    Returns:
        Dict with words as keys and synonyms list as value.
    """
    res = {}
    for word in words:
        synets = wn.synsets(word)
        tmp = []
        for synset in synets:
            for w in synset.lemma_names():
                if "_" not in w and word != w and w not in tmp and stem(w) != stem(word):
                    tmp.append(w)
        res[word] = tmp
    return res


def remove_abbreviations(comment) -> str:
    """
    Helper function for stripping abbreviations from a comment's text.

    Args:
        comment: Comment object to strip abbreviations from.

    Returns: Resulting text.
    """
    return " ".join(list(filter(lambda word: word not in comment.abbreviations, re.split(r"\s+", comment.text))))


def remove_numbers(body: str) -> str:
    """
    Helper function for stripping numbers from a text.

    Args:
        body: String to strip numbers from.

    Returns: Resulting text.
    """
    return re.sub(r"\d", "", body)


def remove_special_characters(body: str) -> str:
    """
    Helper function for stripping special characters from a text.
    Those include: -$%^&*()_+|~=`{}[]";'<>/

    Args:
        body: String to strip special characters from.

    Returns: Resulting text.
    """
    return re.sub(r"[\-$%^&*()_+|~=`{}\[\]\";'<>\/]", " ", body)


def split_camel_case(body: str) -> str:
    """
    Helper function for splitting any camel case in a text

    Args:
        body: String to split the camel case in.

    Returns: Resulting text.
    """
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', body)


def split_function_call(body: str) -> str:
    """
    Helper function for splitting any function calls in a text (e.g. 'comment.evaluate' -> 'comment evaluate')

    Args:
        body: String to split the function calls in.

    Returns: Resulting text.
    """
    return re.sub(r'(\w)\.(?=\w)', r'\1 ', body)


def remove_multiple_spaces(body: str) -> str:
    """
    Helper function for removing multiple whitespaces/newlines in a text (e.g. 'comment    evaluate' -> 'comment evaluate')

    Args:
        body: String to remove multiple whitespaces/newlines in.

    Returns: Resulting text.
    """
    return re.sub(r'\s\s+', " ", body).strip()


def preprocess(comment):
    """
    Helper function for combining all preprocessing functions and write it into preprocessed_text of the comment

    Args:
        comment: comment to preprocess

    """
    comment.processed_text = remove_abbreviations(comment)
    comment.processed_text = comment.processed_text.replace("\n", " ")
    comment.processed_text = split_function_call(comment.processed_text)
    comment.processed_text = split_camel_case(comment.processed_text)
    comment.processed_text = remove_numbers(comment.processed_text)
    comment.processed_text = remove_special_characters(comment.processed_text)
    comment.processed_text = remove_multiple_spaces(comment.processed_text)


def get_coherence_coefficient(words: list, look_up: str):
    """
    Helper function for calculating the coherence coefficient between a list of words and a comment's handle.
    A cc of 0 means a comment is unrelated to its handle and a cc > 0.5 means it is too trivial.

    Args:
        words: list of words of a comment
        look_up: text for comparison
    Returns:

    """
    # do not calculate if words or look_up are empty/non-existent/zero
    if look_up == None or look_up == "" or words == None or len(words) == 0:
        return None
    similar_words = 0
    # most handles are written in camel case, so we need to split it up
    split_look_up = split_camel_case(look_up).lower().split()
    # all words to lower case for comparison
    split_words = map(lambda x: x.lower(), words)
    # calculate coherence coefficient
    for word in split_words:
        for check in split_look_up:
            if levenshtein_distance(word, check) < 2:
                similar_words += 1
    return similar_words / len(words)


def is_commented_code(comment) -> int:
    """
    Helper function for determining if a comment might be commented code.
    It does this by trying to match the symbols [=+&|;].
    When more than three matches are found, the comment might be commented code.

    Args:
        comment: Comment object to evaluate

    Returns:
        Flag if the comment might be commented code (0 or 1)
    """
    matchers = "=+&|;"
    res = 0
    for m in set(matchers):
        res += comment.text.count(m)
    if res > 3:
        return 1
    return 0


def main(project: str, output: str, models: str):
    """
    Scrape a project directory for comments and rate their contents/data.

    Args:
        project: Path to directory of project to analyze.
        output: Path to output file.
        models: Path to directory containing the comment classification models.

    Returns:
        Creates a .csv file at the output location with the data of all found comments and one .csv.missing file with
        the missing comments' data.
    """

    # import and update/download the wordnet data
    import nltk
    nltk.download('wordnet')
    # check if project is a proper directory
    if not os.path.isdir(project):
        logging.error("The project directory does not exist.")
        exit()
    # check if models is a proper directory
    if not os.path.isdir(models):
        logging.error("The models directory does not exist.")
        exit()

    # instantiate Objects
    r = Rater(models)
    s = CommentScraper()
    e = CommentExporter()
    # fetch found and missing comments with the Scraper class
    all_comments = s.get_directory_comments(project)
    comments = all_comments["comments"]
    missing_comments = all_comments["missing_comments"]
    # rate the found comments with the Rater class
    r.rate(comments)
    # Export the missing and found comments with the Exporter class
    e.export_comments(comments, output)
    # Get filename for missing comments
    res_path, res_filename = os.path.split(output)
    res_filename = os.path.splitext(res_filename)[0]
    missing_filename = '%s_missing.csv' % res_filename
    missing_file_path = os.path.join(res_path, missing_filename)
    e.export_missing_comments(missing_comments, missing_file_path)


if __name__ == '__main__':
    # mandatory arguments
    parser = argparse.ArgumentParser(description='Scrape a project for comments and export data as a .csv')
    parser.add_argument('project', metavar='Project', type=str,
                        help='Path to the project directory to scrape for comments.')

    parser.add_argument('output', metavar='Output', type=str,
                        help='Path for the output .csv file')

    parser.add_argument('models', metavar='Models', type=str,
                        help='Path to the directory of the trained models for comment type classification.')
    # optional arguments
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
    # get and set logger level and format
    level = levels.get(args.log.lower())
    logging.basicConfig(format='%(asctime)s -%(levelname)s- [%(filename)s:%(lineno)d] \n \t %(message)s',
                        level=level, stream=sys.stdout)
    # run main() function
    main(args.project, args.output, args.models)

    exit()
