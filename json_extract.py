"""JSON extraction helper functions"""
def json_extractor(obj, key):
    """Recursively fetch values from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for dict_key, dict_value in obj.items():
                if isinstance(dict_value, (dict, list)):
                    extract(dict_value, arr, key)
                elif dict_key == key:
                    arr.append(dict_value)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values

def get_files(obj, key):
    """Recursively fetch all files from a JSON structure."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for dict_key, dict_value in obj.items():
                if isinstance(dict_value, (dict, list)):
                    extract(dict_value, arr, key)
                elif dict_key == key and "." in dict_value:
                    arr.append(dict_value)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values
