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

	if _, err := installer.NewInstaller(project, Version()).Install(skill, targets.FindTarget("copilot"), installer.Options{}); err != nil {
		t.Fatal(err)
	}
	global, err := targets.FindTarget("opencode").Global()
	if err != nil {
		t.Fatal(err)
	}
	if _, err := installer.NewInstaller(home, Version()).Install(skill, global, installer.Options{}); err != nil {
		t.Fatal(err)
	}

	got := findSkillLocations(skill, project, home)
	if len(got) != 2 || got[0].Label != "copilot" || got[1].Label != "opencode (global)" {
		t.Fatalf("locations = %+v, want copilot and opencode (global)", got)
	}
	if got[1].Path != "~/.config/opencode/skills/code-solving/" || !got[1].Global() || got[0].Global() {
		t.Errorf("global location = %+v", got[1])
	}
	if got[0].Status.Status != installer.StatusInstalled {
		t.Errorf("status = %s", got[0].Status.Status)
	}
}

// Run from the home directory, a claude install is found once, as global.
func TestFindSkillLocationsInHome(t *testing.T) {
	home := t.TempDir()
	skill := skills.FindSkill("make-decision")
	global, _ := targets.FindTarget("claude").Global()
	if _, err := installer.NewInstaller(home, Version()).Install(skill, global, installer.Options{}); err != nil {
		t.Fatal(err)
	}
	got := findSkillLocations(skill, home, home)
	if len(got) != 1 || got[0].Label != "claude (global)" {
		t.Fatalf("locations = %+v, want only claude (global)", got)
	}
}
