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

import csv


class CommentExporter:
    """
    Class for exporting the found comment objects to a .csv file

    Attributes:
        comments_header: List of the column names of the resulting .csv for the found comments.
        missing_comments_header: List of the column names of the resulting .csv for the missing comments.
    """
    def __init__(self):
        self.comments_header = ["id", "path", "position", "type", "handle", "text", "label", "label_proba",
                                "coherence_coefficient", "N_question", "N_exclamation",
                                "processed_text", "N_words", "N_complex_words", "N_syllables", "N_sentences",
                                "words", "complex_words", "syllables", "sentences",
                                "fkgls", "frel", "fi", "abbreviations", "N_abbreviations",
                                "time_millis", "language", "language_proba", "synonyms", "is_code", "code_language"]

        self.missing_comments_header = ["path", "position", "handle", "type"]

    def export_comments(self, comments: list, path: str):
        """
        Export the found comments to a .csv file
        Args:
            comments: List of found comments
            path: Path to output file

        Returns:
            Creates a .csv at the output location with the found comments' data
        """
        with open(path, "w", newline='', encoding="UTF-8") as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(self.comments_header)
            for comment in comments:
                writer.writerow(comment.get_row())

    def export_missing_comments(self, comments: list, path: str):
        """
        Export the missing comments to a .csv file
        Args:
            comments: List of missing comments
            path: Path to output file

        Returns:
            Creates a .csv at the output location with the missing comments' data
        """
        with open(path, "w", newline='', encoding="UTF-8") as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(self.missing_comments_header)
            for c in comments:
                writer.writerow([c["file"], c["pos"], c["name"], c["type"]])