from db import connect_db, get_cache, append_cache, append_queue, find_recent_queue_items
from indico import find_all_contributions_with_no_catscan_comment

def finder(event_id):
    error_list = []
    queue_items = 0
    cached_items = 0
    with connect_db() as cnx:
        cache_list = get_cache(cnx, event_id)
        recently_queued = find_recent_queue_items(cnx, event_id)
        exclude_list = recently_queued + cache_list
        to_check, new_exclude_list, find_error = find_all_contributions_with_no_catscan_comment(event_id, exclude_list=exclude_list)
        if find_error is not None:
            error_list.append(f"Error finding contributions: {find_error}")
        for contrib_id in new_exclude_list:
            cache_error = append_cache(cnx, event_id, contrib_id, "unknown")
            if cache_error is not None:
                error_list.append(f"Error adding to cache: {cache_error}")
        for contrib_id, revision_id in to_check:
            # Call the scan function here
            queue_error = append_queue(cnx, event_id, contrib_id, revision_id)
            if queue_error is not None:
                error_list.append(f"Error adding to queue: {queue_error}")
        queue_items = len(to_check)
        cached_items = len(new_exclude_list)
    return queue_items, cached_items, error_list