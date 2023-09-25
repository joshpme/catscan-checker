import re
from collections import OrderedDict
from itertools import chain
from styles import check_style

RE_FIG_TITLES = re.compile(r'(^Figure \d+[.:])')
RE_WRONG_TITLES = re.compile(r'(^Fig.\s?\d+|^Figure\s?\d+[.\s]+)')
RE_FIG_IN_TEXT = re.compile(r'(Fig.\s?\d+|Figure\s?\d+[.\-\s]+)')

STYLES = {
    'SingleLine': {
        'type': 'Figure - Single Line',
        'styles': {
            'jacow': 'Figure Caption',
            'normal': 'Caption',
        },
        'alignment': 'CENTER',
        'font_size': 10.0,
        'space_before': 3.0,
        'space_after': ['>=', 3.0],
        'bold': None,
        'italic': None,
    },
    'MultiLine': {
        'type': 'Figure - Multi Line',
        'styles': {
            'jacow': 'Figure Caption Multi Line',
        },
        'alignment': 'JUSTIFY',
        'font_size': 10.0,
        'space_before': 3.0,
        'space_after': ['>=', 3.0],
        'bold': None,
        'italic': None,
    }
}

VALID_FIGURE_STYLES = ['Figure Caption', 'Figure Caption Multi Line', 'Caption', 'Caption Multi Line']

EXTRA_RULES = [
    'Figure captions must be directly below the figure',
    'Figure must be numbered in the order they are referred to in the main text.',
    'Figure numbers must be unique and not duplicated, or skip numbers in the series.',
    'Figure Captions 1 line long must be “centred” (“Figure Caption” Style). Figure captions 2 or more lines must be “justified” (“Caption Multi Line” Style).',
    'Figure captions and figures are not to be indented.',
    'Figure captions must start with “Figure n:”.',
    'In text references to the figure if mid-sentence must be “Fig. n”, at the start of a sentence it must be “Figure n”.',
    'Figures must have a “.” On the end of the final line.',
]
HELP_INFO = 'CSEFigures'
EXTRA_INF0 = {
    'title':'Use Breakdown',
    'headers': '<thead><tr><th>No.</th><th colspan="2">Caption</th><th>Unique</th><th colspan="2">References</th><th width="30%">Text</th></tr></thead>',
    'columns': ['id', 'name', 'caption_ok', 'unique_ok', 'refs', 'used_ok', 'text'],
    'multi': True
}

def _fig_to_int(s):
    return int(''.join(filter(str.isdigit, s)))


def get_figure_style_details(p):
    text = p.text.strip()
    figure_compare = STYLES['SingleLine']

    # 55 chars is approx where it changes from 1 line to 2 lines
    if len(text) > 55:
        figure_compare = STYLES['MultiLine']

    style_ok, detail = check_style(p, figure_compare)
    style_name = p.style.name
    if p.style.name not in VALID_FIGURE_STYLES:
        final_style_ok = 2
    else:
        final_style_ok = style_ok and p.style.name in VALID_FIGURE_STYLES

    if 40 < len(text) < 80:
        final_style_ok = 2
        style_name = f"'{style_name}' checking against type '{figure_compare['styles']['jacow']}'"

    return final_style_ok, style_name, detail


def extract_figures(doc):
    figures_refs = []
    figures_captions = []
    wrong_captions = []

    def _find_figure_captions(p):
        for f in RE_FIG_TITLES.findall(p.text.strip()):
            text = p.text.strip()
            final_style_ok, style_name, detail = get_figure_style_details(p)

            _id = _fig_to_int(f)
            figure_detail = dict(
                id=_id,
                name=f,
                text=text,
                style=style_name,
                style_ok=final_style_ok,
            )
            figure_detail.update(detail)
            figures_captions.append(figure_detail)

        # find test for wrong versions
        for f in RE_WRONG_TITLES.findall(p.text.strip()):
            # 55 chars is approx where it changes from 1 line to 2 lines
            text = p.text.strip()
            final_style_ok, style_name, detail = get_figure_style_details(p)

            _id = _fig_to_int(f)
            figure_detail = dict(
                id=_id,
                name=f,
                text=text,
                style=style_name,
                style_ok=final_style_ok,
            )
            figure_detail.update(detail)
            wrong_captions.append(figure_detail)

    for p in doc.paragraphs:
        # find references to figures
        for f in iter(f.strip() for f in RE_FIG_IN_TEXT.findall(p.text)):
            if f.endswith('.') and p.text.strip().startswith(f):
                # probably a figure caption with . instead of :
                continue
            figures_refs.append(dict(id=_fig_to_int(f), name=f))

        # find figure captions
        _find_figure_captions(p)

    # search for figure captions in tables
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs:
                    _find_figure_captions(p)

    figures = OrderedDict()
    # no figure found means there is probably an error with parsing though.
    if len(figures_refs) == 0 and len(figures_captions) == 0 and len(wrong_captions) == 0:
        _last = 0
    else:
        _last = max(
            chain.from_iterable(
                [
                    (fig['id'] for fig in figures_captions),
                    (fig['id'] for fig in wrong_captions),
                    (fig['id'] for fig in figures_refs),
                ]
            )
        )

    for i in range(1, _last + 1):
        caption = [c for c in figures_captions if c['id'] == i]
        wrong = [c for c in wrong_captions if c['id'] == i]
        figures[i] = []
        if caption:
            for c in caption:
                refs = list(f['name'] for f in figures_refs if f['id'] == i)
                figure = {
                    'id': i,
                    'refs': refs,
                    'unique_ok': len(caption) == 1,
                    'found_ok': len(caption) > 0,
                    'caption_ok': len(caption) == 1 and c['name'].endswith(':'),
                    'used_ok': len(refs) > 0
                }
                figure.update(**c)
                figures[i].append(figure)
        elif wrong:
            for c in wrong:
                refs = list(f['name'] for f in figures_refs if f['id'] == i)
                figure = {
                    'id': i,
                    'refs': refs,
                    'unique_ok': len(wrong) == 1,
                    'found_ok': len(wrong) > 0,
                    'caption_ok': False,
                    'used_ok': len(refs) > 0
                }
                figure.update(**c)
                figures[i].append(figure)
        else:
            refs = list(f['name'] for f in figures_refs if f['id'] == i)
            figures[i].append({
                'id': i,
                'refs': refs,
                'unique_ok': len(caption) == 1,
                'found_ok': len(caption) > 0,
                'caption_ok': len(caption) == 1 and c['name'].endswith(':'),
                'used_ok': len(refs) > 0
            })

    return figures


def get_figure_summary(doc):
    figures = extract_figures(doc)
    ok = True
    # Use checks first
    for _, sub in figures.items():
        ok = ok and all(
            [item['caption_ok'] and item['unique_ok'] and item['used_ok'] and item['found_ok'] for item in sub]
        )

    # Check style use checks pass
    if ok:
        for _, sub in figures.items():
            # Break out of outer loop too if false
            if not ok:
                break

            for item in sub:
                if not item['style_ok']:
                    # If find a false then the result is false
                    ok = False
                    break
                elif item['style_ok'] == 2:
                    # If find a 2 (?) then result is 2 unless a false is found later
                    ok = 2

    return {
        'title': 'Figures',
        'rules': STYLES,
        'extra_rules': EXTRA_RULES,
        'help_info': HELP_INFO,
        'extra_info': EXTRA_INF0,
        'ok': ok,
        'message': 'Figure issues',
        'details': figures.values(),
        'anchor': 'figures',
        'show_total': True,
    }
