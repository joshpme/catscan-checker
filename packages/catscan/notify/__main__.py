import os
import requests

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

def leave_comment(conference_id, contribution_id, revision_id, comment):
    indico_base = "https://indico.jacow.org"
    url = f"/event/{conference_id}/api/contributions/{contribution_id}/editing/paper/{revision_id}/comments/"
    token = os.getenv('INDICO_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        'text': comment
    }
    response = requests.post(indico_base + url, data=data, headers=headers)
    return response


def catscan(conference_id, contribution_id, revision_id):
    url = f"https://scan-api.jacow.org/catscan/word"
    data = {
        "conference": conference_id,
        "contribution": contribution_id,
        "revision": revision_id
    }
    internal_headers = {
        'Authorization': f'Bearer {os.getenv("INDICO_AUTH")}'
    }
    response = requests.post(url, data, headers=internal_headers)
    if response.status_code == 200:
        return response.json()

    return {"error": "Could not get results from Catscan."}


def send_data(data):
    requests.post("https://webhook.site/54076fc4-d71f-42ad-93c6-c044366787df", json=data)


def run_scan(event):
    http = event.get("http", {})
    headers = http.get("headers", {})
    auth = headers.get("authorization", None)
    if auth is None:
        return {"body": {"error": "Unauthorized"}}

    bearer_token = f"Bearer {os.getenv('INDICO_AUTH')}"
    if auth != bearer_token:
        return {"body": {"error": "Incorrect auth token"}}

    payload = event.get("payload", None)
    if payload is None:
        return {"body": {"error": "Payload not provided"}}

    bearer_token = f"Bearer {os.getenv('INDICO_AUTH')}"
    if auth != bearer_token:
        return {"body": {"error": "Incorrect auth token"}}

    event_name = payload.get("event", None)
    if event_name is None:
        return {"body": {"error": "Event Name not provided"}}

    # Event name is asd-1234, I need to pull of the last digits to get the event ID
    event_id = event_name.split("-")[-1]

    contrib_id = payload.get("contrib_id", None)
    if contrib_id is None:
        return {"body": {"error": "Contribution ID not provided"}}

    revision_id = payload.get("revision_id", None)
    if revision_id is None:
        return {"body": {"error": "Revision ID not provided"}}

    action = payload.get("action", None)
    if action is None:
        return {"body": {"error": "Action not provided"}}

    if action not in {"create", "update"}:
        return {"body": {"ignored": f'Invalid action: {action}'}}

    editable_type = payload.get("editable_type", None)
    if editable_type is None:
        return {"body": {"error": "Editable type not provided"}}

    if editable_type not in {"paper"}:
        return {"body": {"ignored": f'Invalid editable type: {editable_type}'}}

    send_data({"body": "Running Catscan", "event": event_id, "contribution": contrib_id, "revision": revision_id})

    revision, error = find_revision(event_id, contrib_id, revision_id)

    if error is not None:
        return {"body": {"error": error}}

    if revision is None:
        return {"body": {"error": "No revision found"}}

    if 'is_editor_revision' in revision and revision['is_editor_revision'] is True:
        return {"body": {"ignored": "Editor revision"}}

    response = catscan(event_id, contrib_id, revision_id)

    if "error" in response:
        return {"body": response}

    filename = response.get("filename", None)
    if filename is None:
        return {"body": {"error": "Filename not provided"}}

    result_name = filename[:-5]
    html_response = f"# CatScan Results\n\n"
    html_response += f"Your paper has been automatically scanned for formatting issues. Here are the results:\n\n"
    html_response += f"[See Report](https://scan.jacow.org/?results={result_name})"

    leave_comment(event_id, contrib_id, revision_id, html_response)

    return {'body': "Successfully added comment"}


def main(event):
    try:
        response = run_scan(event)
        send_data(response)
        return response
    except Exception as e:
        error_response = {"body": {"error": f"An unexpected error occurred.\n Details:\n {e=}, {type(e)=}"}}
        send_data(error_response)
        return error_response
