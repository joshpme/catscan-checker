from lxml.etree import _Element
from page import get_page_size, convert_twips_to_cm

EXTRA_RULES = [
    '''
    <h3 class="subtitle is-6">Documents MUST be based on A4 or US Letter</h3>
    <table class="table is-bordered">
        <thead><tr><th colspan="2">A4</th></tr></thead>
        <tbody>
        <tr><td>Page Width</td><td>210mm</td></tr>
        <tr><td>Top</td><td>37mm</td></tr>
        <tr><td>Bottom</td><td>19mm</td></tr>
        <tr><td>Left</td><td>20mm</td></tr>
        <tr><td>Right</td><td>20mm</td></tr>
        </tbody>
    </table>
    <table class="table is-bordered">
        <thead><tr><th colspan="2">US Letter</th></tr></thead>
        <tbody>
        <tr><td>Page Width</td><td>8.5in</td></tr>
        <tr><td>Top</td><td>0.75in</td></tr>
        <tr><td>Bottom</td><td>0.75in</td></tr>
        <tr><td>Left</td><td>0.79in</td></tr>
        <tr><td>Right</td><td>1.02in</td></tr>
        </tbody>
    </table>
    Check gutter setting (Space between columns), for all section with more than 1 column, should be 0.51cm.
    '''
]
HELP_INFO = 'CSEPageSizeandMargins'
EXTRA_INFO = {
    'title':'Style Breakdown',
    'headers': '<thead><tr><th>Section</th><th>Page Size</th><th colspan="2">Margins</th><th>Columns</th><th colspan="2">Column Gutter (cm)</th></tr> </thead>',
    'columns': ['loop.index', 'page_size', 'margins', 'margins_ok', 'col_number', 'col_gutter', 'col_ok']
}

def check_sections(doc):
    sections = []
    for i, section in enumerate(doc.sections):
        cols = get_columns(section)
        sections.append(
            {
                'page_size': get_page_size(section),
                'margins_ok': check_margins(section),
                'margins': get_margins(section),
                'col_number': cols[0],
                'col_gutter': cols[1],
                'col_ok': cols[2],
            }
        )
    return sections


def check_margins_A4(section):
    return get_margins_A4(section) == [37, 19, 20, 20]


def check_margins_letter(section):
    return get_margins_letter(section) == [0.75, 0.75, 0.79, 1.02]


def get_margins_A4(section):
    return [
        round(section.top_margin.mm),
        round(section.bottom_margin.mm),
        round(section.left_margin.mm),
        round(section.right_margin.mm),
    ]


def get_margins_letter(section):
    return [
        round(section.top_margin.inches, 2),
        round(section.bottom_margin.inches, 2),
        round(section.left_margin.inches, 2),
        round(section.right_margin.inches, 2),
    ]


def get_margins(section):
    page_size = get_page_size(section)
    if page_size == 'A4':
        return get_margins_A4(section)
    elif page_size == 'Letter':
        return get_margins_letter(section)


def check_margins(section):
    page_size = get_page_size(section)
    if page_size == 'A4':
        return check_margins_A4(section)
    elif page_size == 'Letter':
        return check_margins_letter(section)


def get_columns(section):
    num = 1
    space = 0
    ok = False
    for c1 in section._sectPr.iterchildren():
        if isinstance(c1, _Element) and 'cols' in str(c1):
            for c2 in c1.items():
                if 'num' in str(c2):
                    num = int(c2[1])
                if 'space' in str(c2):
                    space = convert_twips_to_cm(c2[1])
    if num == 1 or ( num == 2 and space == 0.51):
        ok = True
    return num, space, ok


def get_margin_summary(doc):
    # get page size and margin details
    sections = check_sections(doc)
    ok = all([tick['margins_ok'] for tick in sections]) and all([tick['col_ok'] for tick in sections])
    return {
        'title': 'Page Size and Margins',
        'extra_rules': EXTRA_RULES,
        'help_info': HELP_INFO,
        'extra_info': EXTRA_INFO,
        'ok': ok,
        'message': 'Margins',
        'details': sections,
        'anchor': 'margins'
    }