package skills

import (
	"bytes"
	"encoding/csv"
	"fmt"
	"io/fs"
	"os"
	"path"
	"regexp"
	"strings"
	"testing"

	"github.com/HoangTheQuyen/think-better/internal/skills/sourcefs"
)

// sourceRoot is the single source of truth that contributors edit.
const sourceRoot = "../../.agents"

// TestEmbeddedInSync fails when internal/skills/{skills,workflows} drift from
// .agents/. Fix it by running `go generate ./internal/skills` (or `make embed-prep`).
func TestEmbeddedInSync(t *testing.T) {
	for _, dir := range []string{"skills", "workflows"} {
		src := os.DirFS(path.Join(sourceRoot, dir))
		emb, err := fs.Sub(Content, dir)
		if dir == "workflows" {
			emb, err = fs.Sub(Workflows, dir)
		}
		if err != nil {
			t.Fatal(err)
		}

		srcFiles, err := sourcefs.Files(src)
		if err != nil {
			t.Fatalf("listing %s: %v", dir, err)
		}
		embFiles, err := sourcefs.Files(emb)
		if err != nil {
			t.Fatalf("listing embedded %s: %v", dir, err)
		}
		if strings.Join(srcFiles, "\n") != strings.Join(embFiles, "\n") {
			t.Fatalf("%s: embedded file list differs from .agents/%s — run `go generate ./internal/skills`\nsource:   %v\nembedded: %v", dir, dir, srcFiles, embFiles)
		}
		for _, f := range srcFiles {
			a, _ := fs.ReadFile(src, f)
			b, _ := fs.ReadFile(emb, f)
			if !bytes.Equal(a, b) {
				t.Errorf("%s/%s is out of date — run `go generate ./internal/skills`", dir, f)
			}
		}
	}
}

// TestSkillStructure enforces the contract every contributed skill must meet.
func TestSkillStructure(t *testing.T) {
	for _, skill := range Registry {
		sub, err := SkillFS(skill.Name)
		if err != nil {
			t.Fatal(err)
		}
		for _, required := range []string{"SKILL.md", "PROMPT.md"} {
			if _, err := fs.Stat(sub, required); err != nil {
				t.Errorf("%s: missing required file %s", skill.Name, required)
			}
		}

		csvs, _ := fs.Glob(sub, "data/*.csv")
		for _, f := range csvs {
			data, _ := fs.ReadFile(sub, f)
			r := csv.NewReader(bytes.NewReader(data))
			rows, err := r.ReadAll() // enforces a consistent column count
			if err != nil {
				t.Errorf("%s/%s: invalid CSV: %v", skill.Name, f, err)
				continue
			}
			if len(rows) < 2 {
				t.Errorf("%s/%s: want a header and at least one record", skill.Name, f)
			}
		}
	}
}

// TestWorkflowStructure checks each slash-command workflow has a description
// and only references skills that exist.
func TestWorkflowStructure(t *testing.T) {
	files, err := WorkflowFiles()
	if err != nil {
		t.Fatal(err)
	}
	wf, _ := WorkflowFS()
	for _, f := range files {
		data, _ := fs.ReadFile(wf, f)
		meta, err := ParseFrontmatter(string(data))
		if err != nil {
			t.Errorf("%s: %v", f, err)
			continue
		}
		if meta["description"] == "" {
			t.Errorf("%s: frontmatter description is required", f)
		}
		for _, issue := range plainScalarIssues(string(data)) {
			t.Errorf("%s: %s", f, issue)
		}
		for _, line := range strings.Split(string(data), "\n") {
			_, rest, ok := strings.Cut(line, ".agents/skills/")
			if !ok {
				continue
			}
			name, _, _ := strings.Cut(rest, "/")
			if FindSkill(name) == nil {
				t.Errorf("%s: references unknown skill %q", f, name)
			}
		}
	}
}

// TestSkillFrontmatterIsValidYAML catches frontmatter that our lenient parser
// accepts but strict YAML parsers (used by the AI tools) reject.
func TestSkillFrontmatterIsValidYAML(t *testing.T) {
	for _, skill := range Registry {
		data, err := fs.ReadFile(Content, "skills/"+skill.Name+"/SKILL.md")
		if err != nil {
			t.Fatal(err)
		}
		for _, issue := range plainScalarIssues(string(data)) {
			t.Errorf("%s/SKILL.md: %s", skill.Name, issue)
		}
	}
}

