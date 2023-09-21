import re
from styles import check_style, VALID_STYLES, VALID_NON_JACOW_STYLES
from heading import HEADING_STYLES
from page import get_text

PARAGRAPH_STYLES = {
    'normal': {
        'styles': {
            'jacow': 'JACoW_Body Text Indent',
            'normal': 'Body Text Indent',
        },
        'alignment': 'JUSTIFY',
        'font_size': 10.0,
        'space_before': 0.0,
        'space_after': 0.0,
        'first_line_indent': 9.35  # 0.33cm
    }
}
EXTRA_RULES = ''
PARAGRAPH_STYLE_EXCEPTIONS = ['JACoW_Bulleted List', 'JACoW_Numbered list', 'Bulleted List', 'Numbered list']

HELP_INFO = 'SCEParag'
ALL_HELP_INFO = 'CSEParsedDocument'
ALL_EXTRA_INFO = {
    'title':'Breakdown',
    'headers': '<thead><tr><th style="width:60%">Text</th><th style="width:15%">Style</th><th style="width:15%">In Table</th><th style="width:10%">JACoW Style</th> </tr></thead>',
    'columns': ['text', 'style', 'in_table', 'style_ok']
}

PARAGRAPH_SIZE_MIN = 50


def parse_all_paragraphs(doc):
    all_paragraphs = []
    styles = []
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip():
            style_ok = p.style.name in VALID_STYLES or p.style.name in VALID_NON_JACOW_STYLES
            if not style_ok:
                style_ok = 2
            s = [s for s in styles if p.style.name == s['name']]
            if s:
                s[0]['count'] = s[0]['count'] + 1
            else:
                styles.append({'name': p.style.name, 'count': 1})

            all_paragraphs.append({
                'index': i,
                'style': p.style.name,
                'text': get_text(p),
                'style_ok': style_ok,
                'in_table': 'No',
            })

    # TODO Display style summary (and decide whether to include styles of items in tables
    # for s in styles:
    #    print(f"{s['name']}: {s['count']}")

    # search for paragraphs in tables
    count = 1
    show_all = True
    for t in doc.tables:
        if len(t.rows) > 2 and not show_all:
            continue
        for r in t.rows:
            if len(r.cells) > 2 and not show_all:
                continue
            cell_count = 1
            for c in r.cells:
                for p in c.paragraphs:
                    if p.text.strip():
                        style_ok = p.style.name in VALID_STYLES or p.style.name in VALID_NON_JACOW_STYLES
                        if not style_ok:
                            style_ok = 2
                        all_paragraphs.append({
                            'index': 0,
                            'style': p.style.name,
                            'text': get_text(p),
                            'style_ok': style_ok,
                            'in_table': f"Table {count}:<br/>row {r._index + 1}, col {cell_count}"
                        })
                cell_count = cell_count + 1
        count = count + 1
    return all_paragraphs


def get_paragraphs(doc):
    data = iter(doc.paragraphs)
    paragraphs = []
    style_compare = PARAGRAPH_STYLES['normal']
    # don't start looking until abstract header
    for p in data:
        if p.text.strip().lower() == 'abstract':
            break

    for i, p in enumerate(data):
        # only for paraphaphs that are not references, figure captions, headings
        text = p.text.strip()
        text = re.sub(' +', ' ', text)

        if text:
            # no need to check after references
            if text.lower() == 'references':
                break

            # ignore table and figure cations
            # TODO check if any real paragraphs start with figure or table
            if text.startswith('Table ') or text.startswith('Figure ') or text.startswith('Fig. '):
                continue

            # ignore if heading style
            if [name for name, h in HEADING_STYLES.items() if
                        p.style.name in [h['styles']['jacow'], h['styles']['normal']]]:
                continue

            # ignore if one of the style exceptions like lists
            if p.style.name in PARAGRAPH_STYLE_EXCEPTIONS:
                continue

            # ignore if starts with lowercase
            if text[0:1].islower():
                continue

            # short paragraphs are probably headings
            if len(text) < PARAGRAPH_SIZE_MIN:
                continue

            style_ok, detail = check_style(p, style_compare)
            if detail['all_caps']:
                text = text.upper()

            paragraph_details = {
                'type': 'Paragraph',
                'style': p.style.name,
                'style_ok': style_ok,
                'text': text
            }
            paragraph_details.update(detail)
            paragraphs.append(paragraph_details)

    return paragraphs


def get_paragraph_summary(doc):
    paragraphs = get_paragraphs(doc)
    return {
        'title': 'Paragraphs',
        'rules': PARAGRAPH_STYLES,
        'extra_rules': EXTRA_RULES,
        'help_info': HELP_INFO,
        'ok': all([tick['style_ok'] for tick in paragraphs]),
        'message': 'Paragraph issues',
        'details': paragraphs,
        'anchor': 'paragraphs',
        'show_total': True,
    }


def get_all_paragraph_summary(doc):
    all_summary = parse_all_paragraphs(doc)
    ok = all([tick['style_ok'] is True for tick in all_summary])
    if not ok:
        ok = 2
    return {
        'title': 'Parsed Document',
        'help_info': ALL_HELP_INFO,
        'extra_info': ALL_EXTRA_INFO,
        'ok': ok,
        'message': 'Not using only JACoW Styles',
        'details': all_summary,
        'anchor': 'list',
        'show_total': True,
    }
