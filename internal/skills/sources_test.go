package skills

import (
	"bytes"
	"encoding/csv"
	"fmt"
	"io/fs"
	"os"
	"path"
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