// plainScalarIssues reports unquoted frontmatter values containing ": " or " #",
// which end or break a YAML plain scalar. Block scalars (| or >) and quoted
// values are fine.
func plainScalarIssues(doc string) []string {
	lines := strings.Split(doc, "\n")
	var issues []string
	plain := false
	for i, line := range lines[1:] {
		if strings.TrimSpace(line) == "---" {
			break
		}
		value := line
		if !strings.HasPrefix(line, " ") && !strings.HasPrefix(line, "\t") {
			_, v, ok := strings.Cut(line, ":")
			if !ok {
				continue
			}
			value = strings.TrimSpace(v)
			plain = value != "" && !strings.ContainsAny(value[:1], "|>'\"")
		} else if !plain {
			continue
		}
		if plain && (strings.Contains(value, ": ") || strings.Contains(value, " #")) {
			issues = append(issues, fmt.Sprintf("frontmatter line %d: unquoted value contains \": \" or \" #\"; quote it or reword", i+2))
		}
	}
	return issues
}

func TestEveryWorkflowRunsAKnownSkill(t *testing.T) {
	files, err := WorkflowFiles()
	if err != nil {
		t.Fatal(err)
	}
	for _, f := range files {
		name := WorkflowSkill(f)
		if FindSkill(name) == nil {
			t.Errorf("%s: WorkflowSkill = %q, want a registered skill", f, name)
		}
	}
}

// stdinDelimiter ends every heredoc that carries the user's text. It must be a
// word no one types on a line of its own: if the user's text contained the
// delimiter line, the heredoc would end there and the rest would run as shell
// commands (Antigravity's "// turbo" runs them without asking).
const stdinDelimiter = "THINK_BETTER_EOF_7f3a"

var heredocOpener = regexp.MustCompile(`<<-?\s*(['"]?)([A-Za-z_][A-Za-z0-9_]*)(['"]?)`)

// skillDocs returns the agent-facing Markdown: every workflow and each skill's
// SKILL.md and PROMPT.md, keyed by a readable name.
func skillDocs(t *testing.T) map[string]string {
	t.Helper()
	docs := map[string]string{}
	files, err := WorkflowFiles()
	if err != nil {
		t.Fatal(err)
	}
	wf, _ := WorkflowFS()
	for _, f := range files {
		data, err := fs.ReadFile(wf, f)
		if err != nil {
			t.Fatal(err)
		}
		docs["workflows/"+f] = string(data)
	}
	for _, skill := range Registry {
		for _, name := range []string{"SKILL.md", "PROMPT.md"} {
			data, err := fs.ReadFile(Content, "skills/"+skill.Name+"/"+name)
			if err != nil {
				t.Fatal(err)
			}
			docs[skill.Name+"/"+name] = string(data)
		}
	}
	return docs
}

// Every heredoc uses the one quoted delimiter, so the shell expands nothing in
// the user's text; the old, guessable TASK delimiter is gone.
func TestHeredocsUseTheUniqueDelimiter(t *testing.T) {
	for name, doc := range skillDocs(t) {
		for i, line := range strings.Split(doc, "\n") {
			if strings.TrimSpace(line) == "TASK" {
				t.Errorf("%s:%d: heredoc ends with the old TASK delimiter; use %s", name, i+1, stdinDelimiter)
			}
			for _, m := range heredocOpener.FindAllStringSubmatch(line, -1) {
				if m[1] != "'" || m[3] != "'" || m[2] != stdinDelimiter {
					t.Errorf("%s:%d: heredoc %q, want <<'%s'", name, i+1, m[0], stdinDelimiter)
				}
			}
		}
	}
}

