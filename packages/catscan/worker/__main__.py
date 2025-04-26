import json
import requests
import pymysql
import os

indico_base = "https://indico.jacow.org"

def leave_comment(conference_id, contribution_id, revision_id, comment):
    url = f"/event/{conference_id}/api/contributions/{contribution_id}/editing/paper/{revision_id}/comments/"
    token = os.getenv('INDICO_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        'text': comment
    }
    response = requests.post(indico_base + url, data=data, headers=headers)

    if not response.ok:
        return {"error": f"Could not leave comment: {response.status_code}"}

    return None


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

def connect_db():
    return pymysql.connect(
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASS'),
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT')),
        database=os.getenv('MYSQL_DB'))

def check_queue(cnx):
    r = None
    with cnx.cursor() as cursor:
        query = """SELECT id as queue_id, event_id, contribution_id, revision_id FROM scan_queue WHERE scanned IS NULL AND (SCAN_START IS NULL OR SCAN_START < NOW() - INTERVAL 1 MINUTE) ORDER BY REQUESTED ASC LIMIT 1"""
        cursor.execute(query)
        for (queue_id, event_id, contribution_id, revision_id) in cursor:
            start_scan = """UPDATE scan_queue SET SCAN_START = NOW() WHERE id = %s"""
            if cursor.execute(start_scan, (queue_id,)) == 1:
                cnx.commit()
                r = {
                    "queue_id": queue_id,
                    "event_id": event_id,
                    "contribution_id": contribution_id,
                    "revision_id": revision_id
                }
    return r

def save_results(cnx, queue_id, results):
    with cnx.cursor() as cursor:
        if results is None:
            successful = """UPDATE scan_queue SET scanned = NOW() WHERE id = %s"""
            cursor.execute(successful, (queue_id,))
        else:
            failure = """UPDATE scan_queue SET failure_reason = %s, scanned = NOW() WHERE id = %s"""
            cursor.execute(failure, (json.dumps(results), queue_id,))
        cnx.commit()

def run_scan(event_id, contrib_id, revision_id):
    response = catscan(event_id, contrib_id, revision_id)

    if "error" in response:
        return response.get("error", "Unknown error")

    filename = response.get("filename", None)
    if filename is None:
        return "Filename not provided"

    result_name = filename[:-5]
    html_response = f"# CatScan Results\n\n"
    html_response += f"Your paper has been automatically scanned for formatting issues. Here are the results:\n\n"
    html_response += f"[See Report](https://scan.jacow.org/?results={result_name})"

    comment_response = leave_comment(event_id, contrib_id, revision_id, html_response)
    if comment_response is not None:
        return comment_response.get("error", "Unknown error")

    return None



def main():
    try:
        to_scan = False
        queue_id = "unknown"
        scan_result = {}
        with connect_db() as cnx:
            to_scan = check_queue(cnx)
            if to_scan is not None:
                queue_id = to_scan.get("queue_id")
                event_id = to_scan.get("event_id")
                contribution_id = to_scan.get("contribution_id")
                revision_id = to_scan.get("revision_id")
                scan_result = run_scan(event_id=event_id, contrib_id=contribution_id, revision_id=revision_id)
                save_results(
                    cnx,
                    queue_id=queue_id,
                    results=scan_result)
        if to_scan:
            return {'body': f"Scanned {queue_id}: " + json.dumps(scan_result)}
        return {'body': "Nothing to scan"}
    except BaseException as e:
        error_response = {"body": {"error": f"An unexpected error occurred.\n Details:\n {e=}, {type(e)=}"}}
        return error_response