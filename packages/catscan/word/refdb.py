import re
import pymysql.cursors
import os
from utils import remove_white_space

SPMS_HELP_INFO = 'CSESPMSCeck'
SPMS_EXTRA_INFO = {
    'title': 'Title and Author Breakdown',
    'headers': '<thead><tr><th>Type</th><th>Match</th><th>Document</th><th>SPMS</th></tr></thead>',
    'columns': ['type', 'match_ok', 'document', 'spms']
}
BASE_URL = "https://refs.jacow.org"


class PaperNotFoundError(Exception):
    """Raised when the paper submitted by a user has no matching entry in the
    spms references list of papers"""
    pass



def get_references(conference_id):
    cnx = pymysql.connect(
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASS'),
        host=os.getenv('MYSQL_HOST'),
        port=os.getenv('MYSQL_PORT'),
        database=os.getenv('MYSQL_DB'),
        cursorclass=pymysql.cursors.DictCursor)
    cursor = cnx.cursor()

    query = """SELECT * FROM reference WHERE conference_id = %s"""
    cursor.execute(query, (conference_id, ))

    references = []
    for data in cursor:
        references.append(data)

    cursor.close()
    cnx.close()

    return references


NON_BREAKING_SPACE = '\u00A0'
LINE_TERMINATOR_CHARS = ['\u000A', '\u000B', '\u000C', '\u000D', '\u0085', '\u2028', '\u2029', '\n', '\\n']


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
        if my_name_pattern.match(author):  # match has an implied ^ at the start
            # which is ok for our purposes.
            filtered_authors.append(author)
    return filtered_authors


def normalize_author_name(author_name):
    """returns a normalized name suitable for comparing"""
    # ensure periods are followed by a space:
    normalized_name = author_name.replace('.', '. ').replace('  ', ' ')
    # remove hyphens (sometimes inconsistently applied):
    normalized_name = normalized_name.replace('-', '')
    # remove asterisks (sometimes included in document authors text):
    normalized_name = normalized_name.replace('*', '')
    # remove formatting characters occasionally observed:
    normalized_name = normalized_name.replace('†', '')
    # strip possible extra whitespace:
    normalized_name = normalized_name.strip()
    return normalized_name


def get_surname(author_name):
    """finds the index of the last period in the string then returns the substring
    starting 2 positions forward from that period"""
    return author_name[author_name.rfind('.') + 2:]


def get_first_last_only(normalized_author_name):
    """given an author name returns a version with only the first initial
    eg: given 'T. J. Z. Bytes' returns 'T. Bytes' """
    first_intial = normalized_author_name[:2]
    surname = get_surname(normalized_author_name)
    return ' '.join((first_intial, surname))


