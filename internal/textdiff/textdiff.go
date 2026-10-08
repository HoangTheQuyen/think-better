// Package textdiff computes line-based unified diffs (Myers' algorithm),
// using only the standard library.
package textdiff

import (
	"fmt"
	"strings"
)

// OpKind is the kind of one line in an edit script.
type OpKind byte

const (
	Equal  OpKind = ' '
	Delete OpKind = '-'
	Insert OpKind = '+'
)

// Op is one line of an edit script: a line of a kept (Equal), removed
// from a (Delete) or added from b (Insert).
type Op struct {
	Kind OpKind
	Line string
}

// SplitLines splits text into lines, keeping each line's "\n". A final line
// without a newline is kept as is.
func SplitLines(text string) []string {
	if text == "" {
		return nil
	}
	lines := strings.SplitAfter(text, "\n")
	if lines[len(lines)-1] == "" {
		lines = lines[:len(lines)-1]
	}
	return lines
}

// Lines returns a shortest edit script turning a into b.
func Lines(a, b []string) []Op {
	// Common prefix and suffix need no search.
	pre := 0
	for pre < len(a) && pre < len(b) && a[pre] == b[pre] {
		pre++
	}
	suf := 0
	for suf < len(a)-pre && suf < len(b)-pre && a[len(a)-1-suf] == b[len(b)-1-suf] {
		suf++
	}
	ops := make([]Op, 0, len(a)+len(b))
	for _, l := range a[:pre] {
		ops = append(ops, Op{Equal, l})
	}
	ops = append(ops, myers(a[pre:len(a)-suf], b[pre:len(b)-suf])...)
	for _, l := range a[len(a)-suf:] {
		ops = append(ops, Op{Equal, l})
	}
	return ops
}

// myers is the O((N+M)D) greedy algorithm from Myers, "An O(ND) Difference
// Algorithm and Its Variations" (1986), keeping each round's frontier so
// the path can be traced back.
func myers(a, b []string) []Op {
	n, m := len(a), len(b)
	if n == 0 || m == 0 {
		return replaceAll(a, b)
	}
	limit := min(n+m, maxEdits)
	offset := limit + 1
	v := make([]int, 2*limit+3)
	// trace[d] holds v[-d..d] at the start of round d: the only part round
	// d reads, so memory grows with D² rather than D·(N+M).
	var trace [][]int
	for d := 0; d <= limit; d++ {
		trace = append(trace, append([]int(nil), v[offset-d:offset+d+1]...))
		for k := -d; k <= d; k += 2 {
			var x int
			if k == -d || (k != d && v[offset+k-1] < v[offset+k+1]) {
				x = v[offset+k+1] // down: insert from b
			} else {
				x = v[offset+k-1] + 1 // right: delete from a
			}
			y := x - k
			for x < n && y < m && a[x] == b[y] {
				x++
				y++
			}
			v[offset+k] = x
			if x >= n && y >= m {
				return backtrack(a, b, trace, d)
			}
		}
	}
	// Too different to be worth a minimal script.
	return replaceAll(a, b)
}

// replaceAll is the edit script that deletes all of a and inserts all of b.
func replaceAll(a, b []string) []Op {
	ops := make([]Op, 0, len(a)+len(b))
	for _, l := range a {
		ops = append(ops, Op{Delete, l})
	}
	for _, l := range b {
		ops = append(ops, Op{Insert, l})
	}
	return ops
}

// maxEdits bounds the search; files that differ in more lines than this are
// shown as entirely replaced.
const maxEdits = 2000

// backtrack walks the saved frontiers from the end back to the start.
func backtrack(a, b []string, trace [][]int, dEnd int) []Op {
	x, y := len(a), len(b)
	var rev []Op
	for d := dEnd; d > 0; d-- {
		w := trace[d] // v[-d..d] at the start of round d (end of round d-1)
		v := func(k int) int { return w[k+d] }
		k := x - y
		var prevK int
		if k == -d || (k != d && v(k-1) < v(k+1)) {
			prevK = k + 1
		} else {
			prevK = k - 1
		}
		prevX := v(prevK)
		prevY := prevX - prevK
		for x > prevX && y > prevY {
			x--
			y--
			rev = append(rev, Op{Equal, a[x]})
		}
		if x == prevX {
			y--
			rev = append(rev, Op{Insert, b[y]})
		} else {
			x--
			rev = append(rev, Op{Delete, a[x]})
		}
	}
	for x > 0 && y > 0 {
		x--
		y--
		rev = append(rev, Op{Equal, a[x]})
	}
	ops := make([]Op, len(rev))
	for i, op := range rev {
		ops[len(rev)-1-i] = op
	}
	return ops
}

// Unified returns a unified diff of a and b with context lines around each
// change, headed by "--- aName" and "+++ bName"; "" when they are equal.
func Unified(aName, bName, a, b string, context int) string {
	ops := Lines(SplitLines(a), SplitLines(b))
	changed := false
	for _, op := range ops {
		if op.Kind != Equal {
			changed = true
			break
		}
	}
	if !changed {
		return ""
	}

	var sb strings.Builder
	fmt.Fprintf(&sb, "--- %s\n+++ %s\n", aName, bName)
	// aLine/bLine: 1-based line numbers of ops[i] in a and b.
	aLine := make([]int, len(ops)+1)
	bLine := make([]int, len(ops)+1)
	aLine[0], bLine[0] = 1, 1
	for i, op := range ops {
		aLine[i+1], bLine[i+1] = aLine[i], bLine[i]
		if op.Kind != Insert {
			aLine[i+1]++
		}
		if op.Kind != Delete {
			bLine[i+1]++
		}
	}

	for i := 0; i < len(ops); {
		if ops[i].Kind == Equal {
			i++
			continue
		}
		// A hunk starts context lines before the first change and runs until
		// a gap of more than 2*context unchanged lines.
		start := max(i-context, 0)
		end := i
		for j := i; j < len(ops); j++ {
			if ops[j].Kind != Equal {
				end = j + 1
				continue
			}
			if j-end >= 2*context {
				break
			}
		}
		stop := min(end+context, len(ops))
		aCount, bCount := 0, 0
		for _, op := range ops[start:stop] {
			if op.Kind != Insert {
				aCount++
			}
			if op.Kind != Delete {
				bCount++
			}
		}
		fmt.Fprintf(&sb, "@@ -%s +%s @@\n", hunkRange(aLine[start], aCount), hunkRange(bLine[start], bCount))
		for _, op := range ops[start:stop] {
			sb.WriteByte(byte(op.Kind))
			sb.WriteString(op.Line)
			if !strings.HasSuffix(op.Line, "\n") {
				sb.WriteString("\n\\ No newline at end of file\n")
			}
		}
		i = stop
	}
	return sb.String()
}

// hunkRange formats "start,count" as in GNU diff: an empty range is given
// as the line before it, and a count of 1 is omitted.
func hunkRange(start, count int) string {
	switch count {
	case 0:
		return fmt.Sprintf("%d,0", start-1)
	case 1:
		return fmt.Sprintf("%d", start)
	}
	return fmt.Sprintf("%d,%d", start, count)
}
