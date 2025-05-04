import os
import time
import sentry_sdk
from finder import finder

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=True,
)


def main(event):
    try:
        start_timer = time.time()
        event_id = event.get("id", None)
        if event_id is None:
            return {"body": {"error": "Event ID is required"}}
        queue_items, cached_items, errors = finder(event_id=event_id)
        end_timer = time.time()
        content_body = {
            "event_id": event_id,
            "duration": end_timer - start_timer,
            "queue_items": queue_items,
            "cached_items": cached_items,
            "errors": errors
        }
        return_body = {"body": content_body}
        sentry_sdk.capture_event({
            "message": "Finder ran",
            "level": "info",
            "extra": content_body,
        })
        return return_body
    except BaseException as e:
        error_msg = f"Finder: An unexpected error occurred.\n Details:\n {e=}"
        sentry_sdk.capture_message(error_msg, level="error")
        return {"body": {"error": error_msg}}