# below taken from https://stackoverflow.com/questions/6837148/change-foreign-characters-to-their-normal-equivalent
ACCENTED_CHARS_DICT = {'á': 'a', 'Á': 'A', 'à': 'a', 'À': 'A', 'ă': 'a',
                       'Ă': 'A', 'â': 'a', 'Â': 'A', 'å': 'a', 'Å': 'A',
                       'ã': 'a', 'Ã': 'A', 'ą': 'a', 'Ą': 'A', 'ā': 'a',
                       'Ā': 'A', 'ä': 'ae', 'Ä': 'AE', 'æ': 'ae', 'Æ': 'AE',
                       'ḃ': 'b', 'Ḃ': 'B', 'ć': 'c', 'Ć': 'C', 'ĉ': 'c',
                       'Ĉ': 'C', 'č': 'c', 'Č': 'C', 'ċ': 'c', 'Ċ': 'C',
                       'ç': 'c', 'Ç': 'C', 'ď': 'd', 'Ď': 'D', 'ḋ': 'd',
                       'Ḋ': 'D', 'đ': 'd', 'Đ': 'D', 'ð': 'dh', 'Ð': 'Dh',
                       'é': 'e', 'É': 'E', 'è': 'e', 'È': 'E', 'ĕ': 'e',
                       'Ĕ': 'E', 'ê': 'e', 'Ê': 'E', 'ě': 'e', 'Ě': 'E',
                       'ë': 'e', 'Ë': 'E', 'ė': 'e', 'Ė': 'E', 'ę': 'e',
                       'Ę': 'E', 'ē': 'e', 'Ē': 'E', 'ḟ': 'f', 'Ḟ': 'F',
                       'ƒ': 'f', 'Ƒ': 'F', 'ğ': 'g', 'Ğ': 'G', 'ĝ': 'g',
                       'Ĝ': 'G', 'ġ': 'g', 'Ġ': 'G', 'ģ': 'g', 'Ģ': 'G',
                       'ĥ': 'h', 'Ĥ': 'H', 'ħ': 'h', 'Ħ': 'H', 'í': 'i',
                       'Í': 'I', 'ì': 'i', 'Ì': 'I', 'î': 'i', 'Î': 'I',
                       'ï': 'i', 'Ï': 'I', 'ĩ': 'i', 'Ĩ': 'I', 'į': 'i',
                       'Į': 'I', 'ī': 'i', 'Ī': 'I', 'ĵ': 'j', 'Ĵ': 'J',
                       'ķ': 'k', 'Ķ': 'K', 'ĺ': 'l', 'Ĺ': 'L', 'ľ': 'l',
                       'Ľ': 'L', 'ļ': 'l', 'Ļ': 'L', 'ł': 'l', 'Ł': 'L',
                       'ṁ': 'm', 'Ṁ': 'M', 'ń': 'n', 'Ń': 'N', 'ň': 'n',
                       'Ň': 'N', 'ñ': 'n', 'Ñ': 'N', 'ņ': 'n', 'Ņ': 'N',
                       'ó': 'o', 'Ó': 'O', 'ò': 'o', 'Ò': 'O', 'ô': 'o',
                       'Ô': 'O', 'ő': 'o', 'Ő': 'O', 'õ': 'o', 'Õ': 'O',
                       'ø': 'oe', 'Ø': 'OE', 'ō': 'o', 'Ō': 'O', 'ơ': 'o',
                       'Ơ': 'O', 'ö': 'oe', 'Ö': 'OE', 'ṗ': 'p', 'Ṗ': 'P',
                       'ŕ': 'r', 'Ŕ': 'R', 'ř': 'r', 'Ř': 'R', 'ŗ': 'r',
                       'Ŗ': 'R', 'ś': 's', 'Ś': 'S', 'ŝ': 's', 'Ŝ': 'S',
                       'š': 's', 'Š': 'S', 'ṡ': 's', 'Ṡ': 'S', 'ş': 's',
                       'Ş': 'S', 'ș': 's', 'Ș': 'S', 'ß': 'SS', 'ť': 't',
                       'Ť': 'T', 'ṫ': 't', 'Ṫ': 'T', 'ţ': 't', 'Ţ': 'T',
                       'ț': 't', 'Ț': 'T', 'ŧ': 't', 'Ŧ': 'T', 'ú': 'u',
                       'Ú': 'U', 'ù': 'u', 'Ù': 'U', 'ŭ': 'u', 'Ŭ': 'U',
                       'û': 'u', 'Û': 'U', 'ů': 'u', 'Ů': 'U', 'ű': 'u',
                       'Ű': 'U', 'ũ': 'u', 'Ũ': 'U', 'ų': 'u', 'Ų': 'U',
                       'ū': 'u', 'Ū': 'U', 'ư': 'u', 'Ư': 'U', 'ü': 'ue',
                       'Ü': 'UE', 'ẃ': 'w', 'Ẃ': 'W', 'ẁ': 'w', 'Ẁ': 'W',
                       'ŵ': 'w', 'Ŵ': 'W', 'ẅ': 'w', 'Ẅ': 'W', 'ý': 'y',
                       'Ý': 'Y', 'ỳ': 'y', 'Ỳ': 'Y', 'ŷ': 'y', 'Ŷ': 'Y',
                       'ÿ': 'y', 'Ÿ': 'Y', 'ź': 'z', 'Ź': 'Z', 'ž': 'z',
                       'Ž': 'Z', 'ż': 'z', 'Ż': 'Z', 'þ': 'th', 'Þ': 'Th',
                       'µ': 'u', 'а': 'a', 'А': 'a', 'б': 'b', 'Б': 'b',
                       'в': 'v', 'В': 'v', 'г': 'g', 'Г': 'g', 'д': 'd',
                       'Д': 'd', 'е': 'e', 'Е': 'E', 'ё': 'e', 'Ё': 'E',
                       'ж': 'zh', 'Ж': 'zh', 'з': 'z', 'З': 'z', 'и': 'i',
                       'И': 'i', 'й': 'j', 'Й': 'j', 'к': 'k', 'К': 'k',
                       'л': 'l', 'Л': 'l', 'м': 'm', 'М': 'm', 'н': 'n',
                       'Н': 'n', 'о': 'o', 'О': 'o', 'п': 'p', 'П': 'p',
                       'р': 'r', 'Р': 'r', 'с': 's', 'С': 's', 'т': 't',
                       'Т': 't', 'у': 'u', 'У': 'u', 'ф': 'f', 'Ф': 'f',
                       'х': 'h', 'Х': 'h', 'ц': 'c', 'Ц': 'c', 'ч': 'ch',
                       'Ч': 'ch', 'ш': 'sh', 'Ш': 'sh', 'щ': 'sch', 'Щ': 'sch',
                       'ъ': '', 'Ъ': '', 'ы': 'y', 'Ы': 'y', 'ь': '', 'Ь': '',
                       'э': 'e', 'Э': 'e', 'ю': 'ju', 'Ю': 'ju', 'я': 'ja',
                       'Я': 'ja'}


