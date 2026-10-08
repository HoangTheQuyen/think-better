package cli

import (
	"path/filepath"
	"strings"
	"testing"

	"github.com/HoangTheQuyen/think-better/internal/skills"
)

func TestUninstallHelp(t *testing.T) {
	e := newEnv(t)
	e.mustRun(0, RunUninstall, "--help")
	out := e.out.String()
	for _, want := range []string{"  --ai string", "  -y, --yes", "  --force", "  --all", "coding"} {
		if !strings.Contains(out, want) {
			t.Errorf("uninstall help lacks %q:\n%s", want, out)
		}
	}
	if strings.Contains(out, "\n  -ai") || strings.Contains(out, "\n  -y\n") {
		t.Errorf("help shows single-dash flags:\n%s", out)
	}
}

func TestUninstallDetectsTarget(t *testing.T) {
	e := newEnv(t)
	e.mustRun(1, RunUninstall, "--skill", "code-solving", "--yes")
	if !strings.Contains(e.err.String(), "not installed in this project") {
		t.Errorf("stderr:\n%s", e.err.String())
	}
	e.mustRun(1, RunUninstall, "--skill", "code-solving", "--all")
	e.mustRun(0, RunUninstall, "--all", "--yes")
	if !strings.Contains(e.out.String(), "No installed skills found") {
		t.Errorf("output:\n%s", e.out.String())
	}

	// Installed for one AI tool: no --ai needed.
	e.mustRun(0, RunInit, "--ai", "opencode", "--skill", "code-solving")
	e.mustRun(0, RunUninstall, "--skill", "code-solving", "-y")
	if exists(e.file(".opencode")) {
		t.Errorf("opencode install not removed:\n%s", e.out.String())
	}

	// Installed for two: ambiguous without a terminal.
	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "code-solving")
	e.mustRun(0, RunInit, "--ai", "opencode", "--skill", "code-solving")
	e.mustRun(1, RunUninstall, "--skill", "code-solving", "--yes")
	if !strings.Contains(e.err.String(), "claude, opencode") || !strings.Contains(e.err.String(), "--ai") {
		t.Errorf("stderr:\n%s", e.err.String())
	}

	// THINK_BETTER_AI settles it.
	t.Setenv("THINK_BETTER_AI", "opencode")
	e.mustRun(0, RunUninstall, "--skill", "code-solving", "--yes")
	if exists(e.file(".opencode")) || !exists(e.file(".claude", "skills", "code-solving", "SKILL.md")) {
		t.Error("THINK_BETTER_AI=opencode should remove only the opencode install")
	}
	t.Setenv("THINK_BETTER_AI", "")

	// Asked when a terminal is attached; "all of them" removes both.
	e.mustRun(0, RunInit, "--ai", "opencode", "--skill", "code-solving")
	e.answer("3\ny\n")
	e.mustRun(0, RunUninstall, "--skill", "code-solving")
	if exists(e.file(".opencode")) || exists(e.file(".claude")) {
		t.Errorf("both installs should be removed:\n%s\n%s", e.out.String(), e.err.String())
	}

	// Without a terminal and without --yes, nothing is removed.
	e.mustRun(0, RunInit, "--ai", "claude")
	interactive = func() bool { return false }
	e.mustRun(1, RunUninstall, "--all")
	if !strings.Contains(e.err.String(), "--yes") {
		t.Errorf("stderr:\n%s", e.err.String())
	}

	// --all removes every skill.
	e.mustRun(0, RunUninstall, "--all", "--yes", "--dry-run")
	if !exists(e.file(".claude", "skills", "make-decision", "SKILL.md")) {
		t.Error("dry run removed files")
	}
	e.mustRun(0, RunUninstall, "--all", "--yes")
	if exists(e.file(".claude")) {
		t.Errorf(".claude should be gone:\n%s", e.out.String())
	}
	for _, s := range skills.SkillNames() {
		if !strings.Contains(e.out.String(), "Removing skill \""+s+"\"") {
			t.Errorf("output does not mention %s:\n%s", s, e.out.String())
		}
	}
}

func TestUninstallYesKeepsAndForceDeletesModified(t *testing.T) {
	e := newEnv(t)
	dir := e.file(".claude", "skills", "code-solving")
	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "code-solving")
	e.write(filepath.Join(dir, "SKILL.md"), "my notes")
	e.mustRun(0, RunUninstall, "--skill", "code-solving", "--yes")
	if e.read(filepath.Join(dir, "SKILL.md")) != "my notes" || !strings.Contains(e.out.String(), "rerun with --force") {
		t.Errorf("--yes must keep modified files:\n%s", e.out.String())
	}

	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "code-solving")
	if !exists(filepath.Join(dir, "SKILL.md.new")) {
		t.Fatal("expected SKILL.md.new")
	}
	e.write(e.file(".claude", "commands", "code.md"), "my command")
	e.mustRun(0, RunUninstall, "--skill", "code-solving", "--force", "--dry-run")
	if !strings.Contains(e.out.String(), "Would delete .claude/skills/code-solving/SKILL.md (modified by you; --force)") || !exists(filepath.Join(dir, "SKILL.md")) {
		t.Errorf("dry run output:\n%s", e.out.String())
	}
	// --force needs no confirmation, as before.
	e.mustRun(0, RunUninstall, "--skill", "code-solving", "--force")
	if exists(e.file(".claude")) {
		t.Errorf("--force should delete modified files too:\n%s", e.out.String())
	}
	if !strings.Contains(e.out.String(), "Deleted .claude/commands/code.md (modified by you; --force)") {
		t.Errorf("output:\n%s", e.out.String())
	}
}

func TestUninstallConfirmationMentionsKeptFiles(t *testing.T) {
	e := newEnv(t)
	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "make-decision")
	e.write(e.file(".claude", "skills", "make-decision", "SKILL.md"), "mine")
	e.answer("n\n")
	e.mustRun(0, RunUninstall, "--skill", "make-decision")
	if !strings.Contains(e.err.String(), "keeping 1 file you modified?") || !strings.Contains(e.out.String(), "Canceled") {
		t.Errorf("prompt:\n%s", e.err.String())
	}
}

func TestUninstallCopilotOldLocation(t *testing.T) {
	e := newEnv(t)
	installV140Copilot(t, e.project, "make-decision")
	e.mustRun(0, RunUninstall, "--skill", "make-decision", "--yes")
	if exists(e.file(".github")) {
		t.Errorf("old install should be removed:\n%s", e.out.String())
	}
}
