class Comment:
    """
    Comment data class for holding all attributes of a comment and exporting as a .csv row

    Args:
        id: unique id of comment
        path: path to file that contains this comment
        line: line/col of the comment in file
        type: which type of comment (e.g. in-line, class, function, etc.)
        text: raw text of comment
        handle: handle of the class/function/etc that a comment comments on
        code_language: the language of the code in the file (e.g. C#)
    """

    def __init__(self, id: int, path: str, line: str, type: str, text: str, handle: str, code_language: str):
        # init
        self.id = id
        self.path = path
        self.line = line
        self.type = type
        self.text = text
        self.handle = handle
        self.code_language = code_language

        # Tokenizer
        self.processed_text = None
        self.words = None
        self.complex_words = None
        self.sentences = None
        self.syllables = None

        # usefulness
        self.label = None
        self.label_probability = None
        self.question_marks = None
        self.exclamation_marks = None
        self.flesch_kincaid_grade_level = None
        self.flesch_reading_ease_level = None
        self.fog_index = None
        self.abbreviations = None
        self.time_millis = None
        self.is_code = False

        # consistency
        self.language = None
        self.unique_words_swr = None
        self.synonyms = None

        # coherence
        self.coherence_coefficient = None

    def get_row(self) -> list:
        """
        Create a list of attributes for exporting as a row in a .csv

        Returns: List of attributes
        """
        syn = self.synonyms if len(self.synonyms) > 0 else {}
        abbr = self.abbreviations if len(self.abbreviations) > 0 else {}
        return [self.id, self.path, self.line, self.type, self.handle, self.text, self.label, self.label_probability,
                self.coherence_coefficient, self.question_marks, self.exclamation_marks,
                self.processed_text, len(self.words), len(self.complex_words), len(self.syllables), len(self.sentences),
                self.words, self.complex_words, self.syllables, self.sentences,
                self.flesch_kincaid_grade_level, self.flesch_reading_ease_level, self.fog_index, abbr, len(abbr),
                self.time_millis, self.language[0], self.language[1], syn, self.is_code, self.code_language]
