import requests
import os

# output, filename, contents, error
def download_contents(file):
    url = file['download_url']
    token = os.getenv('INDICO_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}'
    }
    indico_base = os.getenv("INDICO_BASE_URL")
    response = requests.get(indico_base + url, headers=headers)
    if response.status_code == 200:
        return file['filename'], response.content.decode('utf-8'), None

    return None, None, f"Status code: {response.status_code}"


# Options: latex / word / bibtex / unknown
def get_contribution(event_id, contribution_id):
    url = f"/event/{event_id}/api/contributions/{contribution_id}/editing/paper"
    token = os.getenv('INDICO_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}'
    }
    indico_base = os.getenv("INDICO_BASE_URL")
    response = requests.get(indico_base + url, headers=headers)
    if response.status_code == 200:
        return response.json(), None

    return None, f"Status code: {response.status_code}"


def find_latest_revision(event_id, contribution_id, revision_id):
    contribution, error = get_contribution(event_id, contribution_id)

    if contribution is None:
        return None, f"No contribution found {error}"

    if revision_id == -1:
        highest = -1
        curr_revision = None
        for revision in contribution.get('revisions', []):
            if revision['id'] > highest:
                highest = revision['id']
                curr_revision = revision

        if highest != -1:
            return curr_revision, None
    else:
        for revision in contribution.get('revisions', []):
            if f"{revision['id']}" == f"{revision_id}":
                return revision, None

    return None, "Revision not found"

# Return data, content_type (latex|bibtex|word|unknown), file (json obj), error
def check_paper_type(revision):
    bibtex_type = [182, 354]
    source_file_type = [180, 31, 352]

    for file in revision.get('files', []):
        if file['filename'].lower().endswith('.docx') and file['file_type'] in source_file_type:
            return "word", file

    file_type = "unknown"
    for file in revision.get('files', []):
        if file['filename'].lower().endswith('.bib') and file['file_type'] in bibtex_type:
            file_type = "bibtex"

    for file in revision.get('files', []):
        if file['filename'].lower().endswith('.tex') and file['file_type'] in source_file_type:
            if file_type == "unknown":
                file_type = "latex"
            return file_type, file

    return "unknown", None


def leave_comment(event_id, contribution_id, revision_id, comment):
    url = f"/event/{event_id}/api/contributions/{contribution_id}/editing/paper/{revision_id}/comments/"
    token = os.getenv('INDICO_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        'text': comment
    }
    indico_base = os.getenv("INDICO_BASE_URL")
    response = requests.post(indico_base + url, data=data, headers=headers)

    if not response.ok:
        return f"Could not leave comment: {response.status_code}"

    return None

