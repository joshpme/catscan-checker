import re
from itertools import chain
from styles import check_style, get_style_font_run

RE_REFS_LIST = re.compile(r'^\[([\d]+)\]')
RE_REFS_LIST_TAB = re.compile(r'^\[([\d]+)\]\t')
RE_REFS_INTEXT = re.compile(r'(?<!^)\[([\d ,-]+)\]')

STYLES = {
    'LessThanNineTotal': {
        'type': 'References when ≤ 9',
        'styles': {
            'jacow': 'JACoW_References when ≤ 9',
        },
        'alignment': 'JUSTIFY',
        'font_size': 9.0,
        'space_before': 0.0,
        'space_after': 3.0,
        # 'hanging_indent':  0.0,
        'first_line_indent': -14.75,  # 0.52 cm,
    },
    'LessThanNine': {
        'type': 'Reference #1-9 when >= 10 Refs',
        'styles': {
            'jacow': 'JACoW_Reference #1-9 when >= 10 Refs',
        },
        'alignment': 'JUSTIFY',
        'font_size': 9.0,
        'space_before': 0.0,
        'space_after': 3.0,
        # 'hanging_indent': 0,  # 0.16 cm,
        'first_line_indent': -14.75,  # 0.52 cm,
    },
    'MoreThanNine': {
        'type': 'Reference #10 onwards',
        'styles': {
            'jacow': 'JACoW_Reference #10 onwards',
        },
        'alignment': 'JUSTIFY',
        'font_size': 9.0,
        'space_before': 0.0,
        'space_after': 3.0,
        # 'hanging_indent':  0.0,
        'first_line_indent': -19.3,  # 0.68 cm,
    }
}
EXTRA_RULES = [
    'All references must be ordered in the reference list based on when they first are referred to in the main text.',
    'References in the main text can be [n], or [n1, n2, n5, etc.], or [n – n3].',
    'A reference can be referred to multiple times in the main text as required..',
    'All references in the reference list must be sited in the main text at least once.',
    'Reference lists which have 9 or less references must be “JACoW_Reference when &lt;= 9 Refs” Style.',
    'When greater than 9 references the first 9 must be “JACoW_Reference #1-9 when &gt;= 10 Refs” Style, '
    'and 10 and onwards must be “JACoW_Reference #10 onwards” Style.',
    'All references must be numbered [n] and have a tab between the ] and the start of the reference text. '
    '(note many authors put spaces in which stuffs up the spacing.',
    'DOIs and URLs should be font 8pt Liberation Mono',
]
HELP_INFO = 'SCEReferences'
EXTRA_INFO = {
    'title': 'Use Breakdown',
    'headers': '<thead><tr><th>No.</th><th colspan="3">Text</th><th>Used</th><th>Order</th><th>Unique</th></tr></thead>',
    'columns': ['id', 'text', 'text_error', 'text_ok', 'used_ok', 'order_ok', 'unique_ok']
}


def _ref_to_int(ref):
    try:
        return [int(ref)]
    except ValueError:
        if ',' in ref:
            return list(
                chain.from_iterable(_ref_to_int(i) for i in ref.split(',') if i.strip())
            )
        elif '-' in ref:
            return list(range(*(int(v) + i for i, v in enumerate(ref.split('-')))))
        raise


