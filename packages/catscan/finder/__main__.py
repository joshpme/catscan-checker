import os
import time
import sentry_sdk
from runner import runner

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=True,
)

def main(event):
    try:
        event_id = event.get("id", None)
        start_timer = time.time()
        queue_items, cached_items, errors = runner(event_id=event_id)
        end_timer = time.time()
        sentry_sdk.capture_event({
            "message": "Runner ran",
            "level": "info",
            "extra": {"event_id": event_id,
                      "duration": end_timer - start_timer,
                      "queue_items": queue_items,
                      "cached_items": cached_items,
                      "errors": errors},
        })
    except BaseException as e:
        error_msg = f"Worker: An unexpected error occurred.\n Details:\n {e=}"
        sentry_sdk.capture_message(error_msg, level="error")
        return {"body": {"error": error_msg}}
