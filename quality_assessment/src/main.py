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
# import evaluator and rater mains
from quality_assessment.src.comment_evaluator import main as evaluate
from quality_assessment.src.rater import main as rate
# path to the temporary files folder
TMP_PATH = r"quality_assessment/src/tmp"


def main(project: str, output: str, models: str, syn: int):
    """Combines the rater and evaluator classes and is the main entry point if you want to assess comment quality.
    Creates a json file with the data at the output location.

    Args:
        project: Path to directory of project to analyze.
        output: Path to output file.
        models: Path to directory holding the comment classification models.
        syn: Argument for enabling the synonym analysis (0 or 1). Not recommended for large projects.
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

    # rate and evaluate project
    comments_data = os.path.join(TMP_PATH, "rater_data.csv")
    logging.debug("Calling rate()")
    rate(project, comments_data, models)
    logging.debug("Done with rate()")
    logging.debug("Calling evaluate()")
    evaluate(project, output, comments_data, comments_data + ".missing", syn)
    logging.debug("Done with evaluate()")
    # delete temporary files
    os.remove(os.path.join(TMP_PATH, "rater_data.csv"))
    os.remove(os.path.join(TMP_PATH, "rater_data.csv.missing"))

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
    main(args.project.replace("\\", "/"), args.output, args.models, args.synonyms)

    exit()
