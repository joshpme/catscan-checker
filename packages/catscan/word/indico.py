import os
import requests
import io

indico_base = "https://indico.jacow.org"

def get_contribution(conference_id, contribution_id):
    url = f"/event/{conference_id}/api/contributions/{contribution_id}/editing/paper"
    token = os.getenv('INDICO_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(indico_base + url, headers=headers)
    if response.status_code == 200:
        return response.json(), None

    return None, f"Status code: {response.status_code}"


def find_revision(conference_id, contribution_id, revision_id):
    contribution, error = get_contribution(conference_id, contribution_id)

    if contribution is None:
        return None, f"No contribution found {error}"

    for revision in contribution.get('revisions', []):
        if f"{revision['id']}" == f"{revision_id}":
            return revision, None

    return None, "No revision found"


def find_word_file(conference_id, contribution_id, revision_id):
    revision, error = find_revision(conference_id, contribution_id, revision_id)
    if error is not None:
        return None, f"No revision found: {error}"

    if revision is None:
        return None, "No revision found"

    for file in revision.get('files', []):
        if file['filename'].endswith('.docx'):
            return file, None

    return None, "No word file found"


def get_word_contents(conference_id, contribution_id, revision_id):
    file, error = find_word_file(conference_id, contribution_id, revision_id)
    if file is None or error is not None:
        return None, None, f"Could not get word contents {error}"

    url = file['download_url']
    token = os.getenv('INDICO_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(indico_base + url, headers=headers)
    if response.status_code == 200:
        file_contents = io.BytesIO(response.content)
        return file_contents, file['filename'], None

    return None, None, f"Status code: {response.status_code}"

