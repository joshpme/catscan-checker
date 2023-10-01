package main

import (
	"github.com/dlclark/regexp2"
	"regexp"
)

var containsEtAl = regexp2.MustCompile(`et al\.`, 0)
var commaProceedsEtAl = regexp2.MustCompile(`,\s*(\\(emph|textit)\{)?et al`, 0)
var containsDoi = regexp2.MustCompile(`doi:10.`, 0)
var containsSpace = regexp2.MustCompile(`doi:\s10`, 0)
var noPrefix = regexp2.MustCompile(`\\url{10\.`, 0)
var doiIsUrl = regexp2.MustCompile(`https?://doi.org`, 0)

var wrappedEtAl = regexp.MustCompile(`\\(emph|textit)\{et al\.}`)
var wrappedDoi = regexp.MustCompile(`\\url\{doi:10\.`)

//var yearWrappedInParathesis = regexp.MustCompile(`\(\d{4}\)`)

func checkBibItem(bibItem BibItem) []Issue {
	var issues []Issue

	// et al. should not be proceeded by a comma
	// eg. L. Kiani et al.,
	match, err := commaProceedsEtAl.FindStringMatch(bibItem.OriginalText)
	if err == nil && match != nil {
		location := Location{Start: match.Index + bibItem.Location.Start, End: match.Index + match.Length + bibItem.Location.Start}
		issues = append(issues, Issue{Type: "ET_AL_WITH_COMMA", Location: location})
	}

	// Check if et al. not wrapped in a emph or textit macro
	// eg. L. Kiani et al.,
	match, err = containsEtAl.FindStringMatch(bibItem.OriginalText)
	if err == nil && match != nil {
		isWrapped := wrappedEtAl.FindString(bibItem.OriginalText)
		if isWrapped == "" {
			location := Location{Start: match.Index + bibItem.Location.Start, End: match.Index + match.Length + bibItem.Location.Start}
			issues = append(issues, Issue{Type: "ET_AL_NOT_WRAPPED", Location: location})
		}
	}

	// Check that the doi does not contain a space after the colon
	// e.g. doi: 10.1000/182
	match, err = containsSpace.FindStringMatch(bibItem.OriginalText)
	if err == nil && match != nil {
		location := Location{Start: match.Index + bibItem.Location.Start, End: match.Index + match.Length + bibItem.Location.Start}
		issues = append(issues, Issue{Type: "DOI_CONTAINS_SPACE", Location: location})
	}

	// Is wrapped in a URL macro
	// e.g. doi:10.1000/182 (without \url{})
	match, err = containsDoi.FindStringMatch(bibItem.OriginalText)
	if err == nil && match != nil {
		isWrapped := wrappedDoi.FindString(bibItem.OriginalText)
		if isWrapped == "" {
			location := Location{Start: match.Index + bibItem.Location.Start, End: match.Index + match.Length + bibItem.Location.Start}
			issues = append(issues, Issue{Type: "DOI_NOT_WRAPPED", Location: location})
		}
	}

	// Check that doi has a doi: prefix
	// e.g. \url{10.1000/182}
	match, err = noPrefix.FindStringMatch(bibItem.OriginalText)
	if err == nil && match != nil {
		location := Location{Start: match.Index + bibItem.Location.Start, End: match.Index + match.Length + bibItem.Location.Start}
		issues = append(issues, Issue{Type: "NO_DOI_PREFIX", Location: location})
	}

	// Check that DOI is not a http link
	// e.g. \url{https://doi.org/10.1000/182}
	match, err = doiIsUrl.FindStringMatch(bibItem.OriginalText)
	if err == nil && match != nil {
		location := Location{Start: match.Index + bibItem.Location.Start, End: match.Index + match.Length + bibItem.Location.Start}
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
