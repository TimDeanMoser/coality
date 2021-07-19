"""
Evaluate the results of the rater class and generate a .json file from the analysis' result.
For a smooth performance, make sure that the root of the repository is the working directory when running the script and use absolute paths as the arguments.

Example:
    $ python comment_evaluator.py C:\\my_project output.json C:\\found_comments.csv C:\\missing_comments.csv -syn 0
"""
# import modules
import argparse
import logging
import os
import sys
from typing import Optional
import numpy as np
import pandas as pd
import ast
import simplejson as simplejson

DF_COLUMNS: list = ["type", "path", "position", "text", "code_language", "ignore", "matched_synonyms", "abbreviations",
                    "fkgls", "frel", "fi",
                    "is_english", "is_code", "is_too_short", "is_too_long", "N_matched_synonyms", "N_exclamation",
                    "N_question", "N_abbreviations", "is_trivial", "is_unrelated", "count", "count_missing", "label",
                    "label_proba", "handle"]
"""Holds all the columns the resulting dataframe and .json will contain"""

COLUMN_AGG: dict = {"fkgls": "mean", "frel": "mean", "fi": "mean",
                    "is_english": "sum", "is_code": "sum", "is_too_short": "sum", "is_too_long": "sum",
                    "N_matched_synonyms": "sum", "N_exclamation": "sum",
                    "N_question": "sum", "N_abbreviations": "sum", "is_trivial": "sum", "is_unrelated": "sum",
                    "count": "sum",
                    "count_missing": "sum"}
"""Defines which column should be aggregated how"""

VALID_EXTENSIONS = ('.java', '.cpp', '.c', '.cc', '.cs', '.h', ".hpp")
"""Defines which file extensions must be considered in the analysis"""


