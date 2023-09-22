from refdb import get_references, create_spms_variables
from score import score
from page import check_tracking_on
from doc import create_upload_variables
from docx import Document
from s3 import get_file

def get_extension(filename):
    return filename.rsplit('.', 1)[1].lower()

def allowed_file(filename):
    return '.' in filename and get_extension(filename) in {"docx"}

def get_name(filename):
    return filename.rsplit('.', 1)[0].upper()

def check_docx(filename, conference_id):
    if filename is None:
        return {
            "error": "Not file specified"
        }

    if not allowed_file(filename):
        return {
            "error": "File format is not allowed"
        }

    file = get_file(filename)

    if file is None:
        return {
            "error": "File not found"
        }

    try:
        doc = Document(docx=file)
    except KeyError:
        return {
            "error": "Document may not be in a supported format. Try to re-saving the file as a 'Word "
                     "Document' and try again."
        }

    metadata = doc.core_properties
    tracking_is_on = check_tracking_on(doc)

    if tracking_is_on:
        return {
            "error": "Cannot process file, tracking is turned on. Please turn tracking off, and try again."
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
            "created": metadata.created.strftime("%d/%m/%Y %H:%M"),
            "modified": metadata.modified.strftime("%d/%m/%Y %H:%M"),
            "version": metadata.version,
            "language": metadata.language,
        }

    return {
        "scores": scores,
        "summary": summary,
        "metadata": meta,
        "filename": filename
    }

def main(event):
    filename = event.get("name", None)
    conference_id = event.get("conference", None)
    try:
        output = check_docx(filename, conference_id)
    except Exception as err:
        output = f"Unexpected {err=}, {type(err)=}"

    return {'body': output}