import os
import requests

def main(event):
    headers = event.get("headers", {})
    auth = headers.get("Authorization", None)
    if auth is None:
        return {"body": {"error": "Unauthorized"}}

    bearer_token = f"Bearer {os.getenv('INDICO_AUTH')}"
    if auth != bearer_token:
        return {"body": {"error": "Incorrect auth token"}}

    event_id = event.get("event", None)
    if event_id is None:
        return {"body": {"error": "Event ID not provided"}}

    contrib_id = event.get("contrib_id", None)
    if contrib_id is None:
        return {"body": {"error": "Contribution ID not provided"}}

    revision_id = event.get("revision_id", None)
    if revision_id is None:
        return {"body": {"error": "Revision ID not provided"}}

    action = event.get("action", None)
    if action is None:
        return {"body": {"error": "Action not provided"}}

    if action not in {"create", "update"}:
        return {"body": {"ignored": "Invalid action"}}

    editable_type = event.get("editable_type", None)
    if editable_type is None:
        return {"body": {"error": "Editable type not provided"}}

    if editable_type not in {"paper"}:
        return {"body": {"ignored": "Invalid editable type"}}

    url = f"https://scan-api.jacow.org/catscan/word"
    data = {
        "conference": event_id,
        "contribution": contrib_id,
        "revision": revision_id
    }
    response = requests.post(url, data)
    if response.status_code == 200:
        return {'body': response.json()}

    return {'body': "Hello from Catscan!"}