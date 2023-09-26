package main

import (
	"regexp"
)

var containsEtAl = regexp.MustCompile(`et al.`)
var wrappedEtAl = regexp.MustCompile(`\\(emph|textit)\{et al\.}`)
var containsDoi = regexp.MustCompile(`doi:10.`)
var containsSpace = regexp.MustCompile(`doi:\s10`)
var wrappedDoi = regexp.MustCompile(`\\url\{doi:10\.`)
var noPrefix = regexp.MustCompile(`\\url{10\.`)
var doiIsUrl = regexp.MustCompile(`https?://doi.org`)
var yearWrappedInParathesis = regexp.MustCompile(`\(\d{4}\)`)

func checkBibItem(bibItem BibItem) []Issue {
	var issues []Issue

	// Check if et al. not wrapped in a emph or textit macro
	// eg. L. Kiani et al.,
	ifContainsEtAl := containsEtAl.FindStringIndex(bibItem.OriginalText)
	if ifContainsEtAl != nil {
		isWrapped := wrappedEtAl.FindString(bibItem.OriginalText)
		if isWrapped == "" {
			location := Location{Start: ifContainsEtAl[0] + bibItem.Location.Start, End: ifContainsEtAl[1] + bibItem.Location.Start}
			issues = append(issues, Issue{Type: "ET_AL_NOT_WRAPPED", Location: location})
		}
	}

	// Check that the doi does not contain a space after the colon
	// e.g. doi: 10.1000/182
	issueExists := containsSpace.FindStringIndex(bibItem.OriginalText)
	if issueExists != nil {
		location := Location{Start: issueExists[0] + bibItem.Location.Start, End: issueExists[1] + bibItem.Location.Start}
		issues = append(issues, Issue{Type: "DOI_CONTAINS_SPACE", Location: location})
	}

	// Is wrapped in a URL macro
	// e.g. doi:10.1000/182 (without \url{})
	ifContainsDoi := containsDoi.FindStringIndex(bibItem.OriginalText)
	if ifContainsDoi != nil {
		isWrapped := wrappedDoi.FindString(bibItem.OriginalText)
		if isWrapped == "" {
			location := Location{Start: ifContainsDoi[0] + bibItem.Location.Start, End: ifContainsDoi[1] + bibItem.Location.Start}
			issues = append(issues, Issue{Type: "DOI_NOT_WRAPPED", Location: location})
		}
	}

	// Check that doi has a doi: prefix
	// e.g. \url{10.1000/182}
	ifNoPrefix := noPrefix.FindStringIndex(bibItem.OriginalText)
	if ifNoPrefix != nil {
		location := Location{Start: ifNoPrefix[0] + bibItem.Location.Start, End: ifNoPrefix[1] + bibItem.Location.Start}
		issues = append(issues, Issue{Type: "NO_DOI_PREFIX", Location: location})
	}

	// Check that DOI is not a http link
	// e.g. \url{https://doi.org/10.1000/182}
	ifDoiIsUrl := doiIsUrl.FindStringIndex(bibItem.OriginalText)
	if ifDoiIsUrl != nil {
		location := Location{Start: ifDoiIsUrl[0] + bibItem.Location.Start, End: ifDoiIsUrl[1] + bibItem.Location.Start}
		issues = append(issues, Issue{Type: "DOI_IS_URL", Location: location})
	}

	return issues
}

func FindBibItemIssues(bibItems []BibItem) []Issue {
	var issues []Issue

	for _, bibItem := range bibItems {
		issues = append(issues, checkBibItem(bibItem)...)
	}

	return issues
}
