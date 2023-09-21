import re
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl, CT_TblPr
from docx.table import _Cell, _Row, Table
from docx.text.paragraph import Paragraph
from lxml.etree import _Element

from styles import check_style
from titlecase import titlecase

RE_TABLE_LIST = re.compile(r'^Table \d+:')
RE_TABLE_ORDER = re.compile(r'^Table \d+')
RE_TABLE_REF_LIST = re.compile(r'(Table\s?\d+|Tables\s?\d+\sand\s\d+)')
RE_TABLE_FORMAT = re.compile(r'\.$')
RE_TABLE_TITLE_CAPS = re.compile(r'^(?:[A-Z][^\s]*\s?)+$')
RE_SPECIAL_CHAR = re.compile(r'[^a-zA-Z ]')
RE_MULTI_SPACE = re.compile(r' +')

STYLES = {
    'SingleLine': {
        'type': 'Table - Single Line',
        'styles': {
            'jacow': 'Table Caption',
        },
        'alignment': 'CENTER',
        'font_size': 10.0,
        'space_before': ['>=', 3.0],
        'space_after': 3.0,
        'bold': None,
        'italic': None,
    },
    'MultiLine': {
        'type': 'Table - Multi Line',
        'styles': {
            'jacow': 'Table Caption Multi Line',
        },
        'alignment': 'JUSTIFY',
        'font_size': 10.0,
        'space_before': ['>=', 3.0],
        'space_after': 3.0,
        'bold': None,
        'italic': None,
    }
}
EXTRA_RULES = [
    'Table captions are actually titles, this means that they are in Title Case, and don’t have a “.” At the end, well unless exceeds 2 lines',
    'The table caption is centred if 1 line (“Table Caption” Style), and Justified if 2 or more (“Table Caption Multi Line” Style).  The table caption must appear above the Table.',
    'All tables must be numbered in the order they appear in the document and not skip a number in the sequence.',
    'All tables start with “Table n:”.',
    'All tables must be referred to in the main text and use “Table n”.'
]
HELP_INFO = 'CSETables'
EXTRA_INFO = {
    'title':'Use Breakdown',
    'headers': '<thead><tr><th>No.</th><th colspan="3">Caption</th><th colspan="2">Used</th><th>Order</th><th>Table</th></tr></thead>',
    'columns': ['id', 'text', 'text_format_ok', 'text_format_message', 'used', 'used_ok', 'order_ok', 'table']
}
VALID_FIGURE_STYLES = ['Table Caption', 'Table Caption Multi Line', 'Caption', 'Caption Multi Line']

def iter_block_items(parent):
    """
    Generate a reference to each paragraph and table child within *parent*,
    in document order. Each returned value is an instance of either Table or
    Paragraph. *parent* would most commonly be a reference to a main
    Document object, but also works for a _Cell object, which itself can
    contain paragraphs and tables.
    """
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    elif isinstance(parent, _Row):
        parent_elm = parent._tr
    else:
        raise ValueError("something's not right")

    # TODO make this work for floating tables
    # as do not necessarily appear in the same order in the document as they do visually
    # Floating tables can be fixed in word doc by right clicking in table, choosing table properties,
    # selecting None for text wrapping and clicking on ok.
    # Then moving the table to the correct place.
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def check_caption_format(title, format_checks):
    result = True
    message = []
    text = title.text.strip()
    for check in format_checks:
        if check['valid_result'] is True and check['test'].search(text) is None:
            result = False
            message.append(check['message'])
        elif check['valid_result'] is False and check['test'].search(text) is not None:
            result = False
            message.append(check['message'])

    # Also check title case
    title_to_check = RE_SPECIAL_CHAR.sub(' ', text)
    # remove extra spaces created by preformat
    title_to_check = RE_MULTI_SPACE.sub(' ', title_to_check)

    # use titlecase library to create title case of title and see if it is same as original
    if titlecase(title_to_check) != title_to_check:
        result = False
        message.append('Not in Title Case/Initial Caps')

    return result, message


def check_is_floating(table):
    # check whether floating table
    tblppr = False
    width_type = False
    for c in table._element.iterchildren():
        if isinstance(c, CT_TblPr):
            for c2 in c.iterchildren():
                if isinstance(c2, _Element) and 'tblpPr' in str(c2):
                    tblppr = True
                    for c3 in c2.items():
                        if 'tblpY' in str(c3):
                            # width should be higher then the line height of 11
                            tblppr = int(c3[1]) > 11
                # also need to check that tblW is auto
                if isinstance(c2, _Element) and 'tblW' in str(c2):
                    # type is the second attribute of tblW
                    width_type = c2.items()[1][1] == 'auto'

    return tblppr and width_type


