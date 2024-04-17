import json

from refdb import get_references, create_spms_variables
from score import score
from page import check_tracking_on
from doc import create_upload_variables
from docx import Document
from s3 import get_file
from indico import get_word_contents

def get_extension(filename):
    return filename.rsplit('.', 1)[1].lower()


def allowed_file(filename):
    return '.' in filename and get_extension(filename) in {"docx"}


def get_name(filename):
    return filename.rsplit('.', 1)[0].upper()


def check_docx(filename, conference_id, file=None):
    if filename is None:
        return {
            "error": "Not file specified."
        }

    if not allowed_file(filename):
        return {
            "error": "File format is not allowed.\nFile must be a .docx"
        }

    if file is None:
        file = get_file(filename)

    if file is None:
        return {
            "error": "File not found.\nPlease try again."
        }

    try:
        doc = Document(docx=file)
    except KeyError:
        return {
            "error": "Document may not be in a supported format.\nTry to re-saving the file as a 'Word "
                     "Document' and try again."
        }

    metadata = doc.core_properties
    tracking_is_on = check_tracking_on(doc)

    if tracking_is_on:
        return {
            "error": "Cannot process file, tracking is turned on.\nPlease turn tracking off, and try again."
        }

    details, error = create_upload_variables(doc)

    if details is None:
        return {
            "error": error
        }

    summary, authors, title = details

    if conference_id is not None:
        paper_code = get_name(filename)
        references = get_references(paper_code, conference_id)
        if conference_id:
            reference_check_summary, reference_details = create_spms_variables(paper_code, authors, title, references)
            if reference_check_summary is not None and reference_details is not None:
                summary.update(reference_check_summary)

    scores = score(summary)

    meta = {}

    if metadata is not None:
        meta = {
            "author": metadata.author,
            "revision": metadata.revision,
            "version": metadata.version,
            "language": metadata.language,
        }

        if metadata.created is not None:
            meta["created"] = metadata.created.strftime("%d/%m/%Y %H:%M")

        if metadata.modified is not None:
            meta["modified"] = metadata.modified.strftime("%d/%m/%Y %H:%M")

    return {
        "scores": scores,
        "summary": summary,
        "metadata": meta,
        "filename": filename
    }


def main(event):
    output = {"error": "No file specified."}

    filename = event.get("name", None)
    conference_id = event.get("conference", None)

    if filename is not None:
        try:
            output = check_docx(filename, conference_id)
            return {'body': output}
        except Exception as err:
            output = {"error": f"An unexpected error occurred.\n Details:\n {err=}, {type(err)=}"}

    contribution_id = event.get("contribution", None)
    revision_id = event.get("revision", None)

    if contribution_id is not None and revision_id is not None:
        file_contents, filename = get_word_contents(conference_id, contribution_id, revision_id)
        if file_contents is None or filename is None:
            output = {"error": "Could not get contents from indico."}
            return {'body': output}

        try:
            output = check_docx(filename, conference_id, file_contents)
            return {'body': output}

        except Exception as err:
            output = {"error": f"An unexpected error occurred.\n Details:\n {err=}, {type(err)=}"}

    return {'body': output}