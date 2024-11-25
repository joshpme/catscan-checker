import requests
import pymysql
import os

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


def append_queue(event_id, contrib_id, revision_id):
    cnx = pymysql.connect(
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASS'),
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT')),
        database=os.getenv('MYSQL_DB'))
    cursor = cnx.cursor()

    query = """INSERT INTO scan_queue (event_id, contribution_id, revision_id) VALUES (%s, %s, %s)"""
    sql_result = cursor.execute(query, (event_id, contrib_id, revision_id))
    if sql_result == 1:
        cnx.commit()
        cursor.close()
        cnx.close()
        return None

    cursor.close()
    cnx.close()
    return "Failed to insert into scan_queue"


def append_item(event):
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

    revision, error = find_revision(event_id, contrib_id, revision_id)

    if error is not None:
        return {"body": {"error": error}}

    if revision is None:
        return {"body": {"error": "No revision found"}}

    if 'is_editor_revision' in revision and revision['is_editor_revision'] is True:
        return {"body": {"ignored": "Editor revision"}}

    append_queue(event_id, contrib_id, revision_id)

    return {'body': "Successfully added to queue"}


def main(event):
    try:
        response = append_item(event)
        return response
    except Exception as e:
        error_response = {"body": {"error": f"An unexpected error occurred.\n Details:\n {e=}, {type(e)=}"}}
        return error_response