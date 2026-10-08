package cli

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// After uninstall keeps a modified file, the skill is not installed: check
// passes and update does not bring the skill back.
func TestUninstallKeepingFileStaysUninstalled(t *testing.T) {
	e := newEnv(t)
	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "make-decision")
	dir := e.file(".claude", "skills", "make-decision")
	e.write(filepath.Join(dir, "SKILL.md"), "my notes")
	e.mustRun(0, RunUninstall, "--ai", "claude", "--skill", "make-decision", "--force")

	e.mustRun(0, RunCheck)
	if strings.Contains(e.out.String(), "incomplete") {
		t.Errorf("check after uninstall:\n%s", e.out.String())
	}
	e.mustRun(0, RunUpdate)
	if !strings.Contains(e.out.String(), "No installed skills found") || exists(filepath.Join(dir, "PROMPT.md")) {
		t.Errorf("update re-created the uninstalled skill:\n%s", e.out.String())
	}
	if e.read(filepath.Join(dir, "SKILL.md")) != "my notes" {
		t.Error("kept file changed")
	}
	e.mustRun(1, RunUninstall, "--ai", "claude", "--skill", "make-decision", "--force")
}

// init --ai claude run in the home directory must not rewrite the
// user-level install with project-relative paths.
func TestInitInHomeDirectoryIsGlobal(t *testing.T) {
	e := newEnv(t)
	t.Chdir(e.home)
	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "make-decision")
	if !strings.Contains(e.err.String(), "using --global") {
		t.Errorf("expected a note about --global, stderr:\n%s", e.err.String())
	}
	skillMD := e.read(filepath.Join(e.home, ".claude", "skills", "make-decision", "SKILL.md"))
	if !strings.Contains(skillMD, "~/.claude/skills/") {
		t.Error("install in the home directory should use user-level (~/) paths")
	}
	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "make-decision", "--global")
	if !strings.Contains(e.out.String(), "is up to date") {
		t.Errorf("--global after init in home should change nothing:\n%s", e.out.String())
	}

	// Targets with separate project and user-level paths keep project scope.
	e.mustRun(0, RunInit, "--ai", "opencode", "--skill", "make-decision")
	if !exists(filepath.Join(e.home, ".opencode", "skills", "make-decision", "SKILL.md")) {
		t.Error("opencode project install in home should stay a project install")
	}
}

// Commands run from a subdirectory work on the project's install.
func TestCommandsFromSubdirectory(t *testing.T) {
	e := newEnv(t)
	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "make-decision")
	dir := e.file(".claude", "skills", "make-decision")
	e.simulateOld(dir, "SKILL.md", "old", "old")

	sub := e.file("src", "pkg")
	if err := os.MkdirAll(sub, 0o755); err != nil {
		t.Fatal(err)
	}
	t.Chdir(sub)

	e.mustRun(0, RunCheck)
	if !strings.Contains(e.out.String(), "outdated") {
		t.Errorf("check from a subdirectory should find the install:\n%s", e.out.String())
	}
	if !strings.Contains(e.err.String(), "using the project at") {
		t.Errorf("expected a note naming the project, stderr:\n%s", e.err.String())
	}
	e.mustRun(0, RunList)
	if !strings.Contains(e.out.String(), "claude") {
		t.Errorf("list from a subdirectory:\n%s", e.out.String())
	}
	e.mustRun(0, RunUpdate)
	if e.read(filepath.Join(dir, "SKILL.md")) == "old" || exists(filepath.Join(sub, ".claude")) {
		t.Error("update from a subdirectory should update the project's install")
	}

	// init installs where it runs, but says a parent has an install.
	e.mustRun(0, RunInit, "--ai", "opencode", "--skill", "make-decision", "--dry-run")
	if !strings.Contains(e.err.String(), "already has skills installed") {
		t.Errorf("init in a subdirectory should warn, stderr:\n%s", e.err.String())
	}

	e.mustRun(0, RunUninstall, "--ai", "claude", "--skill", "make-decision", "--force")
	if exists(dir) {
		t.Error("uninstall from a subdirectory should remove the project's install")
	}
}

// The search for an install stops at the repository root and never
// reaches the home directory.
func TestFindProject(t *testing.T) {
	e := newEnv(t)
	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "make-decision")
	inner := e.file("vendor", "other-repo")
	if err := os.MkdirAll(filepath.Join(inner, ".git", "objects"), 0o755); err != nil {
		t.Fatal(err)
	}
	sub := filepath.Join(inner, "sub")
	if err := os.MkdirAll(sub, 0o755); err != nil {
		t.Fatal(err)
	}
	if got := findProject(sub, e.home); got != inner {
		t.Errorf("findProject = %q, want the inner repository %q", got, inner)
	}
	if got := findProject(e.file("vendor"), e.home); got != e.project {
		t.Errorf("findProject = %q, want %q", got, e.project)
	}
	if got := findProject(e.home, e.home); got != "" {
		t.Errorf("findProject(home) = %q, want none", got)
	}
	homeSub := filepath.Join(e.home, "notes")
	if err := os.MkdirAll(homeSub, 0o755); err != nil {
		t.Fatal(err)
	}
	if got := findProject(homeSub, e.home); got != "" {
		t.Errorf("findProject(~/notes) = %q, want none (stop at home)", got)
	}
}
