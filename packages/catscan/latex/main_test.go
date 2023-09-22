package main

import (
	"fmt"
	"io"
	"os"
	"testing"
)

func GetContents(fileName string) (string, error) {
	file, err := os.Open(fileName)
	if err != nil {
		return "", err
	}
	defer func() {
		if closeErr := file.Close(); closeErr != nil && err == nil {
			err = closeErr
		}
	}()
	contents, err := io.ReadAll(file)
	if err != nil {
		return "", err
	}
	return string(contents), nil
}

func TestMain(m *testing.M) {
	fileName := "./examples/paper.tex"
	contents, err := GetContents(fileName)

	if err != nil {
		fmt.Println(err)
		return
	}

	result, err := Main(Request{Content: contents})

	if err != nil {
		fmt.Println(err)
		return
	}

	fmt.Printf("%s\n", result.Body)
}