class CommentEvaluator:
    """
    Contains functions and attributes for evaluating a .csv generated by the rater class.

    Args:
        path: Path to project directory.
        comment_data: Path to .csv containing all found comments.
        missing_comment_data: Path to .csv containing all missing comments.

    Attributes:
        project_dir: Path to project directory.
        df: Main pandas dataframe that is used for calculations inside the class
    """

    def __init__(self, path: str, comment_data: str, missing_comment_data: str):
        # save path to project
        self.project_dir: str = path
        # read found comments
        df = pd.read_csv(comment_data)
        # set their count to 1
        df["count"] = 1
        # read missing comments
        df_missing = pd.read_csv(missing_comment_data)
        # label them as missing
        df_missing["count_missing"] = 1
        # label found comments as not missing
        df["count_missing"] = 0
        # join the two dataframes and save
        self.df: pd.DataFrame = pd.merge(df, df_missing, how='outer')

    def evaluate(self, output: str, syn: int):
        """
        Main function that analyzes the dataframe and generates the .json file

        Args:
            output: Path to project directory.
            syn: Enable synonym analysis (0 or 1). Not recommended for large projects
        """
        # create new columns with meta-data from the original csv's
        self.df["is_english"] = self.df.apply(lambda row: is_english(row), axis=1)
        self.df["is_too_short"] = self.df.apply(lambda row: is_too_short(row), axis=1)
        self.df["is_too_long"] = self.df.apply(lambda row: is_too_long(row), axis=1)
        self.df["is_trivial"] = self.df.apply(lambda row: is_too_long(row), axis=1)
        self.df["is_unrelated"] = self.df.apply(lambda row: is_too_long(row), axis=1)
        self.df["ignore"] = self.df.apply(lambda row: is_ignore(row), axis=1)
        # set certain cols to 'None' as they should not be considered when aggregating into sums/means
        self.nan_ignored_means()
        self.nan_ignored_sums()
        # evaluate the found synonyms
        self.evaluate_synonyms(syn)
        # drop any columns not needed
        self.df.drop(self.df.columns.difference(DF_COLUMNS), 1, inplace=True)
        # generate the results object
        result = self.path_to_dict(self.project_dir)
        # dump result as json to output file
        with open(output, 'w') as f:
            simplejson.dump(result, f, ignore_nan=True)

    def nan_ignored_means(self):
        """Helper Function to set all ignored row's meaned values to NaN to ignore them in the aggregation"""
        self.df.loc[self.df.ignore == True, 'fkgls'] = np.nan
        self.df.loc[self.df.ignore == True, 'frel'] = np.nan
        self.df.loc[self.df.ignore == True, 'fi'] = np.nan

    def nan_ignored_sums(self):
        """Helper Function to set all ignored row's summed values to NaN to ignore them in the aggregation"""
        self.df.loc[self.df.ignore == True, 'N_exclamation'] = np.nan
        self.df.loc[self.df.ignore == True, 'N_abbreviations'] = np.nan
        self.df.loc[self.df.ignore == True, 'N_question'] = np.nan

    def aggregate(self, path: str):
        """
        Helper function to aggregate all comments that are under a certain path
        Args:
            path: Path to aggregate under.

        Returns:
            Grouped and aggregated dataframe
        """
        # If a comment's path does not contain the agg_path it will be filtered
        agg_df = self.df[self.df["path"].str.contains(path, regex=False)]
        # return one big group that is aggregated appropriately
        return agg_df.groupby(lambda x: True).agg(COLUMN_AGG)

    def write_agg_values(self, d: dict, path: str):
        """
        Aggregates comments under path and appends values to dict d.
        Args:
            d: Dict to edit.
            path: Path to aggregate under.
        """
        agg_df = self.aggregate(path)
        for key in COLUMN_AGG.keys():
            value = get_value(agg_df, key)
            try:
                value = int(value)
            except:
                pass
            finally:
                d[key] = value

    def get_file_comments(self, path: str) -> list:
        """
        Helper function to fetch all comments that are in a certain file.
        Args:
            path: Path to file

        Returns:
            result: List of dicts containing the comments of a file
        """
        # filter comments not part of the file
        df = self.df[self.df["path"].str.contains(path, regex=False)]
        result = []
        # loop through filtered df and append all comments as dicts
        for index, row in df.iterrows():
            comment = {}
            for key in DF_COLUMNS:
                comment[key] = row[key]
            result.append(comment)
        return result

    def path_to_dict(self, path: str) -> Optional[dict]:
        """
        Recursive function to generate a dict mimicking the local directory structure of a project with all directories
        and files containing any comments. Comments contain all their data and Files/Directories the aggregated values
        of all comments in them
        Args:
            path: Path to get structure from

        Returns:
            d: Dictionary containing all (aggregated) data of comments/files/directories under path
        """
        # get filename
        d = {'name': os.path.basename(path)}
        # if path is a directory get all children recursively
        if os.path.isdir(path):
            d['structure'] = "directory"
            # aggregate all data under directory
            self.write_agg_values(d, path.replace("\\", "/"))
            d['children'] = []
            # list of all paths under directory
            paths = [os.path.join(path, x) for x in os.listdir(path)]
            # append all children containing at least one valid file
            for p in paths:
                # recursive call
                c = self.path_to_dict(p)
                if c is not None:
                    d['children'].append(c)
            if not d['children']:
                return None
        # path is a file
        else:
            # exit if not valid
            if not valid_file(path):
                return None
            d['structure'] = "file"
            # write aggregated values of all comments in file
            self.write_agg_values(d, path.replace("\\", "/"))
            # add comments' data as children of file
            d["comments"] = self.get_file_comments(path.replace("\\", "/"))
        return d

    def evaluate_synonyms(self, syn: int):
        """
        Evaluate the use of synonyms in a comment on a file scope.
        Take note if the synonym of a word in a comment is used in another comment in the same file.
        Due to its inherently high complexity it is not recommended to run this analysis on big projects.
        Args:
            syn: Flag for enabling this analysis (0 or 1)
        Returns:
            Adds the matched synonyms and tracks their count in the df of this class
        """
        self.df["matched_synonyms"] = self.df.apply(lambda x: [], axis=1)
        self.df["N_matched_synonyms"] = self.df.apply(lambda x: 0, axis=1)
        # escape if synonym analysis is disabled
        if syn == 0:
            return
        # group comments by file, since we want to look at matches in a file scope
        by_file = self.df.groupby('path')
        # for every file
        for file_name, group in by_file:
            # for every comment in file
            for row_index, row in group.iterrows():
                # disregard ignored comments for evaluation
                if row["ignore"]:
                    continue
                pos = row["position"]
                # get the synonyms
                dict = ast.literal_eval(row["synonyms"])
                res_syn = []
                N_syn = 0
                # for every word in comment
                for key in dict:
                    # compare to every other comments' words synonyms in file
                    for row_index2, row2 in group.iterrows():
                        # disregard ignored comments for lookup
                        if row2["ignore"]:
                            continue
                        pos2 = row2["position"]
                        dict2 = ast.literal_eval(row2["synonyms"])
                        # for every synonym in the look up comment
                        for key2 in dict2:
                            # original word in list of synonyms of another word in file
                            if key != key2 and key in dict2[key2]:
                                res_syn.append({
                                    'word': key,
                                    'synonym': key2,
                                    'pos_word': pos,
                                    'pos_synonym': pos2
                                })
                                # increment count
                                N_syn = N_syn + 1
                # write values to df
                self.df.at[row_index, "N_matched_synonyms"] = N_syn
                self.df.at[row_index, "matched_synonyms"] = res_syn
                logging.debug(row["N_matched_synonyms"], ":", row["matched_synonyms"])


