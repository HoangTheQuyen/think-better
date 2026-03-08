// Package checker provides prerequisite validation.
package checker

import (
	"os/exec"
	"strings"
)

// PythonResult holds the result of checking for Python 3.
type PythonResult struct {
	Found   bool
	Version string // e.g., "3.11.5"
	Path    string // e.g., "/usr/bin/python3"
}

// CheckPython checks for Python 3 availability on the system.
func CheckPython() PythonResult {
	// Try python3 first, then python
	for _, cmd := range []string{"python3", "python"} {
		path, err := exec.LookPath(cmd)
		if err != nil {
			continue
		}
		// Get version
		out, err := exec.Command(path, "--version").CombinedOutput()
		if err != nil {
			continue
		}
		ver := strings.TrimSpace(string(out))
		// "Python 3.11.5" → "3.11.5"
		if strings.HasPrefix(ver, "Python 3") {
			verNum := strings.TrimPrefix(ver, "Python ")
			return PythonResult{Found: true, Version: verNum, Path: path}
		}
	}
	return PythonResult{Found: false}
}

// FormatPythonWarning returns a warning string if Python is not found.
func FormatPythonWarning(result PythonResult) string {
	if result.Found {
		return ""
	}
	return "  ✗ Python 3 not found\n    Install from https://python.org or your package manager"
}
