package targets

import "testing"

func TestFindTarget(t *testing.T) {
	tests := []struct {
		name  string
		found bool
	}{
		{"claude", true},
		{"copilot", true},
		{"antigravity", true},
		{"nonexistent", false},
		{"", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := FindTarget(tt.name)
			if tt.found && got == nil {
				t.Errorf("FindTarget(%q) = nil, want non-nil", tt.name)
			}
			if !tt.found && got != nil {
				t.Errorf("FindTarget(%q) = %v, want nil", tt.name, got)
			}
		})
	}
}

func TestFindTargetCaseInsensitive(t *testing.T) {
	tests := []string{
		"Claude",
		"CLAUDE",
		"Copilot",
		"COPILOT",
		"Antigravity",
		"ANTIGRAVITY",
	}

	for _, name := range tests {
		t.Run(name, func(t *testing.T) {
			got := FindTarget(name)
			if got == nil {
				t.Errorf("FindTarget(%q) = nil, want non-nil (case-insensitive)", name)
			}
		})
	}
}

func TestValidTarget(t *testing.T) {
	if !ValidTarget("claude") {
		t.Error("ValidTarget(\"claude\") = false, want true")
	}
	if ValidTarget("nonexistent") {
		t.Error("ValidTarget(\"nonexistent\") = true, want false")
	}
}

func TestTargetNames(t *testing.T) {
	names := TargetNames()
	if len(names) != len(Targets) {
		t.Errorf("TargetNames() returned %d, want %d", len(names), len(Targets))
	}

	expected := map[string]bool{
		"claude":      true,
		"copilot":     true,
		"antigravity": true,
	}
	for _, name := range names {
		if !expected[name] {
			t.Errorf("unexpected target name: %q", name)
		}
	}
}

func TestInstallDir(t *testing.T) {
	tests := []struct {
		target   string
		skill    string
		expected string
	}{
		{"claude", "make-decision", ".github/prompts/make-decision/"},
		{"copilot", "problem-solving-pro", ".github/prompts/problem-solving-pro/"},
		{"antigravity", "make-decision", ".agents/skills/make-decision/"},
	}

	for _, tt := range tests {
		t.Run(tt.target+"/"+tt.skill, func(t *testing.T) {
			target := FindTarget(tt.target)
			if target == nil {
				t.Fatalf("FindTarget(%q) = nil", tt.target)
			}
			got := target.InstallDir(tt.skill)
			if got != tt.expected {
				t.Errorf("InstallDir(%q) = %q, want %q", tt.skill, got, tt.expected)
			}
		})
	}
}

func TestValidateTarget(t *testing.T) {
	if err := ValidateTarget("claude"); err != nil {
		t.Errorf("ValidateTarget(\"claude\") = %v, want nil", err)
	}
	if err := ValidateTarget(""); err == nil {
		t.Error("ValidateTarget(\"\") = nil, want error")
	}
	if err := ValidateTarget("invalid"); err == nil {
		t.Error("ValidateTarget(\"invalid\") = nil, want error")
	}
}

func TestTargetFields(t *testing.T) {
	for _, target := range Targets {
		if target.Name == "" {
			t.Error("target has empty Name")
		}
		if target.DisplayName == "" {
			t.Errorf("target %q has empty DisplayName", target.Name)
		}
		if target.InstallPattern == "" {
			t.Errorf("target %q has empty InstallPattern", target.Name)
		}
	}
}
