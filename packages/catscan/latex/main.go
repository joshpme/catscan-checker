package main

import (
	"encoding/json"
	"fmt"
)

type Issue struct {
	Type     string   `json:"type"`
	Location Location `json:"location"`
}

type Request struct {
	Filename string `json:"filename"`
	Content  string `json:"content"`
}

type Payload struct {
	Filename string    `json:"filename"`
	Issues   []Issue   `json:"issues"`
	BibItems []BibItem `json:"bibItems"`
	Document Document  `json:"document"`
	Comments []Comment `json:"comments"`
	Contents string    `json:"content"`
}

type Response struct {
	StatusCode int               `json:"statusCode,omitempty"`
	Headers    map[string]string `json:"headers,omitempty"`
	Body       string            `json:"body,omitempty"`
}

func convertOffset(byteOffset int, contents string) int {
	return len([]rune(contents[:byteOffset]))
}

func Main(in Request) (*Response, error) {
	filename := in.Filename
	contents := in.Content
	comments := FindComments(contents)
	document := FindDocument(contents, comments)
	bibItems := FindValidBibItems(contents, comments, document)
	bibItemIssues := FindBibItemIssues(bibItems)

	for i, _ := range bibItemIssues {
		bibItemIssues[i].Location.Start = convertOffset(bibItemIssues[i].Location.Start, contents)
		bibItemIssues[i].Location.End = convertOffset(bibItemIssues[i].Location.End, contents)
	}

	payload := Payload{
		Document: document,
		Comments: comments,
		Issues:   bibItemIssues,
		BibItems: bibItems,
		Filename: filename,
		Contents: contents,
	}

	jsonBytes, err := json.Marshal(payload)

	if err != nil {
		return nil, fmt.Errorf("Error serializing response as json: %s", err.Error())
	}

	return &Response{
		Body: string(jsonBytes),
		Headers: map[string]string{
			"Content-Type": "application/json",
		},
	}, nil
}
