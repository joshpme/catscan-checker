package main

import (
	"testing"
)

func TestFindLastDoi(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "Single DOI",
			input:    "This is a reference with DOI 10.1234/5678",
			expected: "10.1234/5678",
		},
		{
			name:     "Multiple DOIs - should return last one",
			input:    "First DOI: 10.1234/5678, Second DOI: 10.5678/9012, Last DOI: 10.9012/3456",
			expected: "10.9012/3456",
		},
		{
			name:     "No DOI",
			input:    "This is a reference without any DOI",
			expected: "",
		},
		{
			name:     "Empty string",
			input:    "",
			expected: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := findLastDoi(tt.input)
			if result != tt.expected {
				t.Errorf("findLastDoi() = %v, want %v", result, tt.expected)
			}
		})
	}
}
