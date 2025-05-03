import os
import sentry_sdk
from scanner import scan
from queue_handler import check_queue, connect_db, save_results

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=True,
)

def main():
    try:
        queue_id = "unknown"
        with connect_db() as cnx:
            to_scan = check_queue(cnx)
            if to_scan is not None:
                queue_id = to_scan.get("queue_id")
                scan_result = scan(to_scan)
                save_results(
                    cnx,
                    queue_id=queue_id,
                    results=scan_result)
                sentry_sdk.capture_event({
                    "message": "Worker initiated",
                    "level": "info",
                    "extra": {"to_scan": to_scan, "result": scan_result},
                })
        if to_scan:
            return {'body': f"Scanned {queue_id}"}
        return {'body': "Nothing to scan"}
    except BaseException as e:
        error_msg = f"Worker: An unexpected error occurred.\n Details:\n {e=}"
        sentry_sdk.capture_message(error_msg, level="error")
        return {"body": {"error": error_msg}}