def transliterate_accents(name):
    name_copy = name
    for letter in name:
        if ord(letter) > 127:
            if letter in ACCENTED_CHARS_DICT:
                name_copy = name_copy.replace(letter, ACCENTED_CHARS_DICT[letter])
    return name_copy


def build_comparison_author_objects(author_names):
    author_compare_objects = list()
    for author in author_names:
        original_value = author
        compare_value = normalize_author_name(author)
        compare_first_last = get_first_last_only(compare_value)
        compare_last = get_surname(compare_first_last)
        compare_transliterated = transliterate_accents(compare_first_last)
        author_compare_objects.append(
            {
                'original-value': original_value,
                'compare-value': compare_value,
                'compare-first-last': compare_first_last,
                'compare-transliterated': compare_transliterated,
                'compare-last': compare_last
            })
    return author_compare_objects


def get_author_list_report(document_text, authors):
    """Compares two lists of authors (one sourced from the uploaded document file
    and one sourced from the corresponding paper's entry in the SPMS references
    csv file) and produces a dict array report of the form:
        [
            {
            match: True,
            exact: True,
            document: "Y. Z. Gómez Martínez",
            spms: "Y. Gomez Martinez"
            },
            {
            match: True,
            exact: False,
            document: "T. X. Therou",
            spms: "T. Therou"
            },
            {
            match: False,
            exact: False,
            document: "A. Tiller",
            spms: ""
            },
        ]
    """
    extracted_document_authors = get_author_list(document_text)
    extracted_spms_authors = map(lambda x: x['name'], authors)

    # extracted_document_authors = ['Y. Z. Gómez Martínez', 'T. X. Therou', 'A. Tiller']
    document_list = build_comparison_author_objects(extracted_document_authors)
    spms_list = build_comparison_author_objects(extracted_spms_authors)
    # document_list = [
    # {
    #   original-value: 'Y. Z. Gómez Martínez',
    #   compare-value: 'Y. Z. Gomez Martinez',
    #   compare-first-last: 'Y. Gomez Martinez',
    #   compare-last: 'Gomez Martinez'
    # }, ... ]

    # create lists needed for matching and sorting:

    spms_matched = list()
    spms_unmatched = list()
    document_matched = list()
    results = list()

    # perform first round of matching, looking for exact matches:

    all_authors_match = True  # assume they all match until left with unpaired authors
    for spms_author in spms_list[:]:
        document_author = next((document_author for document_author in document_list if
                                document_author['compare-value'] == spms_author['compare-value']), None)
        if document_author:
            document_matched.append(document_author)
            document_list.remove(document_author)
            spms_matched.append(spms_author)
            spms_list.remove(spms_author)
            results.append({'document': document_author['original-value'],
                            'spms': spms_author['original-value'],
                            'exact': True,
                            'match': True})
        else:
            spms_unmatched.append(spms_author)
            spms_list.remove(spms_author)

    # Move remaining authors in document_list to document_unmatched:

    document_unmatched = document_list

    # if any unmatched authors remain, perform second round of matching, looking for loose matches (missing initials)

    for spms_author in spms_unmatched[:]:
        document_author = next((document_author for document_author in document_unmatched if
                                document_author['compare-first-last'] == spms_author['compare-first-last'] or
                                document_author['compare-transliterated'] == spms_author['compare-transliterated']),
                               None)
        if document_author:
            document_matched.append(document_author)
            document_unmatched.remove(document_author)
            spms_matched.append(spms_author)
            spms_unmatched.remove(spms_author)
            results.append({'document': document_author['original-value'],
                            'spms': spms_author['original-value'],
                            'exact': False,
                            'match': True})
    # after all matching rounds completed, any authors remaining in the
    # unmatched lists are added to results with a match value of false:

    for spms_author in spms_unmatched:
        results.append({'document': '',
                        'spms': spms_author['original-value'],
                        'exact': False,
                        'match': False})
        all_authors_match = False

    for document_author in document_unmatched:
        results.append({'document': document_author['original-value'],
                        'spms': '',
                        'exact': False,
                        'match': False})
        all_authors_match = False

    return results, all_authors_match


