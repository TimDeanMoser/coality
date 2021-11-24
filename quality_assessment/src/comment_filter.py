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
Filter scraped comments from the rater class by code language and comment label. Creates a .csv file for filtered comments.
For a smooth performance, make sure that the root of the repository is the working directory when running the script and use absolute paths as the arguments.

Example:
    $ python comment_filter.py filtered_comments.csv comments.csv -label summary
"""

import argparse
import logging
import sys
import pandas as pd

class CommentFilter:
    """
    Contains functions and attributes for filtering a .csv generated by the rater class.

    Args:
        comment_data: Path to .csv containing all found comments.

    Attributes:
        df: Main pandas dataframe that is used for calculations inside the class.
    """

    def __init__(self, comment_data: str):
        # save found comments as dataframe
        self.df = pd.read_csv(comment_data)

    def filter(self, language: str, label: str):
        """
        Filter found comments by code language and comment label.

        Args:
            language: Code language of files.
            label: Comment label (summary, usage, rationale, expand, warning).
        """
        if language:
            self.df = self.df.loc[self.df['code_language'] == language]
        if label:
            self.df = self.df.loc[self.df['label'] == label]
        
def main(output: str, comments: str, language: str, label: str):
    """
    Filter the results of the rater class.

    Args:
        output: Path to output file.
        comments: Path to .csv with all found comments of the rater.
        language: Code language of files.
        label: Comment label (summary, usage, rationale, expand, warning).

    Returns:
        Creates a .csv file at the output location with the data of resulting comments.
    """
    f = CommentFilter(comments)
    f.filter(language, label)
    f.df.to_csv(output, index=False)

if __name__ == '__main__':
    # mandatory arguments
    parser = argparse.ArgumentParser(description='Filter scraped comments and export data as a .csv')

    parser.add_argument('output', metavar='Output', type=str,
                        help='Path for the output .csv file')
    
    parser.add_argument('comments', metavar='Comments', type=str,
                        help='Path to the scraped comments .csv')

    # optional arguments
    labels = {
        'summary': "__label__summary",
        'expand': "__label__expand",
        'usage': "__label__usage",
        'rationale': "__label__rational",
        'warning': "__label__warning",
        'any': ""
    }
    parser.add_argument("-label", "--label", default="any", help=("Filter by comment type. Example --label summary, default='any'"), choices=labels.keys())
    languages = {
        'c': "C",
        'c++': "C++",
        'c#': "C#",
        'java': "Java",
        'any': ""
    }
    parser.add_argument("-lang", "--language", default="any", help=("Filter by code language. Example --language c++, default='any'"), choices=languages.keys())
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
    main(args.output, args.comments, languages[args.language], labels[args.label])

    exit()