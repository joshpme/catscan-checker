import os
from queue_handler import check_queue, connect_db, save_results
import pytest

# Integration test
@pytest.mark.parametrize("scan_result", [None, "Some string result"])
def test_check_queue(scan_result):
    os.environ['MYSQL_USER'] = 'root'
    os.environ['MYSQL_PASS'] = ''
    os.environ['MYSQL_HOST'] = 'localhost'
    os.environ['MYSQL_PORT'] = '3306'
    os.environ['MYSQL_DB'] = 'test'

    with connect_db() as cnx:
        to_scan = check_queue(cnx)
        if to_scan is not None:
            queue_id = to_scan.get("queue_id")
            save_results(
                cnx,
                queue_id=queue_id,
                results=scan_result)
