from json import JSONDecodeError

import requests
import os


# # output, filename, contents, error
# def find_papers(event_id):
#     indico_base = os.getenv("INDICO_BASE_URL")
#     url = f"/event/{event_id}/editing/api/paper/list"
#     response = requests.get(indico_base + url, headers={
#         'Authorization': f'Bearer {os.getenv('INDICO_TOKEN')}'
#     })
#     if response.status_code == 200:
#         return response.json(), None
#
#     return None, f"Status code: {response.status_code}"

#
# # Options: latex / word / bibtex / unknown

#
#
def find_latest_revision(paper):
    highest = -1
    curr_revision = None
    for revision in paper.get('revisions', []):
        if revision['id'] > highest:
            highest = revision['id']
            curr_revision = revision

    if highest != -1:
        return curr_revision, None

    return None, "Revision not found"
#
#
# # Return data, content_type (latex|bibtex|word|unknown), file (json obj), error
def find_paper_type(revision):
    source_file_type = [180, 31]

    for file in revision.get('files', []):
        if file['filename'].lower().endswith('.docx'):
            return "word"

    file_type = "unknown"
    for file in revision.get('files', []):
        if file['filename'].lower().endswith('.bib'):
            file_type = "bibtex"

    for file in revision.get('files', []):
        if file['filename'].lower().endswith('.tex') and file['file_type'] in source_file_type:
            if file_type == "unknown":
                file_type = "latex"
            return file_type

    return "unknown"
#
#
# def has_catscan_comment(revision):
#     for comment in revision.get('comments', []):
#         if f"{comment['user']['id']}" == f"{os.getenv("CATSCAN_USER_ID")}":
#             return True
#     return False

def find_papers(session, event_id):
    indico_base = os.getenv("INDICO_BASE_URL")
    response = session.get(f"{indico_base}/event/{event_id}/editing/api/paper/list")
    if response.status_code != 200:
        return None, f"Status code: {response.status_code}"
    try:
        return response.json(), None
    except JSONDecodeError as e:
        return None, f"JSON decode error: {str(e)}"


def get_paper(session, event_id, contribution_id):
    indico_base = os.getenv("INDICO_BASE_URL")
    response = session.get(f"{indico_base}/event/{event_id}/api/contributions/{contribution_id}/editing/paper")
    if response.status_code != 200:
        return None, f"Status code: {response.status_code}"
    try:
        return response.json(), None
    except JSONDecodeError as e:
        return None, f"JSON decode error: {str(e)}"


def find_contributions(event_id, exclude_list=None):
    if exclude_list is None:
        exclude_list = []
    append_to_exclude_list = []
    contribution_revision_tuples = []  # (contribution_id, revision_id)

    indico_token = os.getenv("INDICO_TOKEN")
    token_value = f"Bearer {indico_token}"
    with requests.Session() as session:
        session.headers.update({
            'Authorization': token_value,
        })
        papers, revision_error = find_papers(session, event_id)

        if papers is None:
            return None, [], f"Error finding papers: {revision_error}"

        for paper in papers:
            if "id" not in paper:
                continue
            contribution_id = paper['id']
            if contribution_id in exclude_list:
                continue
            paper, paper_error = get_paper(session, event_id, contribution_id)
            if paper_error is not None:
                continue
            revision, revision_error = find_latest_revision(paper)
            if revision_error is not None:
                continue
            if revision is None:
                continue
            paper_type = find_paper_type(revision)



    return contribution_revision_tuples, append_to_exclude_list, None

    #

    #     # Skip if the contribution is not found
    #     if revision_error is not None:
    #         continue
    #
    #     if revision is None:
    #         continue
    #
    #     paper_type, _ = check_paper_type(revision)
    #
    #     if paper_type in ["latex", "word"] and has_catscan_comment(revision) is False:
    #         contribution_revision_tuples.append((contribution_id, revision['id']))
    #     else:
    #         append_to_exclude_list.append(contribution_id)
    #
    # return contribution_revision_tuples, append_to_exclude_list, None
