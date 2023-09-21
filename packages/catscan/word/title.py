from page import get_text, check_title_case
from styles import check_style_detail

STYLES = {
    'normal': {
        'type': 'Paper Title',
        'styles': {
            'jacow': 'JACoW_Paper Title',
            'normal': 'Paper Title',
        },
        'alignment': 'CENTER',
        'font_size': 14.0,
        'space_before': 0.0,
        'space_after': 3.0,
        'bold': True,
        'italic': None,
    }
}
EXTRA_RULES = [
    'Case: Title should contain greater than 70% of CAPITAL Letters, can’t be simple Title Case.',
]
HELP_INFO = 'SCEPaperTitle'


def get_title_details(p):
    title = get_text(p)
    title_detail = {
        'text': title,
        'original_text': p.text,
        'case_ok': check_title_case(title, 0.7),
    }
    return title_detail


def get_title_summary(paragraphs):
    style_compare = STYLES['normal']
    title_details = []
    for p in paragraphs:
        if p.text.strip():
            detail = get_title_details(p)
            detail.update(check_style_detail(p, style_compare))
            title_style_ok = p.style.name == style_compare['styles']['jacow']
            detail.update({'title_style_ok': title_style_ok, 'style': p.style.name})
            title_details.append(detail)
    return {
        'details': title_details,
        'rules': STYLES,
        'extra_rules': EXTRA_RULES,
        'help_info': HELP_INFO,
        'title': 'Title',
        'ok': all([tick['style_ok'] and tick['case_ok'] for tick in title_details]),
        'message': 'Title issues',
        'anchor': 'title'
    }


def tex_remove_lines(text):
    return text.replace('\\\\', '')

def get_title_summary_latex(part):
    """
    Example from JACoW example latex file
    (double \\ for title, NoCaseChange and thanks were single in example but causes issues in this comment)
    \\title{preparation OF papers for \\NoCaseChange{JACoW} conferences\\thanks{Work supported by ...}}

    :param part: title component of the parsed tex document
    :return: dict with summary result info
    """
    if part and part.string:
        text = ''
        for i, p in enumerate(part.contents):
            if isinstance(p, str):
                # TODO add parse properly for end of section
                if p[0:9] == '%\\thanks{':
                    continue
                text = text + p.upper()
            elif p.name == 'NoCaseChange':
                text = text + p.string
            elif p.name in ['&']:
                # add escaped characters
                text = text + p.name
            elif p.name in ['thanks']:
                # ignore
                continue

        return {'original_text': part.string, 'text': tex_remove_lines(text.strip()), 'title': 'Title', 'ok': True, 'extra_info': f'Title: {text}'}

    return {'original_text': '', 'text': '', 'title': 'Title', 'ok': False, 'extra_info': f'No Title found'}
