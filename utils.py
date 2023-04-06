import csv


def extract_bijection_csv(path_to_file):
    bijection = []
    with open(path_to_file) as datafile:
        reader = csv.reader(datafile)
        for line in reader:
            if not any(len(_) > 6 for _ in line):
                yield line


def get_lines_with_context(context_file, bijection_extractor):

    text = ""

    with open(context_file) as context:
        text = context.readlines()

    text = set("".join(text))
    print(len(text))

    for line in bijection_extractor:
        glyph = line[0]
        if glyph in text:
            yield line


def raw_extracter(context_file):
    with open(context_file) as datafile:
        reader = csv.reader(datafile)
        for line in reader:
            yield line
