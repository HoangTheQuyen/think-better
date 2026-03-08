package installer

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"

	"github.com/htrbao/think-better/internal/skills"
	"github.com/htrbao/think-better/internal/targets"
)

// Installer handles skill file installation.
type Installer struct {
	BaseDir string // Working directory (usually cwd)
}

// NewInstaller creates an Installer rooted at the given base directory.
func NewInstaller(baseDir string) *Installer {
	return &Installer{BaseDir: baseDir}
}

// Install copies embedded skill files to the target directory.
// Returns the list of created files.
func (inst *Installer) Install(skill *skills.SkillPackage, target *targets.AITarget, force bool, interactive bool) ([]string, error) {
	installDir := filepath.Join(inst.BaseDir, filepath.FromSlash(target.InstallDir(skill.Name)))

	// Check existing installation status
	status, err := CheckStatus(skill, target, inst.BaseDir)
	if err != nil {
		return nil, fmt.Errorf("checking status: %w", err)
	}

	// Handle conflict detection
	if status.Status == StatusInstalled || status.Status == StatusIncomplete {
		if !force {
			// Show what would change
			files, _ := skills.SkillFiles(skill.Name)
			if len(files) > 0 {
				fmt.Fprintf(os.Stderr, "Skill %q is already %s at %s\n", skill.Name, status.Status, target.InstallDir(skill.Name))
				fmt.Fprintf(os.Stderr, "Files that would be overwritten:\n")
				for _, f := range status.InstalledFiles {
					fmt.Fprintf(os.Stderr, "  %s\n", f)
				}
				if len(status.MissingFiles) > 0 {
					fmt.Fprintf(os.Stderr, "Files that would be added:\n")
					for _, f := range status.MissingFiles {
						fmt.Fprintf(os.Stderr, "  %s\n", f)
					}
				}
			}

			if interactive {
				if confirmed := confirmOverwrite(skill.Name); !confirmed {
					return nil, nil // User declined
				}
			} else {
				return nil, fmt.Errorf("skill %q already installed. Use --force to overwrite", skill.Name)
			}
		}
	}

	// Get the skill's embedded filesystem
	sub, err := skills.SkillFS(skill.Name)
	if err != nil {
		return nil, fmt.Errorf("accessing embedded skill %q: %w", skill.Name, err)
	}

	var created []string
	err = fs.WalkDir(sub, ".", func(path string, d fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}

		targetPath := filepath.Join(installDir, filepath.FromSlash(path))

		if d.IsDir() {
			return os.MkdirAll(targetPath, 0o755)
		}

		// Read embedded file
		data, err := fs.ReadFile(sub, path)
		if err != nil {
			return fmt.Errorf("reading embedded %s: %w", path, err)
		}

		// Create parent directory
		if err := os.MkdirAll(filepath.Dir(targetPath), 0o755); err != nil {
			return fmt.Errorf("creating directory for %s: %w", path, err)
		}

		// Write file with appropriate permissions
		mode := fileMode(path)
		if err := os.WriteFile(targetPath, data, mode); err != nil {
			return fmt.Errorf("writing %s: %w", path, err)
		}

		created = append(created, path)
		return nil
	})

	if err != nil {
		return created, fmt.Errorf("installing skill %q: %w", skill.Name, err)
	}

	return created, nil
}

// fileMode returns the appropriate file permission based on extension.
// .py files get 0o755 (executable), everything else gets 0o644.
func fileMode(path string) os.FileMode {
	if strings.HasSuffix(path, ".py") {
		return 0o755
	}
	return 0o644
}

// confirmOverwrite prompts the user to confirm overwriting.
func confirmOverwrite(skillName string) bool {
	fmt.Fprintf(os.Stderr, "Overwrite? [y/N]: ")

	buf := make([]byte, 64)
	n, err := os.Stdin.Read(buf)
	if err != nil || n == 0 {
		return false
	}
	answer := strings.TrimSpace(strings.ToLower(string(buf[:n])))
	return answer == "y" || answer == "yes"
}
