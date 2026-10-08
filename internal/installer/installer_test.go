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

const testVersion = "v1.0.0"

func TestCheckStatusNotInstalled(t *testing.T) {
	tmpDir := t.TempDir()
	skill := skills.FindSkill("make-decision")
	if skill == nil {
		t.Fatal("skill make-decision not found in registry")
	}
	target := targets.FindTarget("claude")

	status, err := CheckStatus(skill, target, tmpDir, testVersion)
	if err != nil {
		t.Fatalf("CheckStatus error: %v", err)
	}
	if status.Status != StatusNotInstalled {
		t.Errorf("Status = %q, want %q", status.Status, StatusNotInstalled)
	}
	if status.SkillName != "make-decision" || status.TargetName != "claude" {
		t.Errorf("status = %+v", status)
	}
}

func TestCheckStatusIncomplete(t *testing.T) {
	tmpDir := t.TempDir()
	skill := skills.FindSkill("make-decision")
	target := targets.FindTarget("claude")

	// Create partial installation — just PROMPT.md
	installDir := filepath.Join(tmpDir, target.InstallDir(skill.Name))
	if err := os.MkdirAll(installDir, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(installDir, "PROMPT.md"), []byte("test"), 0o644); err != nil {
		t.Fatal(err)
	}

	status, err := CheckStatus(skill, target, tmpDir, testVersion)
	if err != nil {
		t.Fatalf("CheckStatus error: %v", err)
	}
	if status.Status != StatusIncomplete {
		t.Errorf("Status = %q, want %q", status.Status, StatusIncomplete)
	}
	if len(status.Missing) == 0 {
		t.Error("Missing should be non-empty for incomplete install")
	}
	if len(status.Modified) != 1 || !strings.HasSuffix(status.Modified[0], "/PROMPT.md") {
		t.Errorf("Modified = %v, want PROMPT.md", status.Modified)
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
			inst := NewInstaller(tmpDir, testVersion)
			for i := range skills.Registry {
				skill := &skills.Registry[i]
				if _, err := inst.Install(skill, &target, Options{}); err != nil {
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
			res, err := NewInstaller(tmpDir, testVersion).Install(skill, &target, Options{})
			if err != nil {
				t.Fatal(err)
			}
			if len(res.Workflows) == 0 {
				t.Fatal("no workflows installed")
			}
			for _, c := range res.Workflows {
				name := c.Path
				if c.Action != ActionCreate {
					t.Errorf("%s: action %s, want create", name, c.Action)
				}
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
	inst := NewInstaller(tmpDir, testVersion)
	for _, name := range []string{"code-solving", "make-decision"} {
		if _, err := inst.Install(skills.FindSkill(name), target, Options{}); err != nil {
			t.Fatal(err)
		}
	}

	res, err := inst.Uninstall(skills.FindSkill("code-solving"), target, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if res.Count(ActionRemove) == 0 || len(res.Workflows) == 0 {
		t.Fatal("nothing removed")
	}
	dir := filepath.Join(tmpDir, ".claude", "commands")
	if _, err := os.Stat(filepath.Join(dir, "code.md")); !os.IsNotExist(err) {
		t.Error("code.md should be removed")
	}
	if _, err := os.Stat(filepath.Join(dir, "decide.md")); err != nil {
		t.Error("decide.md belongs to make-decision and should stay")
	}
	m, err := readWorkflowManifest(tmpDir, ".claude/commands")
	if err != nil || m == nil {
		t.Fatalf("workflow manifest: %v %v", m, err)
	}
	for name, e := range m.Files {
		if e.Skill != "make-decision" {
			t.Errorf("manifest still lists %s (%s)", name, e.Skill)
		}
	}
}

// A --global install writes under the home directory, and every "~/..." script
// path in the installed docs and commands resolves there.
func TestGlobalInstallPaths(t *testing.T) {
	pathRe := regexp.MustCompile(`~/[\w./-]+/scripts/search\.py`)
	for _, project := range targets.Targets {
		target, err := project.Global()
		if err != nil {
			continue
		}
		t.Run(target.Name, func(t *testing.T) {
			home := t.TempDir()
			inst := NewInstaller(home, testVersion)
			for i := range skills.Registry {
				if _, err := inst.Install(&skills.Registry[i], target, Options{}); err != nil {
					t.Fatal(err)
				}
			}
			checked := 0
			err := filepath.WalkDir(home, func(p string, d os.DirEntry, err error) error {
				if err != nil || d.IsDir() || !strings.HasSuffix(p, ".md") {
					return err
				}
				data, err := os.ReadFile(p)
				if err != nil {
					return err
				}
				if strings.Contains(string(data), ".agents/skills/") && target.Name != "antigravity" {
					t.Errorf("%s still references .agents/skills/", p)
				}
				for _, ref := range pathRe.FindAllString(string(data), -1) {
					checked++
					if _, err := os.Stat(filepath.Join(home, filepath.FromSlash(strings.TrimPrefix(ref, "~/")))); err != nil {
						t.Errorf("%s references %s, which does not exist under home", p, ref)
					}
				}
				return nil
			})
			if err != nil {
				t.Fatal(err)
			}
			if checked == 0 {
				t.Error("no ~/ script paths found in installed files")
			}
		})
	}
}
