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
        return response.json()
    return None


def find_revision(conference_id, contribution_id, revision_id):
    contribution = get_contribution(conference_id, contribution_id)

    if contribution is None:
        return None

    for revision in contribution.get('revisions', []):
        if revision['id'] == revision_id:
            return revision

    return None


def find_word_file(conference_id, contribution_id, revision_id):
    revision = find_revision(conference_id, contribution_id, revision_id)
    if revision is None:
        return None

    for file in revision.get('files', []):
        if file['filename'].endswith('.docx'):
            return file

    return None, None


def get_word_contents(conference_id, contribution_id, revision_id):
    file = find_word_file(conference_id, contribution_id, revision_id)
    if file is None:
        return None, None

    url = file['download_url']
    token = os.getenv('INDICO_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(indico_base + url, headers=headers)
    if response.status_code == 200:
        file_contents = io.BytesIO(response.content)
        return file_contents, file['filename']

    return None, None

