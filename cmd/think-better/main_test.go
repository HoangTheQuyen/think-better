package main

import (
	"bytes"
	"strings"
	"testing"
)

func TestRun(t *testing.T) {
	tests := []struct {
		args       []string
		code       int
		stdout     string // substring expected on stdout ("" = stdout empty)
		stderrPart string
	}{
		{nil, 1, "", "Usage:"},
		{[]string{"help"}, 0, "update", ""},
		{[]string{"--help"}, 0, "antigravity, opencode", ""},
		{[]string{"-h"}, 0, "Commands:", ""},
		{[]string{"-v"}, 0, "think-better ", ""},
		{[]string{"--version"}, 0, "think-better ", ""},
		{[]string{"bogus"}, 1, "", `unknown command "bogus"`},
		{[]string{"help", "bogus"}, 1, "", `unknown command "bogus"`},
	}
	for _, tt := range tests {
		var out, errOut bytes.Buffer
		code := run(tt.args, &out, &errOut)
		if code != tt.code {
			t.Errorf("run(%v) = %d, want %d", tt.args, code, tt.code)
		}
		if tt.stdout == "" && out.Len() != 0 {
			t.Errorf("run(%v): unexpected stdout %q", tt.args, out.String())
		}
		if !strings.Contains(out.String(), tt.stdout) {
			t.Errorf("run(%v): stdout %q lacks %q", tt.args, out.String(), tt.stdout)
		}
		if !strings.Contains(errOut.String(), tt.stderrPart) {
			t.Errorf("run(%v): stderr %q lacks %q", tt.args, errOut.String(), tt.stderrPart)
		}
	}
}

// Command help is printed by the command and exits 0.
func TestHelpCommand(t *testing.T) {
	for _, cmd := range []string{"init", "update", "list", "uninstall", "check", "version"} {
		var out, errOut bytes.Buffer
		if code := run([]string{"help", cmd}, &out, &errOut); code != 0 {
			t.Errorf("help %s = %d, want 0", cmd, code)
		}
		if code := run([]string{cmd, "--help"}, &out, &errOut); code != 0 {
			t.Errorf("%s --help = %d, want 0", cmd, code)
		}
	}
}
