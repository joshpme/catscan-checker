package main

import (
	"regexp"
)

type Document struct {
	Location Location
}

func FindDocument(contents string, comments []Comment) Document {
	var documentBeginRegex = regexp.MustCompile(`\\begin{document}`)
	documentBeginMatches := documentBeginRegex.FindAllStringIndex(contents, -1)
	start := 0
	for _, match := range documentBeginMatches {
		location := Location{Start: match[0], End: match[1]}
		if !locationInComments(location, comments) {
			start = location.Start
			break
		}
	}

	var documentEndRegex = regexp.MustCompile(`\\end{document}`)
	documentEndMatches := documentEndRegex.FindAllStringIndex(contents, -1)
	end := len(contents) - 1
	for _, match := range documentEndMatches {
		location := Location{Start: match[0], End: match[1]}
		if !locationInComments(location, comments) {
			end = location.Start
			break
		}
	}

	return Document{Location{start, end}}
}
