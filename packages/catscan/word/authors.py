import re
from styles import check_style_detail

NON_BREAKING_SPACE = '\u00A0'
LINE_TERMINATOR_CHARS = ['\u000A', '\u000B', '\u000C', '\u000D', '\u0085', '\u2028', '\u2029', '\n', '\\n']
# line terminator chars respectively:
# line feed, vertical tab, form feed, carriage return,
# next line, line separator, paragraph separator

STYLES = {
    'normal': {
       'type': 'Author List',
       'styles': {
           'jacow': 'JACoW_Author List',
           'normal': 'Author List',
       },
       'alignment': 'CENTER',
       'font_size': 12.0,
       'space_before': 9.0,
       'space_after': 12.0,
       'bold': [None, False],
       'italic': [None, False],
   }
}
EXTRA_RULES = ['Case: UPPER and lowercase']
HELP_INFO = 'SCEAuthors'

IGNORE = ['P.R. China']

def get_author_details(p):
    superscript_removed_text = ''  # remove superscript footnotes
    for r in p.runs:
        superscript_removed_text += r.text if not r.font.superscript else ''
    author_detail = {
        'text': superscript_removed_text,
        'original_text': p.text,
    }
    return author_detail


def get_author_summary(paragraphs):
    style_compare = STYLES['normal']
    author_details = []
    for p in paragraphs:
        if p.text.strip():
            detail = get_author_details(p)
            detail.update(check_style_detail(p, style_compare))
            title_style_ok = p.style.name == style_compare['styles']['jacow']
            detail.update({'title_style_ok': title_style_ok, 'style': p.style.name})
            author_details.append(detail)

    return {
        'details': author_details,
        'rules': STYLES,
        'extra_rules': EXTRA_RULES,
        'help_info': HELP_INFO,
        'title': 'Author',
        'ok': all([tick['style_ok'] for tick in author_details]),
        'message': 'Author issues',
        'anchor': 'author'
    }


def parse_author_latex(part):
    # TODO finish this better way of parsing author and affiliation
    authors = ['']
    author_count = 0
    for i, p in enumerate(part.contents):
        if isinstance(p, str):
            # check whether there is \\ optionally followed by \n\t\t which is used to split authors
            if '\\' in p:
                author_split = p.split('\\')
                for j, author in enumerate(author_split):
                    author_text = author.replace('\n\t\t', '')
                    if j == 0:
                        if author_count + 1 > len(authors):
                            authors.append(author_text)
                        else:
                            authors[author_count] = authors[author_count] + author_text
                    elif not author_text == '':
                        author_count = author_count + 1
                        authors.append(author_text)
            else:
                if author_count + 1 > len(authors):
                    authors.append(p)
                else:
                    authors[author_count] = authors[author_count] + p
        elif p.name in ['thanks']:
            # ignore thanks but assume that indicates the start of new author info
            author_count = author_count + 1
            continue
        elif p.name in ['textsuperscript']:
            # ignore textsuperscript notes
            continue
    return authors


def get_author_summary_latex(part):
    """
    Example from JACoW example latex file
    (double \\ before author, thanks and textsuperscript were single in example but causes issues in this comment)
    \\author{A. N. Author\\thanks{email address}, H. Coauthor, Name of Institute or Affiliation, City, Country \\
            P. Contributor\\textsuperscript{1}, Name of Institute or Affiliation, City, Country \\
            \\textsuperscript{1}also at Name of Secondary Institute or Affiliation, City, Country}

    :param part: author component of the parsed tex document
    :return: dict with summary result info
    """
    if part and part.string:
        text = ''
        for i, p in enumerate(part.contents):
            if isinstance(p, str):
                author_text = p.replace('\n\t\t', '')
                author_text = author_text.replace('\\\\', ', ')
                author_text = author_text.replace(',,', ',')
                author_text = author_text.replace('  ', ' ')
                for item in IGNORE:
                    author_text = author_text.replace(item, '')
                text = text + author_text
            elif p.name in ['thanks', 'textsuperscript']:
                # ignore text in thanks and textsuperscript
                continue

        return {'original_text': part.string, 'text': text, 'title': 'Author', 'ok': True, 'extra_info': f'Author: {text}'}

    return {'original_text': '', 'text': '', 'title': 'Author', 'ok': False, 'extra_info': f'No Author found'}


def get_author_list(text):
    """function to extract authors from some text that will also include
    associations

    example input:

    `J. C. Jan†, F. Y. Lin, Y. L. Chu, C. Y. Kuo, C. C. Chang, J. C. Huang and C. S. Hwang,
National Synchrotron Radiation Research Center, Hsinchu, Taiwan, R.O.C`

    or

    `M.B. Behtouei, M. Migliorati, L. Palumbo, B. Spataro, L. Faillace`

    assumptions:

    - if you split by ', ' and the second character of a token is a '.' period
        then its probably a valid token (an author) but this is not guaranteed
        (see above example that ends in 'R.O.C')

    - There can be multiple initials as evidenced above.

    - Initials may not necessarily be split by a space.

    watch out for:

    - hypenated names: 'B. Walasek-Hoehne'
    - hyphenated initials: 'E. J-M. Voutier' 'J.-L. Vay'
    - multiple surnames: 'M.J. de Loos' 'S.B. van der Geer' 'A. Martinez de la Ossa' 'N. Blaskovic Kraljevic' 'G. Guillermo Cant�n' 'C. Boscolo Meneguolo'
    - surname with apostrophes: 'G. D'Alessandro'
    - extra stuff tacked on: 'S.X. Zheng [on leave]' 'G.R. Li [on leave]' (from the csv file)
    - one rare instance of non-period separated initials: 'Ph. Richerot (from csv file)

    my pattern of a name which should match vast majority of names while not matching vast majority of non-names:
    single letter, followed by a period, potentially followed by a space but
    not always, repeated n times, and ending in a word of more than one character
    which may contain hyphens, apostrophes, repeated n times, and finally
    finishing with a comma

    word character followed by dot and potentially space, repeated n times
    then
    word character repeated n times

    /(\\w\\.\\ ?)+(\\w+\\ ?)+/g   (note this comment had to double up the escape backslashes)

    (https://regexr.com/)

    """
    newline_fixed_text = text
    for newline_char in LINE_TERMINATOR_CHARS:
        newline_fixed_text = newline_fixed_text.replace(newline_char, ' , ')
    potential_authors = newline_fixed_text.replace(NON_BREAKING_SPACE, ' ').replace(' and ', ', ').split(', ')
    filtered_authors = list()
    my_name_pattern = re.compile("(-?\\w\\.\\ ?)+([\\w]{2,}\\ ?)+")
    # the allowance of an optional hyphen preceding an initial is to satisfy a
    # common pattern observed with the papers coming out of asia.
    for author in potential_authors:
        if my_name_pattern.match(author):   # match has an implied ^ at the start
            # which is ok for our purposes.
            filtered_authors.append(author)
    return filtered_authors
