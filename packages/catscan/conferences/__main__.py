import os
import mysql.connector


def main():

    cnx = mysql.connector.connect(
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASS'),
        host=os.getenv('MYSQL_HOST'),
        port=os.getenv('MYSQL_PORT'),
        database=os.getenv('MYSQL_DB')
    )
    cursor = cnx.cursor()

    query = ("SELECT * FROM conferences")
    cursor.execute(query)

    conferences = []
    for data in cursor:
        conferences.append(data)

    cursor.close()
    cnx.close()

    # conferences = filter(lambda x: not x['isPublished'], get_conferences(authenticate()))
    # conferences = sorted(conferences, key=lambda x: x['id'], reverse=True)
    return {'body': conferences}
