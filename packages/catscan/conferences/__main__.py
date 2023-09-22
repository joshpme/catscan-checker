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

        query = ("SELECT id, code FROM conferences")
        cursor.execute(query)

        conferences = []
        for (id, code) in cursor:
            conferences.append({'id': id, 'code': code })

        cursor.close()
        cnx.close()
    except Exception as err:
        return {'body': f"Unexpected {err=}, {type(err)=}"}

    # conferences = filter(lambda x: not x['isPublished'], get_conferences(authenticate()))
    # conferences = sorted(conferences, key=lambda x: x['id'], reverse=True)
    return {'body': conferences}
