package main

import (
	"os"
	"path/filepath"
	"testing"
)

func writeFile(t *testing.T, p, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}

func readFile(t *testing.T, p string) string {
	t.Helper()
	data, err := os.ReadFile(p)
	if err != nil {
		t.Fatal(err)
	}
	return string(data)
}

func TestRunMirrorsSources(t *testing.T) {
	src, dst := t.TempDir(), t.TempDir()
	writeFile(t, filepath.Join(src, "skills", "a", "SKILL.md"), "skill")
	writeFile(t, filepath.Join(src, "skills", "a", "__pycache__", "x.pyc"), "junk")
	writeFile(t, filepath.Join(src, "workflows", "a.md"), "workflow")
	writeFile(t, filepath.Join(dst, "skills", "stale", "SKILL.md"), "removed skill")

	if err := run(src, dst); err != nil {
		t.Fatal(err)
	}
	if got := readFile(t, filepath.Join(dst, "skills", "a", "SKILL.md")); got != "skill" {
		t.Errorf("SKILL.md = %q", got)
	}
	if got := readFile(t, filepath.Join(dst, "workflows", "a.md")); got != "workflow" {
		t.Errorf("a.md = %q", got)
	}
	for _, gone := range []string{"skills/stale", "skills/a/__pycache__", "skills.old", "workflows.old"} {
		if _, err := os.Stat(filepath.Join(dst, filepath.FromSlash(gone))); err == nil {
			t.Errorf("%s should not exist", gone)
		}
	}
	entries, _ := os.ReadDir(dst)
	if len(entries) != 2 {
		t.Errorf("dst holds %d entries, want skills and workflows only", len(entries))
	}
}

// A wrong -src must fail without deleting the existing copies.
func TestRunBadSourceKeepsCopies(t *testing.T) {
	dst := t.TempDir()
	writeFile(t, filepath.Join(dst, "skills", "a", "SKILL.md"), "keep me")
	writeFile(t, filepath.Join(dst, "workflows", "a.md"), "keep me too")

	missing := filepath.Join(t.TempDir(), "nonexistent")
	if err := run(missing, dst); err == nil {
		t.Fatal("run with a missing source succeeded")
	}
	half := t.TempDir() // skills present, workflows missing
	writeFile(t, filepath.Join(half, "skills", "b", "SKILL.md"), "new")
	if err := run(half, dst); err == nil {
		t.Fatal("run with no workflows succeeded")
	}

	if got := readFile(t, filepath.Join(dst, "skills", "a", "SKILL.md")); got != "keep me" {
		t.Errorf("existing copy changed: %q", got)
	}
	if got := readFile(t, filepath.Join(dst, "workflows", "a.md")); got != "keep me too" {
		t.Errorf("existing workflow changed: %q", got)
	}
	if _, err := os.Stat(filepath.Join(dst, "skills", "b")); err == nil {
		t.Error("partial copy should not be swapped in")
	}
}
