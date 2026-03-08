package checker

import "testing"

func TestCheckPython(t *testing.T) {
	result := CheckPython()
	// We don't assert Found=true since Python may not be on all CI machines,
	// but we verify the struct is populated correctly in either case.
	if result.Found {
		if result.Version == "" {
			t.Error("Found=true but Version is empty")
		}
		if result.Path == "" {
			t.Error("Found=true but Path is empty")
		}
		// Version should start with "3."
		if len(result.Version) < 2 || result.Version[:2] != "3." {
			t.Errorf("unexpected version format: %q", result.Version)
		}
	} else {
		if result.Version != "" {
			t.Errorf("Found=false but Version=%q", result.Version)
		}
		if result.Path != "" {
			t.Errorf("Found=false but Path=%q", result.Path)
		}
	}
}

func TestFormatPythonWarning(t *testing.T) {
	found := PythonResult{Found: true, Version: "3.12.0", Path: "/usr/bin/python3"}
	if warning := FormatPythonWarning(found); warning != "" {
		t.Errorf("FormatPythonWarning(found=true) = %q, want empty", warning)
	}

	notFound := PythonResult{Found: false}
	warning := FormatPythonWarning(notFound)
	if warning == "" {
		t.Error("FormatPythonWarning(found=false) = empty, want warning message")
	}
}
