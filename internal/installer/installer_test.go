package installer

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"

	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

func TestCheckStatusNotInstalled(t *testing.T) {
	tmpDir := t.TempDir()
	skill := skills.FindSkill("make-decision")
	if skill == nil {
		t.Fatal("skill make-decision not found in registry")
	}
	target := targets.FindTarget("claude")
	if target == nil {
		t.Fatal("target claude not found")
	}

	status, err := CheckStatus(skill, target, tmpDir)
	if err != nil {
		t.Fatalf("CheckStatus error: %v", err)
	}
	if status.Status != StatusNotInstalled {
		t.Errorf("Status = %q, want %q", status.Status, StatusNotInstalled)
	}
	if status.SkillName != "make-decision" {
		t.Errorf("SkillName = %q, want %q", status.SkillName, "make-decision")
	}
	if status.TargetName != "claude" {
		t.Errorf("TargetName = %q, want %q", status.TargetName, "claude")
	}
	if len(status.InstalledFiles) != 0 {
		t.Errorf("InstalledFiles = %d, want 0", len(status.InstalledFiles))
	}
}

func TestCheckStatusIncomplete(t *testing.T) {
	tmpDir := t.TempDir()
	skill := skills.FindSkill("make-decision")
	if skill == nil {
		t.Fatal("skill make-decision not found in registry")
	}
	target := targets.FindTarget("claude")
	if target == nil {
		t.Fatal("target claude not found")
	}

	// Create partial installation — just PROMPT.md
	installDir := filepath.Join(tmpDir, target.InstallDir(skill.Name))
	if err := os.MkdirAll(installDir, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(installDir, "PROMPT.md"), []byte("test"), 0o644); err != nil {
		t.Fatal(err)
	}

	status, err := CheckStatus(skill, target, tmpDir)
	if err != nil {
		t.Fatalf("CheckStatus error: %v", err)
	}
	if status.Status != StatusIncomplete {
		t.Errorf("Status = %q, want %q", status.Status, StatusIncomplete)
	}
	if len(status.InstalledFiles) == 0 {
		t.Error("InstalledFiles should contain at least PROMPT.md")
	}
	if len(status.MissingFiles) == 0 {
		t.Error("MissingFiles should be non-empty for incomplete install")
	}
}

func TestFileMode(t *testing.T) {
	if got := fileMode("scripts/search.py"); got != 0o755 {
		t.Errorf("fileMode(.py) = %o, want 755", got)
	}
	if got := fileMode("PROMPT.md"); got != 0o644 {
		t.Errorf("fileMode(.md) = %o, want 644", got)
	}
	if got := fileMode("data/biases.csv"); got != 0o644 {
		t.Errorf("fileMode(.csv) = %o, want 644", got)
	}
}

// Every script path a skill doc tells the AI to run must exist after install,
// for every target (docs are written against .agents/skills/ and rewritten).
func TestInstallRewritesSkillDocPaths(t *testing.T) {
	pathRe := regexp.MustCompile(`[\w./-]+/scripts/search\.py`)
	for _, target := range targets.Targets {
		t.Run(target.Name, func(t *testing.T) {
			tmpDir := t.TempDir()
			inst := NewInstaller(tmpDir)
			for i := range skills.Registry {
				skill := &skills.Registry[i]
				if _, err := inst.Install(skill, &target, true, false); err != nil {
					t.Fatalf("Install(%s): %v", skill.Name, err)
				}
				for _, doc := range []string{"SKILL.md", "PROMPT.md"} {
					data, err := os.ReadFile(filepath.Join(tmpDir, filepath.FromSlash(target.InstallDir(skill.Name)), doc))
					if err != nil {
						t.Fatal(err)
					}
					refs := pathRe.FindAllString(string(data), -1)
					if len(refs) == 0 {
						t.Errorf("%s/%s: no script paths found", skill.Name, doc)
					}
					for _, ref := range refs {
						if _, err := os.Stat(filepath.Join(tmpDir, filepath.FromSlash(ref))); err != nil {
							t.Errorf("%s/%s references %s, which was not installed", skill.Name, doc, ref)
						}
					}
				}
			}
		})
	}
}

// Workflows are installed only for the chosen skills, in each target's format,
// and every script path they run exists after install.
func TestInstallWorkflowsPerTarget(t *testing.T) {
	pathRe := regexp.MustCompile(`[\w./-]+/scripts/search\.py`)
	skill := skills.FindSkill("code-solving")
	for _, target := range targets.Targets {
		if !target.HasWorkflows() {
			continue
		}
		t.Run(target.Name, func(t *testing.T) {
			tmpDir := t.TempDir()
			inst := NewInstaller(tmpDir)
			if _, err := inst.Install(skill, &target, true, false); err != nil {
				t.Fatal(err)
			}
			created, err := inst.InstallWorkflows(&target, true, skill.Name)
			if err != nil {
				t.Fatal(err)
			}
			if len(created) == 0 {
				t.Fatal("no workflows installed")
			}
			for _, name := range created {
				if !strings.HasPrefix(name, "code") {
					t.Errorf("installed %s, which does not run %s", name, skill.Name)
				}
				if target.WorkflowFormat == targets.FormatCopilotPrompt && !strings.HasSuffix(name, ".prompt.md") {
					t.Errorf("copilot workflow %s should end in .prompt.md", name)
				}
				data, err := os.ReadFile(filepath.Join(tmpDir, filepath.FromSlash(target.WorkflowDir()), name))
				if err != nil {
					t.Fatal(err)
				}
				content := string(data)
				if target.WorkflowFormat == targets.FormatCopilotPrompt &&
					(strings.Contains(content, "$ARGUMENTS") || !strings.Contains(content, "${input:task}")) {
					t.Errorf("%s: arguments not adapted for Copilot", name)
				}
				for _, ref := range pathRe.FindAllString(content, -1) {
					if _, err := os.Stat(filepath.Join(tmpDir, filepath.FromSlash(ref))); err != nil {
						t.Errorf("%s runs %s, which was not installed", name, ref)
					}
				}
			}
		})
	}
}

func TestUninstallRemovesOnlyThatSkillsWorkflows(t *testing.T) {
	tmpDir := t.TempDir()
	target := targets.FindTarget("claude")
	inst := NewInstaller(tmpDir)
	for _, name := range []string{"code-solving", "make-decision"} {
		if _, err := inst.Install(skills.FindSkill(name), target, true, false); err != nil {
			t.Fatal(err)
		}
	}
	if _, err := inst.InstallWorkflows(target, true); err != nil {
		t.Fatal(err)
	}

	removed, err := NewUninstaller(tmpDir).UninstallWorkflows(skills.FindSkill("code-solving"), target)
	if err != nil {
		t.Fatal(err)
	}
	if len(removed) == 0 {
		t.Fatal("no workflows removed")
	}
	dir := filepath.Join(tmpDir, ".claude", "commands")
	if _, err := os.Stat(filepath.Join(dir, "code.md")); !os.IsNotExist(err) {
		t.Error("code.md should be removed")
	}
	if _, err := os.Stat(filepath.Join(dir, "decide.md")); err != nil {
		t.Error("decide.md belongs to make-decision and should stay")
	}
}
