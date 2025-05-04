import os
import pymysql

def connect_db():
    return pymysql.connect(
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASS'),
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT')),
        database=os.getenv('MYSQL_DB'))

def append_cache(cnx, event_id, contrib_id, paper_type):
    try:
        with cnx.cursor() as cursor:
            query = """INSERT INTO scan_paper_type_cache (event_id, contribution_id, paper_type) VALUES (%s, %s, %s)"""
            sql_result = cursor.execute(query, (event_id, contrib_id, paper_type))
            if sql_result == 1:
                cnx.commit()
                return None
            return "Failed to insert into paper_type_cache"
    except Exception as e:
        return f"Database error: {str(e)}"

def get_cache(cnx, event_id):
    contributions = []
    with cnx.cursor() as cursor:
        query = """SELECT contribution_id FROM scan_paper_type_cache WHERE event_id = %s""" #  OR SCAN_START < NOW() - INTERVAL 1 MINUTE
        cursor.execute(query, (event_id,))
        for (contribution_id, ) in cursor:
            contributions.append(contribution_id)
    return contributions

def append_queue(cnx, event_id, contrib_id, revision_id):
    try:
        with cnx.cursor() as cursor:
            revision = revision_id if revision_id is not None else "-1"
            query = """INSERT INTO scan_queue (event_id, contribution_id, revision_id) VALUES (%s, %s, %s)"""
            sql_result = cursor.execute(query, (event_id, contrib_id, revision))
            if sql_result == 1:
                cnx.commit()
                return None
            return "Failed to insert into scan_queue"
    except Exception as e:
        return f"Database error: {str(e)}"

def find_recent_queue_items(cnx, event_id):
    contributions = []
    with cnx.cursor() as cursor:
        query = """SELECT DISTINCT contribution_id FROM scan_queue WHERE event_id = %s AND REQUESTED >= NOW() - INTERVAL 24 HOUR""" #  OR SCAN_START < NOW() - INTERVAL 1 MINUTE
        cursor.execute(query, (event_id,))
        for (contribution_id, ) in cursor:
            contributions.append(contribution_id)
    return contributions

