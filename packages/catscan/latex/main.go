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
	Contents string    `json:"content"`
	Issues   []Issue   `json:"issues"`
	BibItems []BibItem `json:"bibItems"`
	Document Document  `json:"-"`
	Comments []Comment `json:"-"`
}

type Response struct {
	StatusCode int               `json:"statusCode,omitempty"`
	Headers    map[string]string `json:"headers,omitempty"`
	Body       string            `json:"body,omitempty"`
}

func Main(in Request) (*Response, error) {
	filename := in.Filename
	contents := in.Content
	comments := FindComments(contents)
	document := FindDocument(contents, comments)
	bibItems := FindValidBibItems(contents, comments, document)
	bibItemIssues := FindBibItemIssues(bibItems)

	payload := Payload{
		Document: document,
		Comments: comments,
		Issues:   bibItemIssues,
		BibItems: bibItems,
		Filename: filename,
		Contents: contents,
	}

	jsonBytes, err := json.MarshalIndent(payload, "  ", "   ")

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
