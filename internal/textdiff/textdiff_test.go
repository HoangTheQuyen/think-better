package textdiff

import (
	"math/rand"
	"strings"
	"testing"
)

// apply checks that ops turns a into b.
func apply(t *testing.T, a, b []string, ops []Op) {
	t.Helper()
	var gotA, gotB []string
	for _, op := range ops {
		if op.Kind != Insert {
			gotA = append(gotA, op.Line)
		}
		if op.Kind != Delete {
			gotB = append(gotB, op.Line)
		}
	}
	if strings.Join(gotA, "|") != strings.Join(a, "|") || strings.Join(gotB, "|") != strings.Join(b, "|") {
		t.Fatalf("edit script does not turn %q into %q: %v", a, b, ops)
	}
}

// lcs is the length of a longest common subsequence (dynamic programming).
func lcs(a, b []string) int {
	prev := make([]int, len(b)+1)
	for i := range a {
		cur := make([]int, len(b)+1)
		for j := range b {
			switch {
			case a[i] == b[j]:
				cur[j+1] = prev[j] + 1
			case prev[j+1] > cur[j]:
				cur[j+1] = prev[j+1]
			default:
				cur[j+1] = cur[j]
			}
		}
		prev = cur
	}
	return prev[len(b)]
}

func TestLinesIsMinimal(t *testing.T) {
	rng := rand.New(rand.NewSource(1))
	words := []string{"a", "b", "c", "d"}
	gen := func() []string {
		out := make([]string, rng.Intn(12))
		for i := range out {
			out[i] = words[rng.Intn(len(words))]
		}
		return out
	}
	for i := 0; i < 2000; i++ {
		a, b := gen(), gen()
		ops := Lines(a, b)
		apply(t, a, b, ops)
		edits := 0
		for _, op := range ops {
			if op.Kind != Equal {
				edits++
			}
		}
		if want := len(a) + len(b) - 2*lcs(a, b); edits != want {
			t.Fatalf("Lines(%q, %q): %d edits, want %d", a, b, edits, want)
		}
	}
}

func TestLinesTooDifferent(t *testing.T) {
	var a, b []string
	for i := 0; i < maxEdits; i++ {
		a = append(a, "a")
		b = append(b, "b")
	}
	ops := Lines(a, b)
	apply(t, a, b, ops)
}

func TestSplitLines(t *testing.T) {
	if got := SplitLines(""); got != nil {
		t.Errorf("SplitLines(\"\") = %q", got)
	}
	if got := SplitLines("a\nb"); len(got) != 2 || got[0] != "a\n" || got[1] != "b" {
		t.Errorf("SplitLines = %q", got)
	}
	if got := SplitLines("a\n"); len(got) != 1 {
		t.Errorf("SplitLines = %q", got)
	}
}

func TestUnified(t *testing.T) {
	if got := Unified("a", "b", "x\ny\n", "x\ny\n", 3); got != "" {
		t.Errorf("equal texts: %q", got)
	}

	a := "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n"
	b := "1\n2\nthree\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n15\n16\n"
	want := `--- mine
+++ new
@@ -1,6 +1,6 @@
 1
 2
-3
+three
 4
 5
 6
@@ -11,5 +11,5 @@
 11
 12
 13
-14
 15
+16
`
	if got := Unified("mine", "new", a, b, 3); got != want {
		t.Errorf("Unified =\n%s\nwant:\n%s", got, want)
	}

	// Changes close together share one hunk.
	got := Unified("a", "b", "1\n2\n3\n4\n5\n", "1\nx\n3\ny\n5\n", 1)
	want = "--- a\n+++ b\n@@ -1,5 +1,5 @@\n 1\n-2\n+x\n 3\n-4\n+y\n 5\n"
	if got != want {
		t.Errorf("Unified =\n%s\nwant:\n%s", got, want)
	}

	// Empty side and missing final newline.
	got = Unified("a", "b", "", "x", 3)
	want = "--- a\n+++ b\n@@ -0,0 +1 @@\n+x\n\\ No newline at end of file\n"
	if got != want {
		t.Errorf("Unified =\n%q\nwant:\n%q", got, want)
	}
}
