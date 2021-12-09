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
This file parses the arguments and runs the main() function, which analyses the quality of a project's comments.
For a smooth performance, make sure that the root of the repository is the working directory when running the script and use absolute paths as the arguments.

Example:
    $ python main.py C:\\my_project output.json C:\\my_models -log debug
"""
# import modules
import argparse
import logging
import os
import sys
# import evaluator, filter, and rater mains
from quality_assessment.src.comment_evaluator import main as evaluate
from quality_assessment.src.comment_filter import main as filter
from quality_assessment.src.comment_rater import main as rate
# path to the temporary files folder
TMP_PATH = r"quality_assessment/src/tmp"


def main(project: str, output: str, models: str, syn: int, language: str, label: str):
    """Combines the rater and evaluator classes and is the main entry point if you want to assess comment quality.
    Creates a json file with the data at the output location.

    Args:
        project: Path to directory of project to analyze.
        output: Path to output file.
        models: Path to directory holding the comment classification models.
        syn: Argument for enabling the synonym analysis (0 or 1). Not recommended for large projects.
        language: Code language of files to be evaluated.
        label: Label (summary, usage, rationale, expand, warning) of comments to be evaluated.
    """
    logging.info("Entering main() function with arguments: project: %s, output: %s, models: %s, syn: %d", project, output, models, syn)
    # check if 'project' is a valid directory
    if not os.path.isdir(project):
        logging.error("The project directory does not exist.")
        exit()
    logging.debug("Project is a valid directory")
    # check if 'models' is a valid directory
    if not os.path.isdir(models):
        logging.error("The models directory does not exist.")
        exit()
    logging.debug("Models is a valid directory")

    # rate, filter, and evaluate project
    comments_data = os.path.join(TMP_PATH, "rater_data.csv")
    missing_comments_data = os.path.join(TMP_PATH, "rater_data_missing.csv")
    filtered_comments_data = os.path.join(TMP_PATH, "rater_data_filtered.csv")

    logging.debug("Calling rate()")
    rate(project, comments_data, models)
    logging.debug("Done with rate()")

    logging.debug("Calling filter()")
    filter(comments_data, language, label)
    logging.debug("Done with filter()")

    logging.debug("Calling evaluate()")
    evaluate(project, output, filtered_comments_data, missing_comments_data, syn)
    logging.debug("Done with evaluate()")
    
    # delete temporary files
    os.remove(comments_data)
    os.remove(missing_comments_data)
    os.remove(filtered_comments_data)

    logging.info("Done. View output file at %s", output)


if __name__ == '__main__':
    # mandatory arguments
    parser = argparse.ArgumentParser(
        description="Scrape and evaluate a project directory's comments and their quality.")
    parser.add_argument('project', metavar='Project', type=str,
                        help='Path to the project directory to evaluate.')

    parser.add_argument('output', metavar='Output', type=str,
                        help='Path for the output .json file')

    parser.add_argument('models', metavar='Models', type=str,
                        help='Path to the directory of the trained models for comment type classification.')
    # optional arguments
    parser.add_argument("-syn", "--synonyms", type=int, help="Enable synonym analysis of comments in files. Not "
                                                             "recommended for big projects due to complexity. [0 ("
                                                             "default), 1].",
                        choices=[0, 1], default=0)
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
    # call main()
    main(args.project.replace("\\", "/"), args.output, args.models, args.synonyms, languages[args.language], labels[args.label])

    exit()
