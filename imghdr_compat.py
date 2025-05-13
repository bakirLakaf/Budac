import filetype

def what(filename):
    kind = filetype.guess(filename)
    if kind is None:
        return None
    return kind.extension