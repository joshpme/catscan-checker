import json

def remove_white_space(text):
    return text.replace("\n", "").replace(" ", "").replace("\t", "")

def is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False


def json_serialise(x):
    json_data = {}
    for i, data in x.items():
        # just log summary
        if i not in ['summary', 'authors', 'title']:
            continue

        if isinstance(data, dict):
            json_data[i] = {}

            for j, d in data.items():
                json_data[i][j] = json.dumps(d)
        else:
            json_data[i] = json.dumps(data)

    return json_data


'''
Look at the logic of references
Look at the logic of figures
Look at whether I can approx single line vs multi line better
Look at the logic for whether something is a paragraph
(currently, after abstract heading and before reference heading where more than 200 characters and doesn't start with Table or Figure)
Look at the logic for whether something is a heading,
(currently one of the following styles - JACoW_Section Heading, Section Heading, JACoW_Subsection Heading, Subsection Heading, JACoW_Third - Level Heading, Third - Level Heading)

{#
jacow text color
#0066ff  4.47 with DDFFDD, 3.82 with DDFFDD, 4.71 with FCFCFC
#0e01fe: 7.91 with DDFFDD, 6.77 with FFDDDD, 8.34 with FCFCFC
#3135dd  7.23 with DDFFDD, 6.19 with FFDDDD, 7.62 with FCFCFC
#0020ff
#0e01fe
#3300ff
#007bff; (from ref.ipac)
#}
'''