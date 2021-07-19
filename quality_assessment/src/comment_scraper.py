# module imports
import os
import subprocess
import xml.dom.minidom as xml
# import Comment Object
from quality_assessment.src.comment_object import Comment

COMMENT_TYPES = ["class", "function", "constructor", "interface", "enum"]
"""List of different possible types of comments"""


class CommentScraper:
    """
    Class for scraping comments of a directory through srcML and instantiate them with basic fields

    Attributes:
        id: keep track and increment the id of found comments
    """

    def __init__(self):
        # start id at 0
        self.id = 0

    def get_directory_comments(self, dir: str) -> dict:
        """
        Get all comments in all files in a directory.

        Args:
            dir: path to parent directory to scrape for comments.

        Returns: dict consisting of "comments" and "missing_comments" consisting of comment objects.
        """
        found_comments = []
        missing_comments = []
        # run srcML on dir, saving it to export.xml temporarily
        p = subprocess.Popen('srcml . -o export.xml --position', shell=True, cwd=dir)
        p.wait()
        doc = None
        try:
            doc = xml.parse(os.path.join(dir, "export.xml"))
        except FileNotFoundError:
            logging.error("srcML needs to be installed and added to PATH or this script has no access to the target directory.")

        # get all files found
        files = doc.getElementsByTagName("unit")
        # iterate through them
        for file in files:
            # get comment text & line position
            file_path = file.getAttribute("filename")
            if file_path == "":
                continue
            # get all comment elements in file and code language
            comments = file.getElementsByTagName("comment")
            code_language = file.getAttribute("language")
            # iterate through all comments in file
            i = 0
            while i < (len(comments)):
                comment = comments[i]
                # get position
                line = comment.getAttribute("pos:start")
                # get text
                text = comment.firstChild.nodeValue

                sibling = None
                try:
                    sibling = comment.nextSibling if comment.nextSibling.nodeType == 1 else comment.nextSibling.nextSibling
                except:
                    # comment at end of file -> no siblings
                    pass

                # concatenate comments that are together in the source code
                while sibling and sibling.tagName == "comment":
                    text += '\\n' + sibling.firstChild.nodeValue
                    i = i + 1
                    try:
                        sibling = sibling.nextSibling if sibling.nextSibling.nodeType == 1 else sibling.nextSibling.nextSibling
                    except:
                        sibling = None
                        pass
                # default is in-line comment
                typ = "in-line"
                handle = None
                # if at start of file it is a header comment
                if line == "1:1":
                    typ = "header"
                # if the next element is a valid comment type, write it to typ
                if sibling and sibling.tagName in COMMENT_TYPES:
                    typ = sibling.tagName
                    handle = get_handle(sibling)
                # discard empty comments
                if text.replace("\n", "").strip() != "":
                    # instantiate and append comment
                    found_comments.append(Comment(self.id, file_path, line, typ, text, handle, code_language))
                    self.id += 1
                i += 1
            children = file.childNodes
            # only look at "Elements" which has node type 1
            children = [child for child in children if child.nodeType == 1]
            # first element should be a (license) comment in every file
            if children[0].tagName != "comment":
                missing_comments.append({"file": file_path, "pos": '1:1', "name": None, "type": "header"})
            # get other missing comments
            missing_comments += get_missing_comments(children, file_path)
        # delete temporary srcML file
        os.remove(os.path.join(dir, "export.xml"))
        return {"comments": found_comments, "missing_comments": missing_comments}


def get_handle(e) -> str:
    """
    Helper to get handle of an element.

    Args:
        e: XML element.

    Returns:
        handle of element e.
    """
    attrs = e.childNodes
    name = ""
    for attr in attrs:
        if attr.nodeType == 1 and attr.tagName == "name":
            name = attr.firstChild.nodeValue
    return name


def get_missing_comments(c, file_path: str) -> list:
    """
    Recursive function for checking a srcML XML for elements that lack a comment.

    Args:
        c: children of an XML element
        file_path: path of comment for writing.

    Returns:
        List of missing comments consisting of 'file', 'pos', 'name' and 'type'
    """
    # only look at "Elements" which have node type 1
    children = [child for child in c if child.nodeType == 1]
    missing_comments = []
    for i in range(1, len(children)):
        # check that an element that is part of COMMENT_TYPES has a comment
        if children[i].tagName in COMMENT_TYPES:
            # missing comment
            if not (i > 1 and children[i - 1].tagName == "comment"):
                name = get_handle(children[i])
                line = children[i].getAttribute("pos:start")
                # add missing comment
                missing_comments.append(
                    {"file": file_path, "pos": line, "name": name, "type": children[i].tagName})
                # recursive call
                try:
                    missing_comments += get_missing_comments(children[i].getElementsByTagName("block")[0].childNodes,
                                                             file_path)
                except IndexError:
                    pass
    return missing_comments
