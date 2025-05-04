import json
from unittest.mock import patch
import pytest
import indico

## Integration tests (need indico .env parameters)

@pytest.mark.parametrize("event_id, contribution_id", [(37, 289)])
def test_find_papers_integration_test(event_id, contribution_id):
    papers, error = indico.find_papers(event_id)

    assert error is None

    # find paper['id'] == contribution in array of papers
    assert any(paper['id'] == contribution_id for paper in papers), f"Contribution {contribution_id} not found in papers"


@pytest.mark.parametrize("event_id, contribution_id", [(37, 289)])
def test_get_paper_integration_test(event_id, contribution_id):
    paper, error = indico.get_paper(event_id, contribution_id)

    assert error is None

    assert paper['contribution']['id'] == contribution_id, f"Contribution {contribution_id} not found in paper"

    assert paper['revisions'] is not None, f"Revisions not found in paper {contribution_id}"

    # has an array of revisions
    assert isinstance(paper['revisions'], list), f"Revisions is not a list in paper {contribution_id}"

    # has atleast one revision
    assert len(paper['revisions']) > 0, f"Revisions is empty in paper {contribution_id}"

@pytest.mark.parametrize("event_id, contribution_id, revision_id", [(37, 289, 20452)])
def test_find_latest_revision_integration_test(event_id, contribution_id, revision_id):
    revision, error = indico.find_latest_revision(event_id, contribution_id)

    assert error is None, f"Error finding latest revision for contribution {contribution_id}: {error}"

    assert revision['id'] == revision_id, f"Revision {revision_id} latest revision not found in paper {contribution_id}"

    assert indico.has_catscan_comment(
        revision) is True, f"Revision {revision_id} does not have catscan comment in paper {contribution_id}"

@pytest.mark.parametrize("event_id, contribution_id, revision_id", [(37, 154, 9037)])
def test_find_correct_contribution_integration_test(event_id, contribution_id, revision_id):
    contribution_revision_tuples, _, error = indico.find_contributions(event_id)

    assert error is None, f"Error finding latest revision for contribution {contribution_id}: {error}"

    # ensure contribution 154 is found, and it has the revision 9037
    assert any(
        (contrib_id, revision_id) == (contribution_id, revision_id) for contrib_id, revision_id in
        contribution_revision_tuples), f"Contribution {contribution_id} with revision {revision_id} not found in papers"


# Ensure the task of scanning all the papers in the event doesn't take more than 15 minute
@pytest.mark.timeout(15*60)
@pytest.mark.parametrize("event_id", [37, 81])
def test_timeout_test_integration_test(event_id):
    contribution_revision_tuples, _, error = indico.find_contributions(event_id)

    assert error is None, f"Error finding all contributions with no catscan comment: {error}"

    assert len(contribution_revision_tuples) > 0, f"No contributions found with no catscan comment in event {event_id}"