// $ARGUMENTS (the user's text) only ever appears alone inside a quoted
// heredoc, and every workflow tells the assistant to check the text for the
// delimiter line before running it.
func TestWorkflowsPassArgumentsOnStdin(t *testing.T) {
	for name, doc := range skillDocs(t) {
		if !strings.HasPrefix(name, "workflows/") {
			continue
		}
		lines := strings.Split(doc, "\n")
		found := false
		for i, line := range lines {
			if !strings.Contains(line, "$ARGUMENTS") {
				continue
			}
			found = true
			if line != "$ARGUMENTS" || i == 0 || i+1 >= len(lines) {
				t.Errorf("%s:%d: $ARGUMENTS must be alone on its line inside a heredoc", name, i+1)
				continue
			}
			if prev := lines[i-1]; !strings.Contains(prev, " --stdin ") || !strings.HasSuffix(prev, "<<'"+stdinDelimiter+"'") {
				t.Errorf("%s:%d: line before $ARGUMENTS must run --stdin and open <<'%s', got %q", name, i, stdinDelimiter, prev)
			}
			if lines[i+1] != stdinDelimiter {
				t.Errorf("%s:%d: line after $ARGUMENTS must be %s, got %q", name, i+2, stdinDelimiter, lines[i+1])
			}
		}
		if !found {
			t.Errorf("%s: never passes $ARGUMENTS to the script", name)
		}
		if !strings.Contains(doc, "no line of it is exactly\n  `"+stdinDelimiter+"`") &&
			!strings.Contains(doc, "no line of it is exactly `"+stdinDelimiter+"`") {
			t.Errorf("%s: must tell the assistant to check the text for the %s line first", name, stdinDelimiter)
		}
	}
}

// SKILL.md and PROMPT.md never show a placeholder for the user's text on the
// command line (search.py "<problem>" ...): those examples get copied.
func TestSkillDocsKeepUserTextOffTheCommandLine(t *testing.T) {
	placeholder := regexp.MustCompile(`search\.py\s+["']<`)
	for name, doc := range skillDocs(t) {
		for i, line := range strings.Split(doc, "\n") {
			if placeholder.MatchString(line) {
				t.Errorf("%s:%d: user text on the command line; pass it with --stdin and a heredoc: %s", name, i+1, strings.TrimSpace(line))
			}
		}
	}
}

// PROMPT.md is SKILL.md without its frontmatter.
func TestPromptMirrorsSkill(t *testing.T) {
	for _, skill := range Registry {
		s, _ := fs.ReadFile(Content, "skills/"+skill.Name+"/SKILL.md")
		p, _ := fs.ReadFile(Content, "skills/"+skill.Name+"/PROMPT.md")
		doc := string(s)
		end := strings.Index(doc[4:], "\n---\n")
		if end < 0 {
			t.Fatalf("%s/SKILL.md: no frontmatter", skill.Name)
		}
		body := strings.TrimLeft(doc[4+end+5:], "\n")
		if string(p) != body {
			t.Errorf("%s/PROMPT.md differs from the body of SKILL.md", skill.Name)
		}
	}
}

// All workflows share the same rules: what to do without text, on errors, in
// which language to answer and how to handle the Next steps table.
func TestWorkflowsShareRules(t *testing.T) {
	shared := []string{
		"### Rules",
		"### Steps",
		"- **No text**:",
		"- **Errors**:",
		"Never present a plan the script did not produce.",
		"- **Language**: answer in the user's language.",
		"- **Next steps**:",
	}
	for name, doc := range skillDocs(t) {
		if !strings.HasPrefix(name, "workflows/") {
			continue
		}
		for _, want := range shared {
			if !strings.Contains(doc, want) {
				t.Errorf("%s: missing shared rule %q", name, want)
			}
		}
		resume := strings.HasSuffix(name, ".resume.md")
		if resume && strings.Contains(doc, "save step-by-step") {
			t.Errorf("%s: offers to save a workspace that is already saved", name)
		}
		if !resume && strings.Contains(doc, "🎯 **Next Steps:**") {
			t.Errorf("%s: adds its own Next Steps table; the plan already ends with one", name)
		}
		if strings.Contains(doc, "--persist") && !strings.Contains(doc, `"step-by-step"`) {
			t.Errorf("%s: save step should accept the step-by-step save phrase", name)
		}
	}
	for _, f := range []string{"workflows/code.review.md"} {
		if !strings.Contains(skillDocs(t)[f], "`Review the current changes`") {
			t.Errorf("%s: with no text it should review the current changes", f)
		}
	}
}
