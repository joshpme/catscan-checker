import os
import sentry_sdk
from append_item import append_item

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=True,
)

def main(event):
    try:
        error = append_item(event)
        sentry_sdk.capture_event({
            "message": "Notification occurred",
            "level": "info",
            "extra": {"error": error, "event": event},
        })
        if error is None:
            return {"body":"Successfully added to queue"}
        else:
            return {"body": {"error": error }}
    except Exception as e:
        error_msg = f"An unexpected error occurred.\n Details:\n {e=}, {type(e)=}"
        sentry_sdk.capture_message(error_msg, level="error")
        return {"body": {"error": error_msg}}