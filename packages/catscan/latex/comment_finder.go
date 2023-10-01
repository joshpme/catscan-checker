package main

import (
	"github.com/dlclark/regexp2"
)

type Comment struct {
	Location Location `json:"location"`
}

var commentRegex = regexp2.MustCompile(`%.*?\n`, regexp2.Singleline)

func FindComments(contents string) []Comment {
	match, err := commentRegex.FindStringMatch(contents)
	comments := make([]Comment, 0)
	for err == nil && match != nil {
		comments = append(comments, Comment{
			Location: Location{
				Start: match.Index,
				End:   match.Index + match.Length,
			},
		})
		match, err = commentRegex.FindNextMatch(match)
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
