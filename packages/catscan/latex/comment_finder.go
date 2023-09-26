package main

import (
	"regexp"
)

type Comment struct {
	Location Location `json:"location"`
}

func FindComments(contents string) []Comment {
	var commentRegex = regexp.MustCompile(`(?s)%.*?\n`)
	matches := commentRegex.FindAllStringIndex(contents, -1)
	comments := make([]Comment, 0)
	for _, match := range matches {
		comments = append(comments, Comment{Location: Location{Start: match[0], End: match[1]}})
	}
	return comments
}

func locationInComments(location Location, comments []Comment) bool {
	for _, comment := range comments {
		if LocationIn(location, comment.Location) {
			return true
		}
	}
	return false
}
