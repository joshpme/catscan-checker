import os
import pymysql
import json

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
        query = """SELECT id as queue_id, event_id, contribution_id, revision_id FROM scan_queue WHERE scanned IS NULL AND SCAN_START IS NULL ORDER BY REQUESTED ASC LIMIT 1""" #  OR SCAN_START < NOW() - INTERVAL 1 MINUTE
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

def save_results(cnx, queue_id, scan_error):
    with cnx.cursor() as cursor:
        if scan_error is None:
            successful = """UPDATE scan_queue SET scanned = NOW() WHERE id = %s"""
            cursor.execute(successful, (queue_id,))
        else:
            failure = """UPDATE scan_queue SET failure_reason = %s, scanned = NOW() WHERE id = %s"""
            cursor.execute(failure, (json.dumps(scan_error), queue_id,))
        cnx.commit()
