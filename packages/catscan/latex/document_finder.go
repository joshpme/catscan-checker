package main

import (
	"github.com/dlclark/regexp2"
)

type Document struct {
	Location Location `json:"location"`
}

var documentBeginRegex = regexp2.MustCompile(`\\begin{document}`, 0)
var documentEndRegex = regexp2.MustCompile(`\\end{document}`, 0)

func FindDocument(contents string, comments []Comment) Document {
	match, err := documentBeginRegex.FindStringMatch(contents)
	start := 0
	for err == nil && match != nil {
		location := Location{Start: match.Index, End: match.Index + match.Length}
		if !locationInComments(location, comments) {
			start = location.Start
			break
		}
		match, err = documentBeginRegex.FindNextMatch(match)
	}

	match, err = documentEndRegex.FindStringMatch(contents)
	end := len(contents) - 1
	for err == nil && match != nil {
		location := Location{Start: match.Index, End: match.Index + match.Length}
		if !locationInComments(location, comments) {
			end = location.Start
			break
		}
		match, err = documentBeginRegex.FindNextMatch(match)
	}

	return Document{Location{start, end}}
}
