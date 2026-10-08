package cli

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

func TestHelpShowsDoubleDashFlags(t *testing.T) {
	e := newEnv(t)
	e.mustRun(0, RunInit, "--help")
	out := e.out.String()
	for _, want := range []string{"  --ai string", "  --exclude-command command", "  --dry-run", "coding"} {
		if !strings.Contains(out, want) {
			t.Errorf("init help lacks %q:\n%s", want, out)
		}
	}
	if strings.Contains(out, "\n  -ai") {
		t.Errorf("help shows single-dash flags:\n%s", out)
	}
	e.mustRun(0, RunDiff, "--help")
	if !strings.Contains(e.out.String(), "  --context lines") || !strings.Contains(e.out.String(), `(default "3")`) {
		t.Errorf("diff help:\n%s", e.out.String())
	}
	e.mustRun(0, RunList, "--help")
	if !strings.Contains(e.out.String(), "coding") {
		t.Errorf("list help:\n%s", e.out.String())
	}
}

func TestPromptChoiceAsksAgain(t *testing.T) {
	e := newEnv(t)
	e.answer("9\nbogus\nopencode\n")
	e.mustRun(0, RunInit, "--skill", "make-decision")
	if !exists(e.file(".opencode", "skills", "make-decision", "SKILL.md")) {
		t.Error("third answer not used")
	}
	if strings.Count(e.err.String(), "is not one of the choices") != 2 {
		t.Errorf("stderr:\n%s", e.err.String())
	}

	e.answer("9\n0\nx\nclaude\n")
	e.mustRun(1, RunInit, "--skill", "make-decision")
	if !strings.Contains(e.err.String(), "no AI target selected") || exists(e.file(".claude")) {
		t.Errorf("should give up after %d answers:\n%s", promptAttempts, e.err.String())
	}
}

// installV140Copilot installs a skill with the Copilot layout of v1.4.0.
func installV140Copilot(t *testing.T, project, skill string) {
	t.Helper()
	legacy := targets.FindTarget("copilot").Legacy()[0]
	if _, err := installer.NewInstaller(project, "v1.4.0").Install(skills.FindSkill(skill), legacy, installer.Options{}); err != nil {
		t.Fatal(err)
	}
}

func TestCopilotOldLocation(t *testing.T) {
	e := newEnv(t)
	installV140Copilot(t, e.project, "code-solving")
	old := e.file(".github", "prompts", "code-solving")
	e.write(filepath.Join(old, "PROMPT.md"), "my prompt")

	e.mustRun(0, RunCheck)
	if !strings.Contains(e.out.String(), "old location (.github/prompts/code-solving/)") ||
		!strings.Contains(e.out.String(), "think-better update --ai copilot --skill code-solving") {
		t.Errorf("check output:\n%s", e.out.String())
	}
	e.mustRun(1, RunCheck, "--strict")

	e.mustRun(0, RunList, "--json")
	var list listOutput
	if err := json.Unmarshal(e.out.Bytes(), &list); err != nil {
		t.Fatal(err)
	}
	found := false
	for _, s := range list.Skills {
		for _, l := range s.Locations {
			if s.Name == "code-solving" && l.Legacy && l.Status == "outdated" && l.Path == ".github/prompts/code-solving/" {
				found = true
			}
		}
	}
	if !found {
		t.Errorf("list --json lacks the old location:\n%s", e.out.String())
	}

	e.mustRun(0, RunUpdate, "--dry-run")
	if !strings.Contains(e.out.String(), "Would move skill \"code-solving\" from .github/prompts/code-solving/ to .github/skills/code-solving/") ||
		!exists(filepath.Join(old, "SKILL.md")) {
		t.Errorf("dry run:\n%s", e.out.String())
	}

	e.mustRun(0, RunUpdate)
	out := e.out.String()
	if !strings.Contains(out, "Moved .github/prompts/code-solving/PROMPT.md to .github/skills/code-solving/PROMPT.md (modified by you)") {
		t.Errorf("update output:\n%s", out)
	}
	if exists(old) || e.read(e.file(".github", "skills", "code-solving", "PROMPT.md")) != "my prompt" ||
		!exists(e.file(".github", "skills", "code-solving", "PROMPT.md.new")) {
		t.Error("skill should be moved, keeping the modified PROMPT.md with a .new next to it")
	}
	if strings.Count(out, "Updating skill") != 0 {
		t.Errorf("the moved install should not be updated twice:\n%s", out)
	}
	prompt := e.read(e.file(".github", "prompts", "code.debug.prompt.md"))
	if !strings.Contains(prompt, ".github/skills/code-solving/") {
		t.Error("prompt files should point at the new location")
	}

	e.mustRun(0, RunCheck, "--strict")
	if strings.Contains(e.out.String(), "old location") {
		t.Errorf("check after update:\n%s", e.out.String())
	}
}

func TestInitMovesCopilotOldLocation(t *testing.T) {
	e := newEnv(t)
	installV140Copilot(t, e.project, "make-decision")
	e.mustRun(0, RunInit, "--ai", "copilot", "--skill", "make-decision")
	if exists(e.file(".github", "prompts", "make-decision")) || !exists(e.file(".github", "skills", "make-decision", "SKILL.md")) {
		t.Errorf("init should move the old install:\n%s", e.out.String())
	}
}

