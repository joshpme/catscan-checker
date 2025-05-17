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
        return response.json(), None

    return None, "Could not get results from Catscan."


def get_word_comment(event_id, contrib_id, revision_id):
    response, error = call_word_scan(event_id, contrib_id, revision_id)

    if error is not None:
        return None, error

    filename = response.get("filename", None)
    if filename is None:
        return None, "Filename not provided"

    result_name = filename[:-5]
    md_comment = f"CatScan has been checked for common formatting problems.\n"
    md_comment += f"**[See CatScan Report](https://scan.jacow.org/?results={result_name})**\n\n"
    md_comment += (f"Please attempt to resolve any errors that were found.\n"
                   f"You can re-check your paper using [CatScan](https://scan.jacow.org/) before re-submitting.")

    return md_comment, None