from word import get_word_comment
from latex import get_latex_comment
from indico import find_latest_revision, check_paper_type, leave_comment
import sentry_sdk

def scan(to_scan):
    event_id = to_scan.get("event_id")
    contrib_id = to_scan.get("contribution_id")
    revision_id = to_scan.get("revision_id")

    revision, error = find_latest_revision(event_id, contrib_id, revision_id)
    if error is not None:
        return f"No revision found: {error}"

    if revision is None:
        return "No revision found"

    # Do not comment on editor revisions
    if 'is_editor_revision' in revision and revision['is_editor_revision'] is True:
        return "Editor revision"

    # reset revision id to revision['id'] found on revision from indico
    revision_id = revision['id']

    file_type, file = check_paper_type(revision)

    if error is not None:
        return error

    if file_type == "word":
        comment, scan_error = get_word_comment(event_id=event_id, contrib_id=contrib_id, revision_id=revision_id)
    elif file_type == "latex":
        comment, scan_error = get_latex_comment(file=file)
    else:
        return f"Unknown file type: {file_type}"

    if scan_error is not None:
        return scan_error

    sentry_sdk.capture_event({
        "message": "Worker message",
        "level": "info",
        "extra": {"to_scan": to_scan, "comment": comment, "revision_id": revision_id},
    })

    if comment is not None:
        comment_error = leave_comment(event_id, contrib_id, revision_id, comment)
        if comment_error is not None:
            return comment_error

    return None