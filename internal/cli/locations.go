package cli

import (
	"os"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// skillLocation is one place a skill is (at least partly) installed.
type skillLocation struct {
	Label  string            // "claude", "opencode (global)", ...
	Target *targets.AITarget // the target, or its Global() variant
	Base   string            // directory the target's paths are relative to
	Path   string            // install path as shown to the user
	Status *installer.InstallStatus
}

// Global reports whether this is a user-level (--global) install.
func (l skillLocation) Global() bool { return l.Target.IsGlobal() }

// findSkillLocations looks for a skill in every target, in the project
// (projectDir) and in the user's home directory (homeDir, "" to skip).
func findSkillLocations(skill *skills.SkillPackage, projectDir, homeDir string) []skillLocation {
	sameDir := homeDir != "" && isSameDir(projectDir, homeDir)
	var found []skillLocation
	for i := range targets.Targets {
		t := &targets.Targets[i]
		type scope struct {
			target *targets.AITarget
			base   string
			label  string
		}
		var scopes []scope
		// Run from the home directory, a project install of a target whose
		// project and user paths coincide is the global install.
		if !sameDir || t.InstallPattern != t.GlobalInstallPattern {
			scopes = append(scopes, scope{t, projectDir, t.Name})
		}
		if g, err := t.Global(); err == nil && homeDir != "" {
			scopes = append(scopes, scope{g, homeDir, t.Name + " (global)"})
		}
		for _, s := range scopes {
			status, err := installer.CheckStatus(skill, s.target, s.base, Version())
			if err != nil || status.Status == installer.StatusNotInstalled {
				continue
			}
			found = append(found, skillLocation{
				Label:  s.label,
				Target: s.target,
				Base:   s.base,
				Path:   s.target.Display(s.target.InstallDir(skill.Name)),
				Status: status,
			})
		}
	}
	return found
}

// isSameDir reports whether two paths name the same directory.
func isSameDir(a, b string) bool {
	fa, err := os.Stat(a)
	if err != nil {
		return false
	}
	fb, err := os.Stat(b)
	if err != nil {
		return false
	}
	return os.SameFile(fa, fb)
}

// userHome returns the home directory, or "" if it cannot be determined.
func userHome() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	return home
}

// statusLabel describes a location's state for tables and messages, e.g.
// "outdated, 2 modified".
func statusLabel(st *installer.InstallStatus) string {
	switch st.Status {
	case installer.StatusIncomplete:
		return "incomplete"
	case installer.StatusOutdated:
		if n := len(st.Modified); n > 0 {
			return "outdated, " + plural(n, "modified file", "modified files")
		}
		return "outdated"
	case installer.StatusModified:
		return plural(len(st.Modified), "modified file", "modified files")
	}
	return string(st.Status)
}
