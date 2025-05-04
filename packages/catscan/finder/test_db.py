from db import connect_db, append_cache, get_cache
import pytest

def test_cache_list_integration_test():
    event_id = 69
    exclude_list = [100, 101, 102]

    with connect_db() as cnx:
        # Clear the cache before the test
        with cnx.cursor() as cursor:
            cursor.execute("DELETE FROM scan_paper_type_cache WHERE event_id = %s", (event_id,))
            cnx.commit()

        # Append contributions to the cache
        for contrib_id in exclude_list:
            error = append_cache(cnx, event_id, contrib_id, "unknown")
            assert error is None, f"Failed to append to cache: {error}"

        # Retrieve the cached contributions
        cached_contributions = get_cache(cnx, event_id)

        # Check if the cached contributions match the expected exclude list
        assert set(cached_contributions) == set(exclude_list), f"Cached contributions do not match expected: {cached_contributions}"


