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
