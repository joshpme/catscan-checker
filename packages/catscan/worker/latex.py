import os
import requests
from indico import download_contents

def call_latex_scan(filename, content):
    latex_scanner_url = os.getenv('LATEX_SCANNER_URL')
    data = {
        'filename': filename,
        'content': content
    }
    response = requests.post(latex_scanner_url, json=data)

    if not response.ok:
        return {"error": f"Could not get response from latex scanner: {response.status_code}"}

    if response.status_code == 200:
        return response.json()

    return None

def get_latex_comment(file):
    filename, contents, error = download_contents(file)
    if error is not None:
        return None, "Could not download contents of latex file"
    scan_result = call_latex_scan(filename, contents)

    if scan_result is None or "body" not in scan_result:
        return None, "No body in result"

    if "error" in scan_result:
        return None, "Could not scan latex file"

    if scan_result["body"] == "No issues found":
        return None, "No issues found"

    md_comment = "CatScan detected the following issues in your references:\n\n"
    md_comment += scan_result["body"].strip()
    md_comment += "\n\n[Re-check your paper @ CatScan](https://scan.jacow.org/) | [Citation Guidelines](https://www.jacow.org/Authors/FormattingCitations) | [Reference Search](https://refs.jacow.org/)"

    return md_comment, None
