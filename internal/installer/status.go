// Package installer provides skill installation, uninstallation, and status checking.
package installer

import (
	"os"
	"path/filepath"

	"github.com/htrbao/think-better/internal/skills"
	"github.com/htrbao/think-better/internal/targets"
)

// Status represents the installation state of a skill.
type Status string

const (
	StatusInstalled    Status = "installed"
	StatusIncomplete   Status = "incomplete"
	StatusNotInstalled Status = "not-installed"
)

// InstallStatus represents the current state of a skill installation.
type InstallStatus struct {
	SkillName      string
	TargetName     string
	InstallPath    string // Resolved absolute path
	Status         Status
	InstalledFiles []string // Files that exist on disk
	MissingFiles   []string // Expected files not found on disk
}

// CheckStatus computes the installation status of a skill for a given target
// relative to baseDir (typically the current working directory).
func CheckStatus(skill *skills.SkillPackage, target *targets.AITarget, baseDir string) (*InstallStatus, error) {
	installDir := filepath.Join(baseDir, filepath.FromSlash(target.InstallDir(skill.Name)))

	absPath, err := filepath.Abs(installDir)
	if err != nil {
		absPath = installDir
	}

	// Get expected files from embedded FS
	expectedFiles, err := skills.SkillFiles(skill.Name)
	if err != nil {
		return nil, err
	}

	var installed, missing []string
	for _, f := range expectedFiles {
		fullPath := filepath.Join(installDir, filepath.FromSlash(f))
		if _, err := os.Stat(fullPath); err == nil {
			installed = append(installed, f)
		} else {
			missing = append(missing, f)
		}
	}

	var status Status
	switch {
	case len(installed) == 0:
		status = StatusNotInstalled
	case len(missing) == 0:
		status = StatusInstalled
	default:
		status = StatusIncomplete
	}

	return &InstallStatus{
		SkillName:      skill.Name,
		TargetName:     target.Name,
		InstallPath:    absPath,
		Status:         status,
		InstalledFiles: installed,
		MissingFiles:   missing,
	}, nil
}
