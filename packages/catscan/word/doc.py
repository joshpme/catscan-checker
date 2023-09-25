from styles import get_style_summary
from margins import get_margin_summary
from title import get_title_summary, get_title_summary_latex
from authors import get_author_summary, get_author_summary_latex
from abstract import get_abstract_summary, get_abstract_summary_latex
from heading import get_heading_summary
from paragraph import get_paragraph_summary, get_all_paragraph_summary
from references import get_reference_summary
from figures import get_figure_summary
from tables import get_table_summary


def parse_paragraphs(doc):
    title_index = author_index = abstract_index = reference_index = -1
    current_style = None

    summary = {}
    for i, p in enumerate(doc.paragraphs):
        # first paragraph is the title
        text = p.text.strip()
        if not text:
            continue

        # first non empty paragraph is the title
        # Assume all of title is same style so end of title is when the style changes
        if title_index == -1:
            title_index = i
        elif title_index != -1 and author_index == -1 and current_style != p.style.name:
            author_index = i

        # find abstract heading
        if text.lower() == 'abstract':
            abstract_index = i
            summary['Abstract'] = get_abstract_summary(p)

        current_style = p.style.name

        # all headings, paragraphs captions, figures, tables, equations should be between these two
        # if abstract_index > 0 and reference_index == -1:
        #     print(i)
        #     # check if a known jacow style
        #     for section_type, section_data in DETAILS.items():
        #         if 'styles' in section_data:
        #             if p.style.name in section_data['styles']['jacow']:
        #                 found = f"{section_type} - {p.style.name}"
        #                 print(found)
        #                 break
        #             elif p.style.name in section_data['styles']['normal']:
        #                 found = f"{section_type} -- {p.style.name}"
        #                 print(found)
        #                 break
        #         else:
        #             for sub_type, sub_data in section_data.items():
        #                 if p.style.name in sub_data['styles']['jacow']:
        #                     found = f"{section_type} - {sub_type} - {p.style.name}"
        #                     print(found)
        #                 elif 'normal' in sub_data['styles'] and p.style.name in sub_data['styles']['normal']:
        #                     found = f"{section_type} -- {sub_type} -- {p.style.name}"
        #                     print(found)
        #                     break

        # find reference heading
        if text.lower() == 'references':
            reference_index = i
            break

    # if abstract not found
    if abstract_index == -1:
        return None, "Abstract not found"

    # authors is all the text between title and abstract heading
    summary['Title'] = get_title_summary(doc.paragraphs[title_index: author_index])
    summary['Authors'] = get_author_summary(doc.paragraphs[author_index: abstract_index])

    return summary, None


def create_upload_variables(doc):
    doc_summary, error = parse_paragraphs(doc)

    if doc_summary is None:
        return None, error

    # get style details
    summary = {
        'Title': doc_summary['Title'],
        'Authors': doc_summary['Authors'],
        'Abstract': doc_summary['Abstract'],
        'Headings': get_heading_summary(doc),
        'Paragraphs': get_paragraph_summary(doc),
        'Figures': get_figure_summary(doc),
        'Tables': get_table_summary(doc),
        'References': get_reference_summary(doc),
        'Styles': get_style_summary(doc),
        'Margins': get_margin_summary(doc),
        'List': get_all_paragraph_summary(doc)
    }

    # get title and author to use in SPMS check
    title = summary['Title']['details']
    authors = summary['Authors']['details']

    return (summary, authors, title), None

#
# def create_spms_variables(paper_name, authors, title, conferences, conference_id=False):
#     summary = {}
#     if len(conferences) > 0:
#         author_text = ''.join([a['text'] + ", " for a in authors])
#         title_text = ''.join([a['text'] for a in title])
#         reference_csv_details = reference_check(paper_name, title_text, author_text, conference_path)
#         conference_detail = conference_path
#         if conference_id:
#             conference_detail = conference_id
#         summary['SPMS'] = {
#             'title': ' SPMS ('+conference_detail+') Abstract Title Author Check',
#             'help_info': SPMS_HELP_INFO,
#             'extra_info': SPMS_EXTRA_INFO,
#             'ok': reference_csv_details['title']['match'] and reference_csv_details['author']['match'],
#             'message': 'SPMS Abstract Title Author Check issues',
#             'details': reference_csv_details['summary'],
#             'anchor': 'spms',
#             'conference': conference_detail
#         }
#     else:
#         reference_csv_details = False
#
#     return summary, reference_csv_details


def create_upload_variables_latex(doc):
    summary = {
        'Title': get_title_summary_latex(doc.title),
        'Authors': get_author_summary_latex(doc.author),
        'Abstract': get_abstract_summary_latex(doc.abstract)
    }

    # get title and author to use in SPMS check
    title = [summary['Title']]
    authors = [summary['Authors']]

    return summary, authors, title

