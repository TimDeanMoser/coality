"""JSON extraction helper functions"""
def _files_comments_helper(obj, key):
    """Recursively fetch all files from a JSON structure."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for dict_key, dict_value in obj.items():
                if isinstance(dict_value, (dict, list)):
                    extract(dict_value, arr, key)
                if dict_key == key and "." in dict_value:
                    arr.append("fl:" + dict_value)
                if dict_key == "text" and dict_value is not None:
                    arr.append(dict_value)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values

def get_files_comments(obj):
    """Return a mapping consisting of file name and comment"""
    unmapped = _files_comments_helper(obj, "name")
    mapped = []
    current_file = ""
    for i in unmapped:
        if "fl:" in i:
            current_file = i
        else:
            mapped.append((current_file.split("fl:")[-1], i))
    return mapped
