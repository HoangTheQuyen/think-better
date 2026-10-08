package installer

import (
	"errors"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"testing"

	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// installLegacyCopilot installs a skill the way releases up to v1.4.0 did
// for Copilot: skill files in .github/prompts/<skill>/ next to the prompt files.
func installLegacyCopilot(t *testing.T, base string, skill *skills.SkillPackage) *targets.AITarget {
	t.Helper()
	legacy := targets.FindTarget("copilot").Legacy()[0]
	if _, err := NewInstaller(base, "v1.4.0").Install(skill, legacy, Options{}); err != nil {
		t.Fatal(err)
	}
	return legacy
}

func readFile(t *testing.T, p string) string {
	t.Helper()
	data, err := os.ReadFile(p)
	if err != nil {
		t.Fatal(err)
	}
	return string(data)
}

func TestMigrateLegacyCopilot(t *testing.T) {
	base := t.TempDir()
	skill := skills.FindSkill("code-solving")
	legacy := installLegacyCopilot(t, base, skill)
	target := targets.FindTarget("copilot")
	oldDir := filepath.Join(base, ".github", "prompts", "code-solving")
	newDir := filepath.Join(base, ".github", "skills", "code-solving")

	// The user edited two files and added one of their own.
	if err := os.WriteFile(filepath.Join(oldDir, "PROMPT.md"), []byte("my prompt"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(oldDir, "scripts", "core.py"), []byte("# mine"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(oldDir, "notes.txt"), []byte("notes"), 0o644); err != nil {
		t.Fatal(err)
	}
	// The new location already has a different core.py: that one is kept in place.
	if err := os.MkdirAll(filepath.Join(newDir, "scripts"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(newDir, "scripts", "core.py"), []byte("# other"), 0o644); err != nil {
		t.Fatal(err)
	}

	inst := NewInstaller(base, testVersion)
	dry, err := inst.MigrateLegacy(skill, legacy, target, Options{DryRun: true})
	if err != nil {
		t.Fatal(err)
	}
	if !onDisk(t, filepath.Join(oldDir, "SKILL.md")) || onDisk(t, filepath.Join(newDir, "PROMPT.md")) {
		t.Fatal("dry run changed files")
	}

	res, err := inst.MigrateLegacy(skill, legacy, target, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if !slices.Equal(res.Moved, dry.Moved) || !slices.Equal(res.Removed, dry.Removed) {
		t.Errorf("dry run planned %v/%v, did %v/%v", dry.Moved, dry.Removed, res.Moved, res.Removed)
	}
	if !slices.Equal(res.Moved, []string{"PROMPT.md"}) || !slices.Equal(res.Kept, []string{"scripts/core.py"}) {
		t.Errorf("moved %v, kept %v", res.Moved, res.Kept)
	}
	if !slices.Contains(res.Removed, "SKILL.md") || slices.Contains(res.Removed, "PROMPT.md") {
		t.Errorf("removed %v", res.Removed)
	}
	if readFile(t, filepath.Join(newDir, "PROMPT.md")) != "my prompt" || onDisk(t, filepath.Join(oldDir, "PROMPT.md")) {
		t.Error("the modified PROMPT.md should move to the new location")
	}
	if readFile(t, filepath.Join(oldDir, "scripts", "core.py")) != "# mine" || readFile(t, filepath.Join(newDir, "scripts", "core.py")) != "# other" {
		t.Error("a modified file whose new path is taken must stay where it is")
	}
	if onDisk(t, filepath.Join(oldDir, "SKILL.md")) || onDisk(t, filepath.Join(oldDir, SkillManifestName)) {
		t.Error("unmodified files and the old manifest should be removed")
	}
	if !onDisk(t, filepath.Join(oldDir, "notes.txt")) || res.DirRemoved {
		t.Error("files think-better did not install are kept, and so is their directory")
	}

	// Install at the new location then treats the moved file as modified.
	ires, err := inst.Install(skill, target, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if actionOf(ires.Files, "PROMPT.md") != ActionKeepNew || actionOf(ires.Files, "SKILL.md") != ActionCreate {
		t.Errorf("install after move: PROMPT.md %s, SKILL.md %s", actionOf(ires.Files, "PROMPT.md"), actionOf(ires.Files, "SKILL.md"))
	}
	if !strings.Contains(readFile(t, filepath.Join(newDir, "SKILL.md")), ".github/skills/code-solving/") {
		t.Error("SKILL.md should reference the new location")
	}
	// Prompt files were written for the old layout; unmodified ones are updated in place.
	prompt := readFile(t, filepath.Join(base, ".github", "prompts", "code.debug.prompt.md"))
	if strings.Contains(prompt, ".github/prompts/code-solving") || !strings.Contains(prompt, ".github/skills/code-solving") {
		t.Error("prompt files should point at the new skill location")
	}
	if actionOf(ires.Workflows, "code.debug.prompt.md") != ActionUpdate {
		t.Errorf("code.debug.prompt.md: %s, want update", actionOf(ires.Workflows, "code.debug.prompt.md"))
	}
}

func TestMigrateLegacyRemovesEmptyOldDir(t *testing.T) {
	base := t.TempDir()
	skill := skills.FindSkill("make-decision")
	legacy := installLegacyCopilot(t, base, skill)
	oldDir := filepath.Join(base, ".github", "prompts", "make-decision")
	if err := os.WriteFile(filepath.Join(oldDir, "SKILL.md.new"), []byte("stale"), 0o644); err != nil {
		t.Fatal(err)
	}
	res, err := NewInstaller(base, testVersion).MigrateLegacy(skill, legacy, targets.FindTarget("copilot"), Options{})
	if err != nil {
		t.Fatal(err)
	}
	// A .new file that is not the offered version is the user's: kept.
	if res.DirRemoved || !onDisk(t, filepath.Join(oldDir, "SKILL.md.new")) {
		t.Fatal("unknown .new file should be kept")
	}
	if err := os.Remove(filepath.Join(oldDir, "SKILL.md.new")); err != nil {
		t.Fatal(err)
	}
	if _, err := NewInstaller(base, testVersion).MigrateLegacy(skill, legacy, targets.FindTarget("copilot"), Options{}); !errors.Is(err, ErrNotInstalled) {
		t.Errorf("second migration: %v, want ErrNotInstalled", err)
	}

	base = t.TempDir()
	installLegacyCopilot(t, base, skill)
	res, err = NewInstaller(base, testVersion).MigrateLegacy(skill, legacy, targets.FindTarget("copilot"), Options{})
	if err != nil {
		t.Fatal(err)
	}
	if !res.DirRemoved || onDisk(t, filepath.Join(base, ".github", "prompts", "make-decision")) {
		t.Error("the emptied old directory should be removed")
	}
	if !onDisk(t, filepath.Join(base, ".github", "prompts", "decide.prompt.md")) {
		t.Error("prompt files must stay")
	}
}

func TestMigrateLegacyWithoutManifest(t *testing.T) {
	base := t.TempDir()
	skill := skills.FindSkill("make-decision")
	legacy := installLegacyCopilot(t, base, skill)
	oldDir := filepath.Join(base, ".github", "prompts", "make-decision")
	if err := os.Remove(filepath.Join(oldDir, SkillManifestName)); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(oldDir, "SKILL.md"), []byte("old release"), 0o644); err != nil {
		t.Fatal(err)
	}
	res, err := NewInstaller(base, testVersion).MigrateLegacy(skill, legacy, targets.FindTarget("copilot"), Options{})
	if err != nil {
		t.Fatal(err)
	}
	// Without a manifest, content that differs from this version is kept as the user's.
	if !slices.Equal(res.Moved, []string{"SKILL.md"}) || !res.DirRemoved {
		t.Errorf("moved %v, dir removed %v", res.Moved, res.DirRemoved)
	}
}

func TestMigrateLegacySameDir(t *testing.T) {
	skill := skills.FindSkill("make-decision")
	claude := targets.FindTarget("claude")
	if _, err := NewInstaller(t.TempDir(), testVersion).MigrateLegacy(skill, claude, claude, Options{}); err == nil {
		t.Error("migrating a location onto itself should fail")
	}
}

func TestExcludedWorkflows(t *testing.T) {
	base := t.TempDir()
	skill := skills.FindSkill("code-solving")
	target := targets.FindTarget("claude")
	inst := NewInstaller(base, testVersion)
	if _, err := inst.Install(skill, target, Options{}); err != nil {
		t.Fatal(err)
	}
	cmds := filepath.Join(base, ".claude", "commands")
	if err := os.WriteFile(filepath.Join(cmds, "code.test.md"), []byte("mine"), 0o644); err != nil {
		t.Fatal(err)
	}

	// A dry run with an exclusion list does not save it.
	res, err := inst.Install(skill, target, Options{DryRun: true, ExcludeWorkflows: []string{"code.perf.md"}})
	if err != nil {
		t.Fatal(err)
	}
	if actionOf(res.Workflows, "code.perf.md") != ActionRemove || !onDisk(t, filepath.Join(cmds, "code.perf.md")) {
		t.Errorf("dry run: code.perf.md %s", actionOf(res.Workflows, "code.perf.md"))
	}
	if list, _ := inst.ExcludedWorkflows(target); len(list) != 0 {
		t.Errorf("dry run saved %v", list)
	}

	if err := inst.SetExcludedWorkflows(target, []string{"code.perf.md", "code.test.md", "code.perf.md"}); err != nil {
		t.Fatal(err)
	}
	if list, _ := inst.ExcludedWorkflows(target); !slices.Equal(list, []string{"code.perf.md", "code.test.md"}) {
		t.Errorf("ExcludedWorkflows = %v", list)
	}
	res, err = inst.Install(skill, target, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if onDisk(t, filepath.Join(cmds, "code.perf.md")) || readFile(t, filepath.Join(cmds, "code.test.md")) != "mine" {
		t.Error("excluded: unmodified command removed, modified one kept")
	}
	if actionOf(res.Workflows, "code.test.md") != ActionKeepRemoved {
		t.Errorf("code.test.md: %s", actionOf(res.Workflows, "code.test.md"))
	}

	// Not restored, and not missing or outdated.
	res, err = inst.Install(skill, target, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if onDisk(t, filepath.Join(cmds, "code.perf.md")) || res.Count(ActionCreate) != 0 {
		t.Error("excluded command restored")
	}
	st, err := CheckStatus(skill, target, base, testVersion)
	if err != nil {
		t.Fatal(err)
	}
	if st.Status != StatusInstalled {
		t.Errorf("status %s (missing %v), want installed", st.Status, st.Missing)
	}

	// Including it again restores it.
	if err := inst.SetExcludedWorkflows(target, nil); err != nil {
		t.Fatal(err)
	}
	if _, err := inst.Install(skill, target, Options{}); err != nil {
		t.Fatal(err)
	}
	if !onDisk(t, filepath.Join(cmds, "code.perf.md")) {
		t.Error("included command not installed")
	}
	if err := inst.SetExcludedWorkflows(target, []string{"../x"}); err == nil {
		t.Error("invalid name accepted")
	}
	g, _ := targets.FindTarget("copilot").Global()
	if err := inst.SetExcludedWorkflows(g, []string{"x"}); err == nil {
		t.Error("a target without workflows cannot exclude any")
	}
}

func TestRemoveModified(t *testing.T) {
	base := t.TempDir()
	skill := skills.FindSkill("make-decision")
	target := targets.FindTarget("claude")
	inst := NewInstaller(base, testVersion)
	if _, err := inst.Install(skill, target, Options{}); err != nil {
		t.Fatal(err)
	}
	dir := filepath.Join(base, ".claude", "skills", "make-decision")
	if err := os.WriteFile(filepath.Join(dir, "SKILL.md"), []byte("mine"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(base, ".claude", "commands", "decide.md"), []byte("mine"), 0o644); err != nil {
		t.Fatal(err)
	}
	res, err := inst.Uninstall(skill, target, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if res.DirRemoved {
		t.Fatal("modified SKILL.md should keep the directory")
	}
	listed, err := inst.RemoveModified(target, res, true)
	if err != nil || len(listed) != 2 || !onDisk(t, filepath.Join(dir, "SKILL.md")) {
		t.Fatalf("dry run: %v %v", listed, err)
	}
	removed, err := inst.RemoveModified(target, res, false)
	if err != nil {
		t.Fatal(err)
	}
	want := []string{".claude/skills/make-decision/SKILL.md", ".claude/commands/decide.md"}
	if !slices.Equal(removed, want) {
		t.Errorf("removed %v, want %v", removed, want)
	}
	if !res.DirRemoved || onDisk(t, filepath.Join(base, ".claude")) {
		t.Error("everything should be gone")
	}
}
