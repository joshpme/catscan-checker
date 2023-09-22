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
	Content string `json:"content"`
}

type Payload struct {
	Issues   []Issue   `json:"issues"`
	BibItems []BibItem `json:"bibItems"`
}

type Response struct {
	StatusCode int               `json:"statusCode,omitempty"`
	Headers    map[string]string `json:"headers,omitempty"`
	Body       string            `json:"body,omitempty"`
}

func Main(in Request) (*Response, error) {

	contents := in.Content
	comments := FindComments(contents)
	document := FindDocument(contents, comments)
	bibItems := FindValidBibItems(contents, comments, document)
	bibItemIssues := FindBibItemIssues(bibItems)

	payload := Payload{
		Issues:   bibItemIssues,
		BibItems: bibItems,
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
