from db import connect_db, append_log, append_queue
import os

def append_item(event):
    http = event.get("http", {})
    headers = http.get("headers", {})
    auth = headers.get("authorization", None)
    if auth is None:
        return "Unauthorized"

    bearer_token = f"Bearer {os.getenv('INDICO_AUTH')}"
    if auth != bearer_token:
        return "Incorrect auth token"

    payload = event.get("payload", None)
    if payload is None:
        return "Payload not provided"

    bearer_token = f"Bearer {os.getenv('INDICO_AUTH')}"
    if auth != bearer_token:
        return "Incorrect auth token"

    event_name = payload.get("event", None)
    if event_name is None:
        return "Event Name not provided"

    # Event name is asd-1234, I need to pull of the last digits to get the event ID
    event_id = event_name.split("-")[-1]

    contrib_id = payload.get("contrib_id", None)
    if contrib_id is None:
        return "Contribution ID not provided"

    action = payload.get("action", None)
    if action is None:
        return "Action not provided"

    editable_type = payload.get("editable_type", None)
    if editable_type is None:
        return "Editable type not provided"

    with connect_db() as cnx:
        revision_id = payload.get("revision_id", None)

        append_log(cnx, event_id, contrib_id, revision_id, editable_type, action)

        if action not in {"create", "update"}:
            return f'Invalid action: {action}'

        if editable_type not in {"paper"}:
            return f'Invalid editable type: {editable_type}'

        append_queue(cnx, event_id, contrib_id, revision_id)

    return None

