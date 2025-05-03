import io

import pytest
from docx import Document
from margins import check_sections

def get_document(filename):
    with open(filename, 'rb') as f:
        document_content = f.read()
    return Document(docx=io.BytesIO(document_content))

@pytest.mark.parametrize("filename", ["JACoW_MSWord_Style_Guide"])
@pytest.mark.parametrize("page_size", ["JACoW"])
def test_check_sections(filename, page_size):
    doc = get_document(f"example_file/{filename}.docx")
    sections = check_sections(doc)
    for section in sections:
        assert section['page_size'] == page_size
