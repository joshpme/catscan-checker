import requests
import os

indico_base = os.getenv("INDICO_BASE_URL")

def get_session():
    # Create a session object
    session = requests.Session()

    # Set common headers for the session
    token = os.getenv('INDICO_TOKEN')
    session.headers.update({
        'Authorization': f'Bearer {token}'
    })

    return session


# output, filename, contents, error
def find_papers(event_id, session=None):
    if session is None:
        session = get_session()
    url = f'/event/{event_id}/editing/api/paper/list'
    response = session.get(indico_base + url)
    if response.status_code == 200:
        return response.json(), None

    return None, f"Status code: {response.status_code}"


# Options: latex / word / bibtex / unknown
def get_paper(event_id, contribution_id, session=None):
    if session is None:
        session = get_session()
    url = f"/event/{event_id}/api/contributions/{contribution_id}/editing/paper"
    response = session.get(indico_base + url)
    if response.status_code == 200:
        return response.json(), None

    return None, f"Status code: {response.status_code}"


def find_latest_revision(event_id, contribution_id, session=None):
    contribution, error = get_paper(event_id, contribution_id, session=session)

    if contribution is None:
        return None, f"No contribution found {error}"

    highest = -1
    curr_revision = None
    for revision in contribution.get('revisions', []):
        if revision['id'] > highest:
            highest = revision['id']
            curr_revision = revision

    if highest != -1:
        return curr_revision, None

    return None, "Revision not found"

# Return data, content_type (latex|bibtex|word|unknown), file (json obj), error
def check_paper_type(revision):
    source_file_type = [180, 31]

    for file in revision.get('files', []):
        if file['filename'].lower().endswith('.docx'):
            return "word", file

    file_type = "unknown"
    for file in revision.get('files', []):
        if file['filename'].lower().endswith('.bib'):
            file_type = "bibtex"

    for file in revision.get('files', []):
        if file['filename'].lower().endswith('.tex') and file['file_type'] in source_file_type:
            if file_type == "unknown":
                file_type = "latex"
            return file_type, file

    return "unknown", None


def has_catscan_comment(revision):
    for comment in revision.get('comments', []):
        if f"{comment['user']['id']}" == f"{os.getenv("CATSCAN_USER_ID")}":
            return True
    return False


def find_all_contributions_with_no_catscan_comment(event_id, exclude_list=None):
    if exclude_list is None:
        exclude_list = []
    append_to_exclude_list = []
    contribution_revision_tuples = [] # (contribution_id, revision_id)

    session = get_session()

    papers, error = find_papers(event_id, session=session)
    if error is not None:
        return None, append_to_exclude_list, f"Error finding papers: {error}"

    for paper in papers:
        contribution_id = paper['id']
        if contribution_id in exclude_list:
            continue
        revision, error = find_latest_revision(event_id, contribution_id, session=session)

        # Skip if the contribution is not found
        if error is not None:
            continue

        if revision is None:
            continue

        paper_type, _ = check_paper_type(revision)

        if paper_type in ["latex", "word"] and has_catscan_comment(revision) is False:
            contribution_revision_tuples += [(contribution_id, revision['id'])]
        else:
            append_to_exclude_list.append(contribution_id)

    return contribution_revision_tuples, append_to_exclude_list, None
