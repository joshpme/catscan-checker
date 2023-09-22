package main

import (
	"regexp"
	"strings"
)

type BibItem struct {
	Name         string   `json:"name"`
	OriginalText string   `json:"-"`
	Ref          string   `json:"ref"`
	Location     Location `json:"location"`
}

func removeExcessWhitespace(contents string) string {
	var whitespaceRegex = regexp.MustCompile(`(?s)\s+`)
	return whitespaceRegex.ReplaceAllString(contents, " ")
}

func findBibItems(contents string) []BibItem {
	var bibItemRegex = regexp.MustCompile(`(?s)\\bibitem{(.*?)}(.*?)(\\bibitem|\\end{thebibliography})`)
	var items []BibItem
	matches := bibItemRegex.FindAllStringSubmatchIndex(contents, -1)
	for _, match := range matches {
		matchStart := match[0]
		matchEnd := match[6] // before next bibitem or end of thebibliography
		nameStart := match[2]
		nameEnd := match[3]
		refStart := match[4]
		refEnd := match[5]
		refContent := removeExcessWhitespace(contents[refStart:refEnd])
		trimmedItem := strings.Trim(refContent, " \n\t")
		items = append(items, BibItem{
			Name:         contents[nameStart:nameEnd],
			Ref:          trimmedItem,
			OriginalText: contents[matchStart:matchEnd],
			Location:     Location{Start: matchStart, End: matchEnd},
		})
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
