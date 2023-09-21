from docx.oxml.text.font import CT_RPr
from lxml.etree import _Element

VALID_LANGUAGES = ['en-US', 'en-GB', 'en-AU', 'en-NZ']
EXTRA_RULES = [
'''<p>Document overall language should be set to English for proofing tools.<br/>
Below are the codes that should be in the list</p>
<table class="table is-bordered">
    <thead><tr><th colspan="2">English Codes</th></tr></thead>
    <tbody>
    <tr><td>en-GB</td><td>English (United Kingdom)</td></tr>
    <tr><td>en-US</td><td>English (United States)</td></tr>
    <tr><td>en-AU</td><td>English (Australia)</td></tr>
    <tr><td>en-nz</td><td>English (New Zealand)</td></tr>
    </tbody>
</table>
If you want to look up other codes, you can do so <a href="https://www.andiamo.co.uk/resources/iso-language-codes/" target="_blank">here</a>'''
]
HELP_INFO = 'SCELanguages'


# simple unique list of languages
def get_language_tags(doc):
    tags = get_language_tags_location(doc)
    # get unique list
    return list(dict.fromkeys(tags.values()))


def get_language_tags_location(doc):
    tags = {}
    if doc.core_properties.language != '':
        tags['-1'] = doc.core_properties.language
    for i, p in enumerate(doc.paragraphs):
        for r in p.runs:
            for c in r.element.iterchildren():
                if isinstance(c, CT_RPr):
                    for cc in c.iterchildren():
                        if isinstance(cc, _Element) and 'lang' in str(cc):
                            tags[r.text] = cc.items()[0][1]
    # get unique list
    return tags


def get_language_summary(doc):
    language_summary = get_language_tags(doc)
    languages = get_language_tags_location(doc)
    ok = len([languages[lang] for lang in languages if languages[lang] not in VALID_LANGUAGES]) == 0

    if ok:
        extra_info = 'English proofing languages were found.'
    else:
        extra_info = 'Non English proofing languages were found in document, please set all document content proofing language to English.'

    return {
        'title': 'Languages',
        'extra_rules': EXTRA_RULES,
        'help_info': HELP_INFO,
        'extra_info': extra_info,
        'ok': ok,
        'message': 'Language issues',
        'details': language_summary,
        'extra': languages,
        'anchor': 'languages'
    }
