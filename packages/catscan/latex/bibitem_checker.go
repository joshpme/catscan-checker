package main

import (
	"regexp"
)

//
//// return list of errors
//func checkDoi(bibItem BibItem) ([]Issue, error) {
//	var issues []Issue
//
//	// Check that the doi does not contain a space after the colon
//	// e.g. doi: 10.1000/182
//	containsSpace, issue := containsSpace(bibItem)
//	if containsSpace {
//		issues = append(issues, issue)
//	}
//
//	// Is wrapped in a URL macro
//	// e.g. doi:10.1000/182 (without \url{})
//
//	// Check that DOI is not a http link
//	// e.g. \url{https://doi.org/10.1000/182}
//	containsUrl, err := regexp.MatchString(`https?://doi.org`, bibItem.Ref)
//	if err != nil {
//		return nil, err
//	}
//	if containsUrl {
//		issues = append(issues, "DOI is a URL, but should be a \\url{doi:10....} link")
//	}
//
//	// Check that doi has a doi: prefix
//	// e.g. \url{10.1000/182}
//	noPrefix, err := regexp.MatchString(`\\url{10\.`, bibItem.Ref)
//	if err != nil {
//		return nil, err
//	}
//	if noPrefix {
//		issues = append(issues, "DOI is not prefixed with doi:")
//	}
//
//	return issues, nil
//}

var containsDoi = regexp.MustCompile(`doi:\s10.`)
var containsSpace = regexp.MustCompile(`doi:\s10`)
var wrappedDoi = regexp.MustCompile(`\\url\{doi:10\.`)

func checkBibItem(bibItem BibItem) []Issue {
	var issues []Issue

	// DOI contains space e.g. doi: 10
	issueExists := containsSpace.FindStringIndex(bibItem.Ref)
	if issueExists != nil {
		location := Location{Start: issueExists[0] + bibItem.Location.Start, End: issueExists[1] + bibItem.Location.Start}
		issues = append(issues, Issue{Type: "DOI_CONTAINS_SPACE", Location: location})
	}

	ifContainsDoi := containsDoi.FindStringIndex(bibItem.Ref)
	if ifContainsDoi != nil {
		isWrapped := wrappedDoi.FindString(bibItem.Ref)
		if isWrapped == "" {
			location := Location{Start: ifContainsDoi[0] + bibItem.Location.Start, End: ifContainsDoi[1] + bibItem.Location.Start}
			issues = append(issues, Issue{Type: "DOI_NOT_WRAPPED", Location: location})
		}
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
