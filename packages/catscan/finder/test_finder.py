from finder import finder
import pytest

@pytest.mark.timeout(15*60)
@pytest.mark.parametrize("event_id", [81])
def test_timeout_test_integration_test(event_id):
    queue_items, cached_items, errors = finder(event_id)

    assert errors == [], f"Errors occurred during the test: {errors}"
    assert queue_items > 0, f"No items queued for event {event_id}"



