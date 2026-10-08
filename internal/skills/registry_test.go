package skills

import (
	"testing"
	"testing/fstest"
)

func TestFindSkill(t *testing.T) {
	tests := []struct {
		name  string
		found bool
	}{
		{"make-decision", true},
		{"problem-solving-pro", true},
		{"nonexistent", false},
		{"", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := FindSkill(tt.name)
			if tt.found && got == nil {
				t.Errorf("FindSkill(%q) = nil, want non-nil", tt.name)
			}
			if !tt.found && got != nil {
				t.Errorf("FindSkill(%q) = %v, want nil", tt.name, got)
			}
		})
	}
}

func TestFindSkillCaseInsensitive(t *testing.T) {
	tests := []string{
		"Make-Decision",
		"MAKE-DECISION",
		"Make-decision",
		"PROBLEM-SOLVING-PRO",
		"Problem-Solving-Pro",
	}

	for _, name := range tests {
		t.Run(name, func(t *testing.T) {
			got := FindSkill(name)
			if got == nil {
				t.Errorf("FindSkill(%q) = nil, want non-nil (case-insensitive)", name)
			}
		})
	}
}

func TestSkillNames(t *testing.T) {
	names := SkillNames()
	if len(names) != len(Registry) {
		t.Errorf("SkillNames() returned %d names, want %d", len(names), len(Registry))
	}

	expected := map[string]bool{
		"code-solving":        true,
		"make-decision":       true,
		"problem-solving-pro": true,
	}
	for _, name := range names {
		if !expected[name] {
			t.Errorf("unexpected skill name: %q", name)
		}
	}
}

func TestRegistryFields(t *testing.T) {
	for _, skill := range Registry {
		if skill.Name == "" {
			t.Error("skill has empty Name")
		}
		if skill.Description == "" {
			t.Errorf("skill %q has empty Description", skill.Name)
		}
		if len(skill.Dependencies) == 0 {
			t.Errorf("skill %q has no Dependencies", skill.Name)
		}
	}
}

func TestNoDiscoveryErrors(t *testing.T) {
	for _, e := range discoveryErrors {
		t.Error(e)
	}
}

func TestDiscoverRejectsInvalidSkills(t *testing.T) {
	fsys := fstest.MapFS{
		"skills/good/SKILL.md":       {Data: []byte("---\nname: good\ndescription: Does a thing. Use when...\n---\n")},
		"skills/no-skill-md/x.md":    {Data: []byte("hi")},
		"skills/wrong-name/SKILL.md": {Data: []byte("---\nname: other\ndescription: x\n---\n")},
		"skills/no-desc/SKILL.md":    {Data: []byte("---\nname: no-desc\n---\n")},
	}
	pkgs, errs := discover(fsys)
	if len(pkgs) != 1 || pkgs[0].Name != "good" || pkgs[0].Description != "Does a thing." {
		t.Errorf("discover() pkgs = %+v, want only %q", pkgs, "good")
	}
	if len(errs) != 3 {
		t.Errorf("discover() errs = %v, want 3 errors", errs)
	}
}

func TestParseFrontmatter(t *testing.T) {
	doc := "---\nname: demo\ndescription: |\n  First line.\n  Second line.\nother: 'quoted'\n---\n# Body\n"
	meta, err := ParseFrontmatter(doc)
	if err != nil {
		t.Fatalf("ParseFrontmatter error: %v", err)
	}
	want := map[string]string{"name": "demo", "description": "First line. Second line.", "other": "quoted"}
	for k, v := range want {
		if meta[k] != v {
			t.Errorf("meta[%q] = %q, want %q", k, meta[k], v)
		}
	}

	for _, bad := range []string{"no frontmatter", "---\nname: x\n"} {
		if _, err := ParseFrontmatter(bad); err == nil {
			t.Errorf("ParseFrontmatter(%q) = nil error, want error", bad)
		}
	}
}
