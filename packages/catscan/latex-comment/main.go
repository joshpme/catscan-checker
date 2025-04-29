package main

import (
	"fmt"
	"latex/checker"
	"latex/finder"
	"latex/structs"
	"log"
	"os"
	"path/filepath"
	"strings"
)

func Finder(in structs.Request) structs.Contents {
	filename := in.Filename
	contents := in.Content
	comments := finder.FindComments(contents)
	document := finder.FindDocument(contents, comments)
	bibItems := finder.FindValidBibItems(contents, comments, document)
	return structs.Contents{
		Document: document,
		Comments: comments,
		BibItems: bibItems,
		Filename: filename,
		Content:  contents,
	}
}

func findFiles(directory string) []string {
	files := make([]string, 0)
	entries, err := os.ReadDir(directory)
	if err != nil {
		log.Fatalf("failed reading directory: %v", err)
	}

	for _, entry := range entries {
		if !entry.IsDir() && filepath.Ext(entry.Name()) == ".tex" {
			files = append(files, filepath.Join(directory, entry.Name()))
		}
	}
	return files
}

func getResult(fileName string, contents string) (*structs.Contents, error) {
	result := Finder(structs.Request{Content: contents, Filename: fileName})
	return &result, nil
}

func issueToDescription(issue structs.Issue) string {
	switch issue.Type {
	case "INCORRECT_STYLE_REFERENCE":
		return "Reference does not appear to be in the JACoW style, please adjust your reference style to be consistent with the JACoW style reference, please see https://www.jacow.org/Authors/FormattingCitations"
	case "ET_AL_WITH_COMMA":
		return "et al. is preceded by a comma, which is incorrect. Please remove the comma before the et al."
	case "ET_AL_NOT_WRAPPED":
		return "et al. is not wrapped in a macro to make it italic. Please use \\emph{et al.} instead of et al."
	case "DOI_CONTAINS_SPACE":
		return "DOI contains a space after the colon. Please remove the space."
	case "DOI_NOT_WRAPPED":
		return "DOI not wrapped in \\url{} macro. Please use \\url{doi:10.18429/JACoW-IPAC2023-XXXX} instead of doi:10.18429/JACoW-IPAC2023-XXXX"
	case "NO_DOI_PREFIX":
		return "DOI does not contain \"doi:\" prefix. It should appear like this \\url{doi:10.18429/JACoW-IPAC2023-XXXX}"
	case "DOI_IS_URL":
		return "DOI is written as a web URL (including https://doi.org/) which is incorrect. Remove the https://doi.org/, and write it as per this example. \\url{doi:10.18429/JACoW-IPAC2023-XXXX}"
	}
	return ""
}

type Request struct {
	Filename string `json:"filename"`
	Content  string `json:"content"`
}

type Response struct {
	StatusCode int               `json:"statusCode,omitempty"`
	Headers    map[string]string `json:"headers,omitempty"`
	Body       string            `json:"body,omitempty"`
}

func Main(in Request) (*Response, error) {

	fileName := in.Filename
	contents := in.Content

	// for each file, read the contents and run the main function
	result, err := getResult(fileName, contents)
	if err != nil {
		return nil, fmt.Errorf("error reading file: %w", err)
	}

	report := ""
	issueFound := false

	for _, bibItem := range result.BibItems {
		issues := checker.CheckBibItem(bibItem)
		if len(issues) > 0 {
			issueFound = true
			report += fmt.Sprintf("\nIssue found in reference %s:\n%s\n", strings.Trim(bibItem.Name, " \t\r\n"), strings.Trim(bibItem.Ref, " \t\n"))
			for _, issue := range issues {
				descriptionOfIssue := issueToDescription(issue)
				if descriptionOfIssue != "" {
					issueFound = true
					report += fmt.Sprintf(" %s\n", descriptionOfIssue)
				}
			}
		}

		doiResult, suggestion := checker.CheckDOIExists(bibItem)
		if doiResult == structs.HasIssue {
			issueFound = true
			if suggestion != nil {
				report += fmt.Sprintf("\nIssue found in reference DOI for reference %s:\n%s\n", strings.Trim(bibItem.Name, " \t\r\n"), strings.Trim(bibItem.Ref, " \t\n"))
				report += fmt.Sprintf("%s\n", suggestion.Description)
				if suggestion.Content != "" {
					report += fmt.Sprintf("Suggested DOI: %s\n", suggestion.Content)
				}
			}
		}
	}
	if issueFound {
		return &Response{
			StatusCode: 200,
			Body:       report,
		}, nil
	}
	return &Response{
		StatusCode: 200,
		Body:       "No issues found",
	}, nil
}

//
//func main() {
//	// find all the files in the examples folder
//	dirPath := "./examples"
//	fileNames := findFiles(dirPath)
//	if len(fileNames) == 0 {
//		fmt.Println("No .tex files found in the directory.")
//		return
//	}
//
//	for _, fileName := range fileNames {
//		file, err := os.Open(fileName)
//		if err != nil {
//			fmt.Printf("Error opening file %s: %v\n", fileName, err)
//			continue
//		}
//		defer file.Close()
//
//		contents, err := io.ReadAll(file)
//		if err != nil {
//			fmt.Printf("Error reading file %s: %v\n", fileName, err)
//			continue
//		}
//
//		response, err := Main(Request{
//			Filename: fileName,
//			Content:  string(contents),
//		})
//
//		if err != nil {
//			fmt.Printf("Error processing file %s: %v\n", fileName, err)
//			continue
//		}
//
//		if response.StatusCode == 200 {
//			fmt.Printf("File: %s\n", fileName)
//			fmt.Println(response.Body)
//			return
//		} else {
//			fmt.Printf("Error processing file %s: %s\n", fileName, response.Body)
//		}
//	}
//}
