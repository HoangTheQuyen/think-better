package skills

import "testing"

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
		if skill.EntryPoint == "" {
			t.Errorf("skill %q has empty EntryPoint", skill.Name)
		}
		if skill.AntigravityEntryPoint == "" {
			t.Errorf("skill %q has empty AntigravityEntryPoint", skill.Name)
		}
		if len(skill.Dependencies) == 0 {
			t.Errorf("skill %q has no Dependencies", skill.Name)
		}
	}
}