def extract_references(doc, strict_styles=False):
    data = iter(doc.paragraphs)
    references_in_text = []

    # don't start looking until abstract header
    for p in data:
        if p.text.strip().lower() == 'abstract':
            break
    else:
        raise Exception('Abstract header not found')

    # find all references in text and references list
    references_list = []
    ref_list_start = 0
    for i, p in enumerate(data):
        for ref in RE_REFS_INTEXT.findall(p.text):
            references_in_text.append(_ref_to_int(ref))

        refs = RE_REFS_LIST.findall(p.text.strip())
        if refs:
            for ref in refs:
                if int(ref) == 1:
                    ref_list_start = i
                references_list.append(
                    dict(id=int(ref), text=p.text.strip(), style=p.style.name, p=p)
                )
        elif ref_list_start > 0:
            should_find = references_list[-1]['id'] + 1
            if str(should_find) in p.text.strip()[:4]:  # only look in first 4 chars
                references_list.append(
                    dict(
                        id=should_find,
                        text=p.text.strip(),
                        style=p.style.name,
                        p=p,
                        text_ok=False,
                        text_error=f"Number format wrong should be [{should_find}]"
                    )
                )

    # check references in body are in correct order
    stack = [0]
    seen = []
    out_of_order = set()
    for _range in references_in_text:
        for _ref in _range:
            if _ref in stack:
                continue
            if _ref - stack[-1] == 1:
                stack.append(_ref)
            elif _ref not in seen:
                seen.append(_ref)
        for _ref in seen.copy():
            if _ref - stack[-1] == 1:
                stack.append(_ref)
                seen.remove(_ref)
        if len(seen) > 0:
            out_of_order.update(seen)

    # get a set of references so we know which ones are used
    used_references = set(chain.from_iterable(references_in_text))

    # check reference styles, order etc
    ref_count = len(references_list)
    seen = set()
    for i, ref in enumerate(references_list, 1):
        if ref['id'] in seen:
            ref['duplicate'] = True
            ref['unique_ok'] = False
        else:
            ref['unique_ok'] = True
        seen.add(ref['id'])
        ref['order_ok'] = i == ref['id'] and i not in out_of_order
        ref['used_ok'] = i in used_references
        ref['text_ok'] = True
        ref['text_error'] = ''

        if not RE_REFS_LIST_TAB.search(ref['text']):
            ref['text_error'] = f"Number format error should be [{i}] followed by a tab"
            ref['text_ok'] = False

        # check for doi or urls
        starts = ['doi:', 'http://www.', 'http://', 'https://', 'www.']
        url_font = {'name': 'Liberation Mono', 'size': 8}
        has_url = has_url_error = False
        for r in ref['p'].runs:
            if r.style is not None:
                text = r.text.strip()
                for s in starts:
                    if text.startswith(s):
                        has_url = True
                        bold, italic, font_size, font_name, all_caps = \
                            get_style_font_run(r)

                        if not font_size or not font_name == url_font['name'] \
                                or not font_size == url_font['size']:
                            has_url_error = True
                            ref['text_ok'] = False
                        break
                    elif s in text:
                        # means that the font name and size did not change at start.
                        # may be an issue if two DOIs or URLs after one another
                        has_url = True
                        has_url_error = True
                        ref['text_ok'] = False

        if has_url_error:
            ref['text_error'] = ref['text_error'] + \
                                f"URLs and DOIs should be {url_font['name']} and size {url_font['size']}pt"

        if ref_count <= 9:
            style_compare = STYLES['LessThanNineTotal']
        else:
            if i <= 9:
                style_compare = STYLES['LessThanNine']
            else:
                style_compare = STYLES['MoreThanNine']

        style_ok, detail = check_style(
            ref['p'],
            style_compare,
            url={'has_url': has_url, 'url_font': url_font, 'starts': starts}
        )
        if strict_styles:
            ref['style_ok'] = ref['style'] == style_compare['styles']['jacow']
            if not ref['style_ok']:
                ref['style'] = f"{ref['style']} should be '{style_compare['styles']['jacow']}'"
        else:
            ref['style_ok'] = style_ok

        ref.update(detail)
        # delete p from dictionary since it is un unserialisable Paragragh
        del ref['p']

    return references_in_text, references_list


def get_reference_summary(doc):
    references_in_text, references_list = extract_references(doc)
    # Use checks first
    ok = references_list and all([
            all([tick['text_ok'], tick['used_ok'], tick['order_ok'], tick['unique_ok']])
            for tick in references_list])

    # Check style use checks pass
    if ok:
        for tick in references_list:
            if not tick['style_ok']:
                # If find a false then the result is false
                ok = False
                break
            elif tick['style_ok'] == 2:
                # If find a 2 (?) then result is 2 unless a false is found later
                ok = 2

    return {
        'title': 'References',
        'rules': STYLES,
        'extra_rules': EXTRA_RULES,
        'help_info': HELP_INFO,
        'extra_info': EXTRA_INFO,
        'ok': ok,
        'message': 'Reference issues',
        'details': references_list,
        'anchor': 'references',
        'show_total': True,
    }