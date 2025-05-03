import os
from append_item import append_item
import pytest

@pytest.mark.parametrize("payload", [
    {"action": "create", "contrib_id": 5678, "editable_type": "paper", "event": "test-1234"},
    {"action": "update", "contrib_id": 6719, "editable_type": "paper", "event": "indico-jacow-org-75",
     "revision_id": 20752}])
def test_append_item(payload):
    # Set up environment variables
    os.environ['INDICO_AUTH'] = 'test_auth_token'
    os.environ['MYSQL_USER'] = 'root'
    os.environ['MYSQL_PASS'] = ''
    os.environ['MYSQL_HOST'] = 'localhost'
    os.environ['MYSQL_PORT'] = '3306'
    os.environ['MYSQL_DB'] = 'test'

    # Create a valid test event
    test_create_event = {
        "http": {
            "headers": {
                "authorization": "Bearer test_auth_token"
            }
        },
        "payload": payload
    }

    result = append_item(test_create_event)

    assert result is None
