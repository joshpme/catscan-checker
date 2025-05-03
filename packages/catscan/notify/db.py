import os
import pymysql

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
            revision = revision_id if revision_id is not None else "-1"
            query = """INSERT INTO scan_queue (event_id, contribution_id, revision_id) VALUES (%s, %s, %s)"""
            sql_result = cursor.execute(query, (event_id, contrib_id, revision))
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