# runs conformity checks against the references csv file and returns a dict of
# results, eg: result = { title_match: True, authors_match: False }
def reference_check(filename_minus_ext, title, authors, references):
    result = {
        'title_match': False, 'authors_match': False,
    }

    # the encoding value is one that should work for most documents.
    # the encoding for a file can be detected with the command:
    #    ` file -i FILE `

    for reference in references:

        if filename_minus_ext == reference['paperId']:
            RE_MULTI_SPACE = re.compile(r' +')
            reference_title = RE_MULTI_SPACE.sub(' ', reference['title'].upper())
            title_match = remove_white_space(title.upper().strip('*')) == remove_white_space(reference_title)
            report, authors_match = get_author_list_report(authors, reference['authors'])

            spms_authors = list(map(lambda x: x['name'], reference['authors']))
            spms_author_string = ' '.join(spms_authors)
            # builds the data for display, match_ok determines the colour of the cell
            # True for green, False for red, 2 for amber.
            summary_list = [{
                'type': 'Author',
                'match_ok': 2 if result['match'] and not result['exact'] else result['match'],
                'document': result['document'],
                'spms': result['spms']} for result in report]

            return {
                'title': {
                    'match': title_match,
                    'document': title,
                    'spms': reference_title
                },
                'author': {
                    'match': authors_match,
                    'document': authors,
                    'spms': spms_author_string,
                    'document_list': get_author_list(authors),
                    'spms_list': spms_authors,
                    'report': report
                },
                'summary': [{
                    'type': 'Title',
                    'match_ok': title_match,
                    'document': title,
                    'spms': reference_title
                }, {
                    'type': 'Extracted Author List',
                    'match_ok': authors_match,
                    'document': authors,
                    'spms': spms_author_string,
                }, *summary_list],
            }

    return None


def create_spms_variables(paper_name, authors, title, references):
    summary = {}
    author_text = ''.join([a['text'] + ", " for a in authors])
    title_text = ''.join([a['text'] for a in title])
    reference_csv_details = reference_check(paper_name, title_text, author_text, references)

    if reference_csv_details is None:
        return None, None

    summary['Abstract Submission'] = {
        'title': ' Title Author Check',
        'help_info': SPMS_HELP_INFO,
        'extra_info': SPMS_EXTRA_INFO,
        'ok': reference_csv_details['title']['match'] and reference_csv_details['author']['match'],
        'message': 'Title Author Check issues',
        'details': reference_csv_details['summary'],
        'anchor': 'abstract'
    }

    return summary, reference_csv_details
