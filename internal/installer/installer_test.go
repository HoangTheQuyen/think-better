package installer

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/htrbao/think-better/internal/skills"
	"github.com/htrbao/think-better/internal/targets"
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
	installDir := filepath.Join(tmpDir, ".github", "prompts", "make-decision")
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
