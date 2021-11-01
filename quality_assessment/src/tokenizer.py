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

import re

import nltk

WORD_PAT = r"([a-z][-'a-z]*)"
"""Pattern for matching words."""
VOWELS = r"[aeiouy]"
"""Vowel Characters"""
VALID_HYPHENS = r"[a-z]{2,}-[a-z]{2,}"
"""Pattern for matching words with valid hyphens"""
SYLLABLES = r"[bcdfghjklmnpqrstvwxz]*[aeiouy]+[bcdfghjklmnpqrstvwxz]*"
"""Pattern for matching syllables of a word"""


class Tokenizer:
    """
    Class for basic NLP on comment objects

    Attributes:
        words: List of words in comment
        complex_words: List of words with >=3 syllables in comment
        sentences: List of sentences in comment
        syllables: Concatenated list of all syllables in a comment
    """
    def __init__(self):
        # nltk.download('punkt')
        self.words: list = []
        self.complex_words: list = []
        self.sentences: list = []
        self.syllables: list = []

    def get_stats(self, comment):
        """
        Basic NLP on a comment's text.

        Args:
            comment: Comment object to evaluate

        Returns:
            Writes words, complex_words, sentences and syllables into comment object
        """
        line = comment.processed_text
        # match words
        raw_words = re.findall(WORD_PAT, line.lower().strip())
        # filter words without vowels or with invalid hyphens
        self.words = list(filter(lambda word: not (
                not re.search(VOWELS, word) or (word.find("-") > 0 and not re.search(VALID_HYPHENS, word))), raw_words))
        # get sentences
        self.sentences = nltk.sent_tokenize(line)
        for word in self.words:
            syl = re.findall(SYLLABLES, word.lower())
            # tailing 'e' can cause an edge case with the regex, which is why it is added to the second to last syllable
            if len(syl) > 1 and syl[-1] == "e":
                tmp = syl[0:-2]
                tmp.append(syl[-2] + 'e')
                syl = tmp
            self.syllables = self.syllables + syl
            # add complex word list if >= 3 syllables
            if len(syl) >= 3:
                self.complex_words.append(word)
        comment.words = self.words
        comment.complex_words = self.complex_words
        comment.sentences = self.sentences
        comment.syllables = self.syllables