from django.db import connection


def find_block_by_id(bid):
    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT name
        FROM block
        WHERE blockid = %s
        """, [bid])
        r = cursor.fetchone()
        return r[0]

