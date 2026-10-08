package cli

import (
	"os"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// skillLocation is one place a skill is (at least partly) installed.
type skillLocation struct {
	Label  string // "claude", "opencode (global)", ...
	Path   string // install path as shown to the user
	Status installer.Status
}

// findSkillLocations looks for a skill in every target, in the project
// (projectDir) and in the user's home directory (homeDir, "" to skip).
func findSkillLocations(skill *skills.SkillPackage, projectDir, homeDir string) []skillLocation {
	var found []skillLocation
	for i := range targets.Targets {
		t := &targets.Targets[i]
		scopes := []struct {
			target *targets.AITarget
			base   string
			label  string
		}{{t, projectDir, t.Name}}
		if g, err := t.Global(); err == nil && homeDir != "" {
			scopes = append(scopes, struct {
				target *targets.AITarget
				base   string
				label  string
			}{g, homeDir, t.Name + " (global)"})
		}
		for _, s := range scopes {
			status, err := installer.CheckStatus(skill, s.target, s.base)
			if err != nil || status.Status == installer.StatusNotInstalled {
				continue
			}
			found = append(found, skillLocation{
				Label:  s.label,
				Path:   s.target.Display(s.target.InstallDir(skill.Name)),
				Status: status.Status,
			})
		}
	}
	return found
}

// userHome returns the home directory, or "" if it cannot be determined.
func userHome() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	return home
}
