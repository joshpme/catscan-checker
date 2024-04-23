import os
import requests

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
    response = requests.post(indico_base + url,data=data, headers=headers)
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

def construct_table(response):
    results = response.get("results", None)
    if results is None:
        print("No body in response")
        return None

    categories = results.get("scores", None)
    if categories is None:
        print("No scores in body")
        return None

    table = "<table><thead><tr><td><b>Section</b></td><td><b>Ok</b></td><td><b>Warnings</b></td><td><b>Errors</b></td></tr></thead><tbody>"
    for category, scores in categories.items():
        table += f"<tr><td>{category.title()}&nbsp;</td><td>&nbsp;{scores[0]}&nbsp;</td><td>&nbsp;{scores[1]}&nbsp;</td><td>&nbsp;{scores[2]}</td></tr>"
    table += "</tbody></table>"

    return table


def main(event):
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

    event_id = payload.get("event", None)
    if event_id is None:
        return {"body": {"error": "Event ID not provided"}}

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
        return {"body": {"ignored": "Invalid action"}}

    editable_type = payload.get("editable_type", None)
    if editable_type is None:
        return {"body": {"error": "Editable type not provided"}}

    if editable_type not in {"paper"}:
        return {"body": {"ignored": "Invalid editable type"}}

    response = catscan(event_id, contrib_id, revision_id)

    if "error" in response:
        return {"body": response}

    filename = response.get("filename", None)
    if filename is None:
        return {"body": {"error": "Filename not provided"}}

    result_name = filename[:-5]
    html_response = f"<h2>CatScan Results</h2>"
    html_response += f"<p>Your paper has been automatically scanned for formatting issues. Here are the results:</p>"
    html_response += f"<p><b><a target='_blank' href='https://scan.jacow.org/?results={result_name}'>See Report</a></b></p>"

    table = construct_table(response)
    if table is not None:
        html_response += "<h3>Summary</h3>" + table

    leave_comment(event_id, contrib_id, revision_id, html_response)

    return {'body': "Successfully added comment"}
