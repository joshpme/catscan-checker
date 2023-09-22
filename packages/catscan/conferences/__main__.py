import os
import mysql.connector

def main():
    try:
        cnx = mysql.connector.connect(
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASS'),
            host=os.getenv('MYSQL_HOST'),
            port=os.getenv('MYSQL_PORT'),
            database=os.getenv('MYSQL_DB')
        )
        cursor = cnx.cursor()

        query = ("SELECT id, code FROM conference WHERE is_published = 0 ORDER BY id DESC")
        cursor.execute(query)

        conferences = []
        for (id, code) in cursor:
            conferences.append({'id': id, 'code': code })

        cursor.close()
        cnx.close()
    except Exception as err:
        return {'body': { "error": f"Unexpected {err=}, {type(err)=}"}}

    return {'body': conferences}
