def score_node(node):
    positive, unknown, negative = 0, 0, 0
    for name, value in node.items():
        if name == 'text':
            continue
        if '_ok' in name:
            if value == 2:
                unknown += 1
            elif value is False:
                negative += 1
            elif value is True:
                positive += 1
        elif isinstance(value, str) and 'should be' in value:
            negative += 1

    return positive, unknown, negative


def check_styles(section):
    total_unknown, total_negative, total_positive = 0, 0, 0
    if 'details' in section:
        if isinstance(section['details'], list):
            for detail in section['details']:
                (positive, unknown, negative) = score_node(detail)
                total_unknown += unknown
                total_positive += positive
                total_negative += negative
        elif isinstance(section['details'], dict):
            for node in section['details']:
                for detail in section['details'][node]:
                    (positive, unknown, negative) = score_node(detail)
                    total_unknown += unknown
                    total_positive += positive
                    total_negative += negative

    return total_positive, total_unknown, total_negative


def score(summary):
    total_positive, total_unknown, total_negative = 0, 0, 0

    scores = {}
    for name, section in summary.items():
        if name != 'Languages':
            (positive, unknown, negative) = check_styles(section)
            total_unknown += unknown
            total_positive += positive
            total_negative += negative
            scores[name] = (positive, unknown, negative)

    scores['total'] = (total_positive, total_unknown, total_negative)

    return scores
