package main

import (
	"github.com/dlclark/regexp2"
	"strings"
)

type BibItem struct {
	Name         string   `json:"-"`
	OriginalText string   `json:"-"`
	Ref          string   `json:"ref"`
	Location     Location `json:"location"`
}

func removeExcessWhitespace(contents string) string {
	var whitespaceRegex = regexp2.MustCompile(`\s+`, regexp2.Singleline)
	var withoutMoreThanOneSpace, _ = whitespaceRegex.Replace(contents, " ", 0, -1)
	return strings.Trim(withoutMoreThanOneSpace, " \n\t")
}

var bibItemRegex = regexp2.MustCompile(`\\bibitem\{(.*?)}(.*?)(?=(\\bibitem|\\end\{thebibliography}))`, regexp2.Singleline)

func findBibItems(contents string) []BibItem {
	var items []BibItem
	match, err := bibItemRegex.FindStringMatch(contents)
	for err == nil && match != nil {
		fullMatch := match.Groups()[0].Capture
		items = append(items, BibItem{
			Name:         match.Groups()[1].String(),
			Ref:          removeExcessWhitespace(match.Groups()[2].String()),
			OriginalText: match.Groups()[2].String(),
			Location: Location{
				Start: fullMatch.Index,
				End:   fullMatch.Index + fullMatch.Length,
			},
		})
		match, err = bibItemRegex.FindNextMatch(match)
	}
	return items
}

func filterBibItemsInComments(references []BibItem, comments []Comment) []BibItem {
	var filtered []BibItem
	for _, ref := range references {
		if !locationInComments(ref.Location, comments) {
			filtered = append(filtered, ref)
		}
	}
	return filtered
}

func filterBibItemInDocument(references []BibItem, document Document) []BibItem {
	var filtered []BibItem
	for _, ref := range references {
		if !LocationIn(ref.Location, document.Location) {
			filtered = append(filtered, ref)
		}
	}
	return filtered
}

func FindValidBibItems(contents string, comments []Comment, document Document) []BibItem {
	all := findBibItems(contents)
	noCommented := filterBibItemsInComments(all, comments)
	inDocument := filterBibItemInDocument(noCommented, document)
	return inDocument
}