func TestCopilotGlobal(t *testing.T) {
	e := newEnv(t)
	e.mustRun(0, RunInit, "--ai", "copilot", "--global", "--skill", "code-solving")
	if !exists(filepath.Join(e.home, ".copilot", "skills", "code-solving", "SKILL.md")) {
		t.Error("global copilot skill not installed")
	}
	if !strings.Contains(e.out.String(), "not installed for your user account") || strings.Contains(e.out.String(), "/code.debug") {
		t.Errorf("output:\n%s", e.out.String())
	}
	skill := e.read(filepath.Join(e.home, ".copilot", "skills", "code-solving", "SKILL.md"))
	if strings.Contains(skill, ".agents/skills/") {
		t.Error("skill paths not rewritten")
	}
}

func TestDiffCommand(t *testing.T) {
	e := newEnv(t)
	e.mustRun(0, RunDiff)
	if !strings.Contains(e.out.String(), "nothing is waiting to be merged") {
		t.Errorf("output:\n%s", e.out.String())
	}

	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "code-solving")
	dir := e.file(".claude", "skills", "code-solving")
	want := e.read(filepath.Join(dir, "PROMPT.md"))
	mine := strings.Replace(want, "\n", "\nMY LINE\n", 1)
	e.simulateOld(dir, "PROMPT.md", "old", mine)
	e.mustRun(0, RunUpdate)
	if !strings.Contains(e.out.String(), "think-better diff") {
		t.Errorf("update should point at diff:\n%s", e.out.String())
	}

	e.mustRun(0, RunDiff)
	out := e.out.String()
	for _, s := range []string{
		"--- .claude/skills/code-solving/PROMPT.md (yours)\n",
		"+++ .claude/skills/code-solving/PROMPT.md.new (new version)\n",
		"\n-MY LINE\n",
		"mv <file>.new <file>",
		"think-better update --force",
	} {
		if !strings.Contains(out, s) {
			t.Errorf("diff output lacks %q:\n%s", s, out)
		}
	}
	e.mustRun(0, RunDiff, "--ai", "opencode")
	if !strings.Contains(e.out.String(), "nothing is waiting") {
		t.Errorf("--ai filter:\n%s", e.out.String())
	}
	e.mustRun(0, RunDiff, "--global")
	if !strings.Contains(e.out.String(), "nothing is waiting") {
		t.Errorf("--global filter:\n%s", e.out.String())
	}

	// A .new equal to the file only needs removing.
	e.write(filepath.Join(dir, "PROMPT.md"), want)
	e.mustRun(0, RunDiff, "--skill", "code-solving")
	if !strings.Contains(e.out.String(), "PROMPT.md.new is identical") {
		t.Errorf("output:\n%s", e.out.String())
	}
	e.mustRun(1, RunDiff, "--context", "-1")
	e.mustRun(1, RunDiff, "--ai", "nope")
	e.mustRun(1, RunDiff, "--skill", "nope")
}

func TestExcludeCommand(t *testing.T) {
	e := newEnv(t)
	cmds := e.file(".claude", "commands")
	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "code-solving", "--exclude-command", "/code.perf,code.test.md")
	if exists(filepath.Join(cmds, "code.perf.md")) || exists(filepath.Join(cmds, "code.test.md")) || !exists(filepath.Join(cmds, "code.md")) {
		t.Error("excluded commands installed")
	}
	if !strings.Contains(e.out.String(), "/code.feature, /code.refactor") || !strings.Contains(e.out.String(), "Excluded slash commands: /code.perf, /code.test") {
		t.Errorf("output:\n%s", e.out.String())
	}

	e.mustRun(0, RunUpdate)
	e.mustRun(0, RunCheck, "--strict")
	if exists(filepath.Join(cmds, "code.perf.md")) {
		t.Error("update restored an excluded command")
	}

	e.mustRun(0, RunUpdate, "--include-command", "code.perf", "--dry-run")
	if exists(filepath.Join(cmds, "code.perf.md")) || !strings.Contains(e.out.String(), "Would create .claude/commands/code.perf.md") {
		t.Errorf("dry run:\n%s", e.out.String())
	}
	e.mustRun(0, RunUpdate, "--include-command", "code.perf")
	if !exists(filepath.Join(cmds, "code.perf.md")) || exists(filepath.Join(cmds, "code.test.md")) {
		t.Error("--include-command should restore only that command")
	}

	// A deleted command comes back, with a hint how to keep it removed.
	if err := os.Remove(filepath.Join(cmds, "code.debug.md")); err != nil {
		t.Fatal(err)
	}
	e.mustRun(0, RunUpdate)
	if !exists(filepath.Join(cmds, "code.debug.md")) || !strings.Contains(e.out.String(), "think-better update --exclude-command code.debug") {
		t.Errorf("output:\n%s", e.out.String())
	}

	e.mustRun(1, RunUpdate, "--exclude-command", "nope")
	e.mustRun(1, RunInit, "--ai", "claude", "--exclude-command", "nope")
	e.mustRun(1, RunInit, "--ai", "claude", "--exclude-command", "code", "--include-command", "code")
}

func TestNormalizeCommand(t *testing.T) {
	for in, want := range map[string]string{"/code.perf": "code.perf", "code.perf.prompt.md": "code.perf", "decide.md": "decide", " solve ": "solve"} {
		if got := normalizeCommand(in); got != want {
			t.Errorf("normalizeCommand(%q) = %q, want %q", in, got, want)
		}
	}
}