def is_ignore(row) -> bool:
    """
    Helper function to determine if a comment should be ignored.
    Headers, commented code, non-english, too short and missing comments get ignored.
    Args:
        row: The row of the df to evaluate.

    Returns:
        True if ignored, False otherwise.
    """
    return row["type"] == "header" or row["is_code"] == 1 or row["is_english"] == 0 or row["is_too_short"] == 1 or row[
        "count_missing"] == 1


def is_english(row) -> int:
    """
        Helper function to determine if a comment is in english (probability > 0.75).
        Args:
            row: The row of the df to evaluate.

        Returns:
            1 if english, 0 otherwise.
    """
    return 0 if row["language"] != "en" or row["language_proba"] < 0.75 else 1


def is_too_short(row) -> int:
    """
        Helper function to determine if a comment is too short (N_words < 3).
        Args:
            row: The row of the df to evaluate.

        Returns:
            1 if too short, 0 otherwise.
    """
    return 1 if row["N_words"] < 3 else 0


def is_too_long(row) -> int:
    """
        Helper function to determine if an in-line comment is too long (N_words > 30).
        Args:
            row: The row of the df to evaluate.

        Returns:
            1 if too long, 0 otherwise.
    """
    return 1 if row["type"] == "in-line" and row["N_words"] > 30 else 0


def is_trivial(row) -> int:
    """
        Helper function to determine if a comment is trivial. A comment is trivial when its coherence coefficient is
        > 0.5 as it contains few extra information besides repeating the handle.
        Args:
            row: The row of the df to evaluate.

        Returns:
            1 if trivial, 0 otherwise.
    """
    return 1 if row["coherence_coefficient"] and row["coherence_coefficient"] > 0.5 else 0


def is_unrelated(row) -> int:
    """
        Helper function to determine if a comment is unrelated. A comment is unrelated when its coeherence coefficient
        is exactly 0, as the comment has no words in common with the handle.
        Args:
            row: The row of the df to evaluate.

        Returns:
            1 if unrelated, 0 otherwise.
    """
    return 1 if row["coherence_coefficient"] and row["coherence_coefficient"] == 0.0 else 0


def valid_file(path) -> bool:
    """
        Helper function to determine if a file has a valid extension.
        Args:
            path: The path of the file to validate.

        Returns:
            True if valid file, False otherwise.
    """
    return path.lower().endswith(VALID_EXTENSIONS)


def get_value(d, key):
    """
    Helper Function to get the value of a grouped dataframe with a key to a column.
    Args:
        d: DataFrame to get value from
        key: Key of value to get

    Returns:
        The value
    """
    return d[key].values[0] if len(d[key].values) > 0 else None


def main(project: str, output: str, comments: str, missing_comments: str, syn: int):
    """
    Evaluate the results of the rater class.

    Args:
        project: Path to directory of project to analyze.
        output: Path to output file.
        comments: Path to .csv with all found comments of the rater.
        missing_comments: Path to .csv with all missing comments found by the rater.
        syn: Flag for synonym analysis (0 or 1). Not recommended for big projects.

    Returns:
        Creates a .json file at the output location.
    """
    # check if project is a valid directory
    if not os.path.isdir(project):
        logging.error("The project directory does not exist.")
        exit()
    # instantiate evaluator
    c = CommentEvaluator(project, comments, missing_comments)
    # evaluate missing and found comments
    c.evaluate(output, syn)


if __name__ == '__main__':
    # mandatory arguments
    parser = argparse.ArgumentParser(description='Evaluate scraped comments and save the data as a .json')
    parser.add_argument('project', metavar='Project', type=str,
                        help='Path to the project directory to evaluate.')

    parser.add_argument('output', metavar='Output', type=str,
                        help='Path for the output .json file')

    parser.add_argument('comments', metavar='Comments', type=str,
                        help='Path to the scraped comments .csv')

    parser.add_argument('missing_comments', metavar='Comments', type=str,
                        help='Path to the scraped missing comments .csv')

    # optional arguments
    parser.add_argument("-syn", "--synonyms", type=int, help="Enable synonym analysis of comments in files. Not "
                                                             "recommended for big projects due to complexity. [0 ("
                                                             "default), 1].",
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

    # get and set logger level and format
    level = levels.get(args.log.lower())
    logging.basicConfig(format='%(asctime)s -%(levelname)s- [%(filename)s:%(lineno)d] \n \t %(message)s',
                        level=level, stream=sys.stdout)
    # run main function
    main(args.project.replace("\\", "/"), args.output, args.comments, args.missing_comments, args.synonyms)

    exit()
