import json
from unittest.mock import patch
import pytest

import indico

def get_and_parse_json(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            data = json.loads(content)
            return data
    except FileNotFoundError:
        print(f"Error: File not found at '{filepath}'")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON from '{filepath}'. Check the file content.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

@patch('indico.get_contribution')
@pytest.mark.parametrize("revision_id", [-1, 20452, "20452"])
def test_find_latest_revision_calls_get_contribution(mock_get_contribution, revision_id):
    mock_get_contribution.return_value = get_and_parse_json("example_contribution.json"), None
    event_id = 123
    contribution_id = 456
    revision, error = indico.find_latest_revision(event_id, contribution_id, revision_id)

    assert error is None
    assert revision['id'] == 20452
