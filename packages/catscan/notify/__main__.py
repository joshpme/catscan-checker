import requests
import pymysql
import os
import sentry_sdk

indico_base = "https://indico.jacow.org"

# Set up environment variables
# os.environ['SENTRY_DSN'] = ""
# os.environ['INDICO_AUTH'] = 'test_auth_token'
# os.environ['INDICO_TOKEN'] = 'test_indico_token'
# os.environ['MYSQL_USER'] = 'root'
# os.environ['MYSQL_PASS'] = ''
# os.environ['MYSQL_HOST'] = 'localhost'
# os.environ['MYSQL_PORT'] = '3306'
# os.environ['MYSQL_DB'] = 'test'

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=True,
)

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


def find_latest_revision(conference_id, contribution_id, revision_id=None):
    contribution, error = get_contribution(conference_id, contribution_id)

    if contribution is None:
        return None, f"No contribution found {error}"

    if revision_id is None:
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


def connect_db():
    return pymysql.connect(
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASS'),
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT')),
        database=os.getenv('MYSQL_DB'))


def append_queue(cnx, event_id, contrib_id, revision_id):
    try:
        with cnx.cursor() as cursor:
            query = """INSERT INTO scan_queue (event_id, contribution_id, revision_id) VALUES (%s, %s, %s)"""
            sql_result = cursor.execute(query, (event_id, contrib_id, revision_id))
            if sql_result == 1:
                cnx.commit()
                return None
            return "Failed to insert into scan_queue"
    except Exception as e:
        return f"Database error: {str(e)}"


def append_log(cnx, event_id, contrib_id, revision_id, editable_type, action_type):
    try:
        with cnx.cursor() as cursor:
            revision = revision_id if revision_id is not None else "-1"
            query = """INSERT INTO notify_log (event_id, contribution_id, revision_id, action_type, editable_type) VALUES (%s, %s, %s, %s, %s)"""
            sql_result = cursor.execute(query, (event_id, contrib_id, revision, action_type, editable_type))
            if sql_result == 1:
                cnx.commit()
                return None
            return "Failed to insert into notify_log"
    except Exception as e:
        return f"Database error: {str(e)}"


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

    action = payload.get("action", None)
    if action is None:
        return {"body": {"error": "Action not provided"}}

    editable_type = payload.get("editable_type", None)
    if editable_type is None:
        return {"body": {"error": "Editable type not provided"}}

    with connect_db() as cnx:
        revision_id = payload.get("revision_id", None)

        append_log(cnx, event_id, contrib_id, revision_id, editable_type, action)

        if action not in {"create", "update"}:
            return {"body": {"ignored": f'Invalid action: {action}'}}

        if editable_type not in {"paper"}:
            return {"body": {"ignored": f'Invalid editable type: {editable_type}'}}

        revision, error = find_latest_revision(event_id, contrib_id, revision_id)

        if error is not None:
            return {"body": {"error": error}}

        if revision is None:
            return {"body": {"error": "No revision found"}}

        if 'is_editor_revision' in revision and revision['is_editor_revision'] is True:
            return {"body": {"ignored": "Editor revision"}}

        append_queue(cnx, event_id, contrib_id, revision["id"])

    return {'body': "Successfully added to queue"}


def main(event):
    try:
        response = append_item(event)
        sentry_sdk.capture_event({
            "message": "Notification occurred",
            "level": "info",
            "extra": {"response": response, "event": event},
        })
        return response
    except Exception as e:
        error_msg = f"An unexpected error occurred.\n Details:\n {e=}, {type(e)=}"
        sentry_sdk.capture_message(error_msg, level="error")
        return {"body": {"error": error_msg}}
#
#
# def test_main():
#     # Create a valid test event
#     test_event = {
#         "http": {
#             "headers": {
#                 "authorization": "Bearer test_auth_token"
#             }
#         },
#         "payload": {
#             "event": "test-1234",  # Conference ID
#             "contrib_id": "5678",  # Contribution ID
#             "revision_id": "9012",  # Revision ID
#             "action": "create",  # Valid action
#             "editable_type": "paper"  # Valid editable type
#         }
#     }
#
#     # Execute main function
#     result = main(test_event)
#     print("Test Result:", result)
#
#
# test_main()
