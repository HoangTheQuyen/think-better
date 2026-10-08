package cli

import (
	"testing"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

func TestFindSkillLocations(t *testing.T) {
	project, home := t.TempDir(), t.TempDir()
	skill := skills.FindSkill("code-solving")

	if got := findSkillLocations(skill, project, home); len(got) != 0 {
		t.Fatalf("nothing installed, got %v", got)
	}

	if _, err := installer.NewInstaller(project).Install(skill, targets.FindTarget("copilot"), true, false); err != nil {
		t.Fatal(err)
	}
	global, err := targets.FindTarget("opencode").Global()
	if err != nil {
		t.Fatal(err)
	}
	if _, err := installer.NewInstaller(home).Install(skill, global, true, false); err != nil {
		t.Fatal(err)
	}

	got := findSkillLocations(skill, project, home)
	if len(got) != 2 || got[0].Label != "copilot" || got[1].Label != "opencode (global)" {
		t.Fatalf("locations = %+v, want copilot and opencode (global)", got)
	}
	if got[1].Path != "~/.config/opencode/skills/code-solving/" {
		t.Errorf("global path = %q", got[1].Path)
	}
}
