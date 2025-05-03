import os
import requests

def call_word_scan(event_id, contribution_id, revision_id):
    url = os.getenv('WORD_SCANNER_URL')
    data = {
        "conference": event_id,
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


def get_word_comment(event_id, contrib_id, revision_id):
    response = call_word_scan(event_id, contrib_id, revision_id)

    if "error" in response:
        return None, response.get("error", "Unknown error")

    filename = response.get("filename", None)
    if filename is None:
        return None, "Filename not provided"

    result_name = filename[:-5]
    md_comment = f"# CatScan Results\n\n"
    md_comment += f"Your paper has been automatically scanned for formatting issues. Here are the results:\n\n"
    md_comment += f"[See Report](https://scan.jacow.org/?results={result_name})"

    return md_comment, None