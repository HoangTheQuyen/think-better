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
		{"opencode", true},
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
		"Opencode",
		"OPENCODE",
		"OpenCode",
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
		"opencode":    true,
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
		{"claude", "make-decision", ".claude/skills/make-decision/"},
		{"copilot", "problem-solving-pro", ".github/prompts/problem-solving-pro/"},
		{"antigravity", "make-decision", ".agents/skills/make-decision/"},
		{"opencode", "make-decision", ".opencode/skills/make-decision/"},
		{"opencode", "problem-solving-pro", ".opencode/skills/problem-solving-pro/"},
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

func TestAdaptWorkflow(t *testing.T) {
	src := "1. Read:\n// turbo\n```\ncat .agents/skills/make-decision/SKILL.md\n```\n"

	if got := FindTarget("antigravity").AdaptWorkflow(src); got != src {
		t.Errorf("antigravity should keep workflow unchanged, got:\n%s", got)
	}

	got := FindTarget("claude").AdaptWorkflow(src)
	want := "1. Read:\n```\ncat .claude/skills/make-decision/SKILL.md\n```\n"
	if got != want {
		t.Errorf("claude AdaptWorkflow =\n%s\nwant:\n%s", got, want)
	}
}

func TestOpenCodeCommands(t *testing.T) {
	opencode := FindTarget("opencode")
	if opencode.WorkflowDir() != ".opencode/commands/" {
		t.Errorf("WorkflowDir = %q, want .opencode/commands/", opencode.WorkflowDir())
	}
	if got := opencode.WorkflowFileName("code.debug.md"); got != "code.debug.md" {
		t.Errorf("WorkflowFileName = %q, want code.debug.md", got)
	}
	src := "---\ndescription: Fix a bug.\n---\n// turbo\n```\npython3 .agents/skills/code-solving/scripts/search.py --stdin <<'THINK_BETTER_EOF_7f3a'\n$ARGUMENTS\nTHINK_BETTER_EOF_7f3a\n```\n"
	want := "---\ndescription: Fix a bug.\n---\n```\npython3 .opencode/skills/code-solving/scripts/search.py --stdin <<'THINK_BETTER_EOF_7f3a'\n$ARGUMENTS\nTHINK_BETTER_EOF_7f3a\n```\n"
	if got := opencode.AdaptWorkflow(src); got != want {
		t.Errorf("opencode AdaptWorkflow =\n%s\nwant:\n%s", got, want)
	}
}

func TestAdaptWorkflowCopilotPrompt(t *testing.T) {
	copilot := FindTarget("copilot")
	if got := copilot.WorkflowFileName("code.debug.md"); got != "code.debug.prompt.md" {
		t.Errorf("WorkflowFileName = %q, want code.debug.prompt.md", got)
	}
	if got := FindTarget("claude").WorkflowFileName("code.debug.md"); got != "code.debug.md" {
		t.Errorf("claude WorkflowFileName = %q, want unchanged", got)
	}

	src := "---\ndescription: Fix a bug.\n---\n// turbo\n```\npython3 .agents/skills/code-solving/scripts/search.py --stdin --plan <<'THINK_BETTER_EOF_7f3a'\n$ARGUMENTS\nTHINK_BETTER_EOF_7f3a\n```\n"
	want := "---\nagent: agent\nargument-hint: Describe the task\ndescription: Fix a bug.\n---\n```\npython3 .github/prompts/code-solving/scripts/search.py --stdin --plan <<'THINK_BETTER_EOF_7f3a'\n${input:task}\nTHINK_BETTER_EOF_7f3a\n```\n"
	if got := copilot.AdaptWorkflow(src); got != want {
		t.Errorf("copilot AdaptWorkflow =\n%s\nwant:\n%s", got, want)
	}
}

func TestGlobalScope(t *testing.T) {
	if _, err := FindTarget("copilot").Global(); err == nil {
		t.Error("copilot Global() should be unsupported")
	}
	cases := map[string]string{
		"claude":      "~/.claude/skills/",
		"opencode":    "~/.config/opencode/skills/",
		"antigravity": "~/.gemini/config/skills/",
	}
	for name, root := range cases {
		project := FindTarget(name)
		g, err := project.Global()
		if err != nil {
			t.Fatalf("%s Global(): %v", name, err)
		}
		if !g.IsGlobal() || project.IsGlobal() {
			t.Errorf("%s: IsGlobal wrong (global %v, project %v)", name, g.IsGlobal(), project.IsGlobal())
		}
		got := g.RewriteSkillPaths("python3 .agents/skills/x/scripts/search.py")
		if want := "python3 " + root + "x/scripts/search.py"; got != want {
			t.Errorf("%s global RewriteSkillPaths = %q, want %q", name, got, want)
		}
	}

	// Antigravity keeps its "// turbo" annotations in the global scope too
	g, _ := FindTarget("antigravity").Global()
	if got := g.AdaptWorkflow("// turbo\n.agents/skills/x/"); got != "// turbo\n~/.gemini/config/skills/x/" {
		t.Errorf("antigravity global AdaptWorkflow = %q", got)
	}
}
