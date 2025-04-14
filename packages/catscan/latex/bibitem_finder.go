package main

import (
	"github.com/dlclark/regexp2"
	"strings"
)

type BibItem struct {
	Name         string   `json:"-"`
	OriginalText string   `json:"-"`
	Doi          string   `json:"doi"`
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
		items = append(items, BibItem{
			Name:         match.Groups()[1].String(),
			Ref:          removeExcessWhitespace(match.Groups()[2].String()),
			OriginalText: match.Groups()[2].String(),
			Location: Location{
				Start: match.Groups()[2].Index,
				End:   match.Groups()[2].Index + match.Groups()[2].Length,
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

var doiRegex = regexp2.MustCompile(`10.\d{4,9}/[-._;()/:A-Z0-9]+`, regexp2.Singleline)

func findLastDoi(reference string) string {
	var lastDoi string
	match, err := doiRegex.FindStringMatch(reference)
	for err == nil && match != nil {
		lastDoi = match.Groups()[0].String()
		match, err = doiRegex.FindNextMatch(match)
	}
	return lastDoi
}

func findDois(references []BibItem) []BibItem {
	var dois []BibItem
	for _, ref := range references {
		dois = append(dois, BibItem{
			Name:         ref.Name,
			Ref:          ref.Ref,
			OriginalText: ref.OriginalText,
			Location:     ref.Location,
			Doi:          findLastDoi(ref.Ref),
		})
	}
	return dois
}

func FindValidBibItems(contents string, comments []Comment, document Document) []BibItem {
	all := findBibItems(contents)
	noCommented := filterBibItemsInComments(all, comments)
	inDocument := filterBibItemInDocument(noCommented, document)
	withDois := findDois(inDocument)
	return withDois
}
