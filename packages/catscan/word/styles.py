import operator
from docx.shared import Inches, Mm, Twips
from docx.oxml.text.parfmt import CT_PPr, CT_Ind
from docx.text.paragraph import Paragraph

VALID_STYLES = [
    'JACoW_Abstract_Heading',
    'JACoW_Author List',
    'JACoW_Body Text Indent',
    'JACoW_Bulleted List',
    'JACoW_Numbered list',
    'JACoW_Paper Title',
    'JACoW_Reference #10 onwards',
    'JACoW_Reference #1-9 when >= 10 Refs',
    'JACoW_Reference when <= 9 Refs',
    'JACoW_Reference Italics',
    'JACoW_Reference url_doi',
    'JACoW_Third-level Heading',
    'JACoW_Section Heading',
    'JACoW_Subsection Heading'
]

VALID_NON_JACOW_STYLES = [
    'Figure Caption',
    'Figure Caption Multi Line',
    'Table Caption',
    'Table Caption Multi Line',
    'Caption',
    'Caption Multi Line'
]

# These are in the jacow templates so may be in docs created from them
# Caption and Normal for table title and figure title
# 'Body Text Indent' instead of 'JACoW_Body Text Indent' in a few places
# 'Heading 3' for Acronyms header
OTHER_VALID_STYLES = ['Body Text Indent', 'Normal', 'Caption', 'Heading 3']

EXTRA_RULES = [
    '''
<p>The latest JACoW Template must be used.<br/>
Standard JACoW Style’s must embedded in the document.</p>   
    '''
]
HELP_INFO = 'CSEJACoWStyles'
EXTRA_INFO = {
    'title': 'Style Breakdown',
    'headers': '<thead><tr><th>Style</th><th>Embedded in Document</th></tr></thead>',
    'columns': ['style', 'style_ok']
}


# check if th
def check_jacow_styles(doc):
    result = []
    jacow_styles = get_jacow_styles(doc)

    for valid_style in VALID_STYLES:
        result.append({'style': valid_style, 'style_ok': valid_style in jacow_styles})

    return result


def get_jacow_styles(doc):
    return [s.name for s in doc.styles if s.name.startswith('JACoW')]


def get_paragraph_style_exceptions(doc):
    jacow_styles = get_jacow_styles(doc)
    exceptions = []
    for i, p in enumerate(doc.paragraphs):
        if (
            not p.text.strip() == ''
            and p.style.name not in jacow_styles
            and p.style.name not in OTHER_VALID_STYLES
        ):
            exceptions.append(p)
    return exceptions


def get_paragraph_alignment(paragraph):
    # alignment style can be overridden by more local definition
    alignment = paragraph.style.paragraph_format.alignment
    if alignment is None and paragraph.style.base_style is not None and \
            paragraph.style.base_style.paragraph_format.alignment is not None:
        alignment = paragraph.style.base_style.paragraph_format.alignment

    if paragraph.alignment is not None:
        alignment = paragraph.alignment
    elif paragraph.paragraph_format.alignment is not None:
        alignment = paragraph.paragraph_format.alignment

    if alignment:
        return alignment._member_name
    else:
        return None


def get_indents(style_format):
    first_line_indent, hanging_indent, left_indent = None, None, None
    for i in style_format.element.iterchildren():
        if isinstance(i, CT_PPr):
            for j in i.iterchildren():
                if isinstance(j, CT_Ind):
                    first_line_indent, hanging_indent, left_indent = j.firstLine, j.hanging, j.left
    return first_line_indent, hanging_indent, left_indent


def get_paragraph_space(paragraph):
    # paragraph formatting style can be overridden by more local definition
    before, after = \
        paragraph.style.paragraph_format.space_before, \
        paragraph.style.paragraph_format.space_after

    first_line_indent, hanging_indent, left_indent = get_indents(paragraph.style.paragraph_format)

    if paragraph.style.base_style is not None:
        first_line, hanging, left = get_indents(paragraph.style.base_style.paragraph_format)
        if before is None:
            before = paragraph.style.base_style.paragraph_format.space_before
        if after is None:
            after = paragraph.style.base_style.paragraph_format.space_after
        if first_line_indent is None:
            first_line_indent = first_line
        if hanging_indent is None:
            hanging_indent = hanging
        if left_indent is None:
            left_indent = left

    if paragraph.paragraph_format.space_before is not None:
        before = paragraph.paragraph_format.space_before
    if paragraph.paragraph_format.space_after is not None:
        after = paragraph.paragraph_format.space_after
    first_line, hanging, left = get_indents(paragraph.paragraph_format)
    if first_line is not None:
        first_line_indent = first_line
    if hanging is not None:
        hanging_indent = hanging
    if left is not None:
        left_indent = left

    if before:
        before = before.pt
    if after:
        after = after.pt
    if first_line_indent:
        first_line_indent = first_line_indent.pt
    elif hanging_indent:
        first_line_indent = -hanging_indent.pt
    if hanging_indent:
        hanging_indent = hanging_indent.pt
    if left_indent:
        left_indent = left_indent.pt

    return before, after, first_line_indent, hanging_indent, left_indent

