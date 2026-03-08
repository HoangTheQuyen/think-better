package skills

import (
	"embed"
	"fmt"
	"io/fs"
	"strings"
)

// Content holds all embedded skill files.
// The skills/ directory is populated by `make embed-prep` before building.
//
//go:embed all:skills
var Content embed.FS

// SkillFS returns the filesystem rooted at a specific skill's directory.
func SkillFS(skillName string) (fs.FS, error) {
	return fs.Sub(Content, "skills/"+skillName)
}

// SkillFiles returns all file paths (relative) within a skill.
func SkillFiles(skillName string) ([]string, error) {
	sub, err := SkillFS(skillName)
	if err != nil {
		return nil, fmt.Errorf("skill %q not found in embedded files: %w", skillName, err)
	}

	var files []string
	err = fs.WalkDir(sub, ".", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !d.IsDir() {
			files = append(files, path)
		}
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("walking skill %q: %w", skillName, err)
	}
	return files, nil
}

// ValidateEmbedded checks that all registry skills have at least one file
// in the embedded filesystem. Call during init to fail fast if build missed files.
func ValidateEmbedded() error {
	var missing []string
	for _, skill := range Registry {
		files, err := SkillFiles(skill.Name)
		if err != nil || len(files) == 0 {
			missing = append(missing, skill.Name)
		}
	}
	if len(missing) > 0 {
		return fmt.Errorf("embedded skills missing files: %s (run 'make embed-prep' before building)", strings.Join(missing, ", "))
	}
	return nil
}