def get_table_paragraphs(doc):
    prev = None
    table_details = []
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            prev = block
        elif isinstance(block, Table):
            # exclude those with only 1 column, since not likely to be real tables.
            if len(block.columns) == 1:
                continue
            # exclude those with only 1 row, since not likely to be real tables.
            if len(block.rows) == 1:
                continue

            # check whether there is data in table
            text_found = False
            for row in block.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if paragraph.text.strip() != '':
                            text_found = True
                            break

            if text_found:
                table_details.append({'table': block, 'title': prev})
    return table_details


def check_table_titles(doc):
    """
    Table captions are actually titles, this means that they are in Title Case, and don’t have a “.”
    at the end, well unless exceeds 2 lines.  The table caption is centred if 1 line (“Table Caption” Style),
    and Justified if 2 or more (“Table Caption Multi Line” Style.  The table caption must appear above the Table.

    All tables must be numbered in the order they appear in the document and not skip a number in the sequence.

    All tables start with “Table n:”.
    All tables must be referred to in the main text and use “Table n”.
    """
    table_details = get_table_paragraphs(doc)

    refs = []
    table_titles = [item['title'].text for item in table_details]
    for paragraph in doc.paragraphs:
        # don't include if it is one of the table titles
        if paragraph.text not in table_titles:
            # make sure we are using normal spaces
            text = paragraph.text.replace(u'\xa0', u' ')
            # Check for table names
            result = RE_TABLE_REF_LIST.findall(text)
            if result is not None:
                for f in result:
                    # split by space and parse for numbers
                    for w in f.split(' '):
                        try:
                            refs.append(int(w))
                        except ValueError:
                            # do nothing
                            continue

    title_details = []
    count = 1

    table_caption_format_checks = [
        {
            'test': RE_TABLE_LIST,
            'valid_result': True,
            'message': 'Does not use "Table N: " format',
        },
        {
            'test': RE_TABLE_FORMAT,
            'valid_result': False,
            'message': 'Has a . at the end of the sentence',
        },
    ]

    for table in table_details:
        p = table['title']
        text = p.text.strip()
        result, message = check_caption_format(p, table_caption_format_checks)

        order_check = RE_TABLE_ORDER.findall(text)
        # TODO Add info if doing some common wrong ways of doing references like 'table 1'
        used_count = refs.count(count)

        floating = check_is_floating(table['table'])

        table_compare = STYLES['SingleLine']
        # 55 chars is approx where it changes from 1 line to 2 lines
        if len(text) > 55:
            table_compare = STYLES['MultiLine']

        style_ok, detail = check_style(p, table_compare)
        style_name = p.style.name
        if p.style.name not in VALID_FIGURE_STYLES:
            final_style_ok = 2
        else:
            final_style_ok = style_ok

        if 40 < len(text) < 80:
            final_style_ok = 2
            style_name = f"'{style_name}' checking against type '{table_compare['styles']['jacow']}'"

        title_detail = {
            'id': count,
            'text': p.text,
            'text_format_ok': result,
            'text_format_message': message,
            'used': used_count,
            'used_ok': used_count > 0,
            'order_ok': f'Table {count}' in order_check,
            'style': style_name,
            'style_ok': final_style_ok,
            'table': f"rows: {len(table['table'].rows)}, columns: {len(table['table'].columns)}, floating: {floating}"
        }
        title_detail.update(detail)
        title_details.append(title_detail)
        count = count+1

    return title_details


def get_table_summary(doc):
    table_titles = check_table_titles(doc)
    # Use checks first
    ok = all([
            all([tick['text_format_ok'], tick['order_ok'], tick['style_ok'], tick['order_ok']])
            for tick in table_titles])

    # Check style use checks pass
    if ok:
        for tick in table_titles:
            if not tick['style_ok']:
                # If find a false then the result is false
                ok = False
                break
            elif tick['style_ok'] == 2:
                # If find a 2 (?) then result is 2 unless a false is found later
                ok = 2

    return {
        'title': 'Tables',
        'rules': STYLES,
        'extra_rules': EXTRA_RULES,
        'help_info': HELP_INFO,
        'extra_info': EXTRA_INFO,
        'ok': ok,
        'message': 'Table issues',
        'details': table_titles,
        'anchor': 'tables',
        'show_total': True,
    }