def get_style_font_run(run):
    style = run.style
    bold, italic, font_size, font_name, all_caps = style.font.bold, style.font.italic, style.font.size, style.font.name, style.font.all_caps
    if run.style.base_style is not None:
        style = run.style.base_style
        # if values not set, use base style
        if font_size is None:
            font_size = style.font.size
        if font_name is None:
            font_name = style.font.name
        if bold is None:
            bold = style.font.bold
        if italic is None:
            italic = style.font.italic
        if all_caps is None:
            all_caps = style.font.all_caps

    if font_name is None:
        font_name = run.font.name
    if font_size is None:
        font_size = run.font.size

    if font_size is not None:
        font_size = font_size.pt

    return bold, italic, font_size, font_name, all_caps


def get_style_font(paragraph, url):
    # use paragraph style if values set
    style = paragraph.style
    bold, italic, font_size, font_name, all_caps = style.font.bold, style.font.italic, style.font.size, style.font.name, style.font.all_caps
    if paragraph.style.base_style is not None:
        style = paragraph.style.base_style
        # if values not set, use base style
        if font_size is None:
            font_size = style.font.size
        if font_name is None:
            font_name = style.font.name
        if bold is None:
            bold = style.font.bold
        if italic is None:
            italic = style.font.italic
        if all_caps is None:
            all_caps = style.font.all_caps

    # TODO get distinct list
    sections = [paragraph]
    if isinstance(paragraph, Paragraph):
        sections = paragraph.runs

    for r in sections:
        text = r.text.strip()
        if not text:
            continue

        if 'has_url' in url and url['has_url']:
            found = False
            for s in url['starts']:
                if text.startswith(s):
                    found = True
            # ignore font if url found at start
            if found:
                continue

        if r.font is not None:
            if r.font.size is not None:
                font_size = r.font.size
            if r.font.name is not None:
                font_name = r.font.name
            if r.font.bold is not None:
                bold = r.font.bold
            if r.font.italic is not None:
                italic = r.font.italic
            if r.font.all_caps is not None:
                all_caps = r.font.all_caps
        if r.bold is not None:
            bold = r.bold
        if r.italic is not None:
            italic = r.italic

    if not font_size:
        font_size = 10.0
        # TODO find default size (from section ?)
        # styles = paragraph._parent._parent._parent._parent.styles
    else:
        font_size = font_size.pt

    if not font_name:
        font_name = 'Times new Roman'

    return bold, italic, font_size, font_name, all_caps


def get_style_details(p, url={}):
    space_before, space_after, first_line_indent, hanging_indent, left_indent = get_paragraph_space(p)
    bold, italic, font_size, font_name, all_caps = get_style_font(p, url)
    alignment = get_paragraph_alignment(p)
    return locals()


def get_compare(inp, relate, cut):
    ops = {'>': operator.gt,
           '<': operator.lt,
           '>=': operator.ge,
           '<=': operator.le,
           '=': operator.eq}
    return ops[relate](inp, cut)


# TODO work out why two almost identical functions below
def check_style(p, compare, url={}):
    detail = get_style_details(p, url)
    # remove paragraph from dict returned since it is not json serialisable
    del detail['p']

    # use list from compare
    style_ok = True
    for key, value in compare.items():
        if key not in detail:
            continue
        elif key in ['space_before', 'space_after']:
            if isinstance(compare[key], list):
                result = detail[key] is not None and get_compare(detail[key], compare[key][0], compare[key][1])
                if not result:
                    detail[key] = f"{detail[key]} should be {' '.join(map(str, compare[key]))}"
            else:
                result = any([detail[key] == compare[key], detail[key] is None and compare[key] == 0.0])
                if not result:
                    detail[key] = f"{detail[key]} should be {compare[key]}"
        else:
            result = detail[key] == compare[key]
            if not result:
                detail[key] = f"{detail[key]} should be {compare[key]}"
        if not result:
            style_ok = False

    # if key not in compare, then change to NA
    for key, value in detail.items():
        if not key == 'all_caps' and key not in compare.keys():
            detail[key] = 'NA'
    return style_ok, detail


def check_style_detail(p, compare):
    detail = get_style_details(p)
    # remove paragraph from dict returned since it is not json serialisable
    del detail['p']

    # use list from compare
    style_ok = True
    for key, value in compare.items():
        if key not in detail:
            continue
        elif key in ['space_before', 'space_after']:
            if isinstance(compare[key], list):
                result = detail[key] is not None and get_compare(detail[key], compare[key][0], compare[key][1])
                if not result:
                    detail[key] = f"{detail[key]} should be {' '.join(map(str, compare[key]))}"
            else:
                result = any([detail[key] == compare[key], detail[key] is None and compare[key] == 0.0])
                if not result:
                    detail[key] = f"{detail[key]} should be {compare[key]}"
        else:
            if isinstance(compare[key], list):
                result = detail[key] in compare[key]
            else:
                result = detail[key] == compare[key]

            if not result:
                detail[key] = f"{detail[key]} should be {compare[key]}"
        if not result:
            style_ok = False
        detail['style_ok'] = style_ok

    # if key not in compare, then change to NA
    for key, value in detail.items():
        if key not in ['all_caps', 'style_ok'] and key not in compare.keys():
            detail[key] = 'NA'
    return detail


def get_style_summary(doc):
    jacow_styles = check_jacow_styles(doc)
    return {
        'title': 'JACoW Styles',
        'extra_rules': EXTRA_RULES,
        'help_info': HELP_INFO,
        'extra_info': EXTRA_INFO,
        'ok': all([tick['style_ok'] for tick in jacow_styles]),
        'message': 'Styles issues',
        'details': jacow_styles,
        'anchor': 'styles'
    }
