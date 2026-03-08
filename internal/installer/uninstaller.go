package installer

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/htrbao/think-better/internal/skills"
	"github.com/htrbao/think-better/internal/targets"
)

// Uninstaller handles skill file removal.
type Uninstaller struct {
	BaseDir string
}

// NewUninstaller creates an Uninstaller rooted at the given base directory.
func NewUninstaller(baseDir string) *Uninstaller {
	return &Uninstaller{BaseDir: baseDir}
}

// Uninstall removes all installed skill files and empty parent directories.
// Returns the list of removed files.
func (u *Uninstaller) Uninstall(skill *skills.SkillPackage, target *targets.AITarget, force bool, interactive bool) ([]string, error) {
	installDir := filepath.Join(u.BaseDir, filepath.FromSlash(target.InstallDir(skill.Name)))

	// Check status first
	status, err := CheckStatus(skill, target, u.BaseDir)
	if err != nil {
		return nil, err
	}

	if status.Status == StatusNotInstalled {
		return nil, fmt.Errorf("skill %q is not installed", skill.Name)
	}

	// Confirm before removal
	if !force {
		if interactive {
			fmt.Fprintf(os.Stderr, "Remove skill %q from %s? (%d files)\n",
				skill.Name, target.InstallDir(skill.Name), len(status.InstalledFiles))
			fmt.Fprintf(os.Stderr, "Remove? [y/N]: ")
			buf := make([]byte, 64)
			n, readErr := os.Stdin.Read(buf)
			if readErr != nil || n == 0 {
				return nil, nil
			}
			answer := string(buf[:n])
			if len(answer) == 0 || (answer[0] != 'y' && answer[0] != 'Y') {
				return nil, nil
			}
		} else {
			return nil, fmt.Errorf("use --force to remove without confirmation")
		}
	}

	// Remove installed files
	var removed []string
	for _, f := range status.InstalledFiles {
		fullPath := filepath.Join(installDir, filepath.FromSlash(f))
		if err := os.Remove(fullPath); err != nil && !os.IsNotExist(err) {
			return removed, fmt.Errorf("removing %s: %w", f, err)
		}
		removed = append(removed, f)
	}

	// Clean up empty directories (bottom-up from deepest subdirectories)
	// Stop at the target's parent install directory — don't remove it
	installPatternSlash := target.InstallDir(skill.Name)
	// Extract the root directory from the install pattern (e.g., ".github/prompts" or ".antigravity/skills")
	stopDir := filepath.Join(u.BaseDir, filepath.Dir(filepath.FromSlash(installPatternSlash)))
	cleanEmptyDirsRecursive(installDir, stopDir)

	return removed, nil
}

// cleanEmptyDirsRecursive walks the install directory tree and removes empty
// directories from the bottom up, then cleans parent dirs up to stopAt.
func cleanEmptyDirsRecursive(dir string, stopAt string) {
	absStop, _ := filepath.Abs(stopAt)

	// First, collect all subdirectories and try to remove them bottom-up
	var dirs []string
	filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() {
			dirs = append(dirs, path)
		}
		return nil
	})

	// Remove in reverse order (deepest first)
	for i := len(dirs) - 1; i >= 0; i-- {
		entries, err := os.ReadDir(dirs[i])
		if err == nil && len(entries) == 0 {
			os.Remove(dirs[i])
		}
	}

	// Walk up from installDir's parent to stopAt, removing empty dirs
	current := filepath.Dir(dir)
	for {
		absCurrent, _ := filepath.Abs(current)
		if absCurrent == absStop || len(absCurrent) <= len(absStop) {
			break
		}
		entries, err := os.ReadDir(current)
		if err != nil || len(entries) > 0 {
			break
		}
		os.Remove(current)
		current = filepath.Dir(current)
	}
}
