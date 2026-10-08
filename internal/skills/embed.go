package skills

import (
	"embed"
	"fmt"
	"io/fs"
	"strings"
)

//go:generate go run ./gen -src ../../.agents -dst .

// Content holds all embedded skill files.
// The skills/ directory is mirrored from .agents/skills by `go generate ./internal/skills`.
//
//go:embed all:skills
var Content embed.FS

// Workflows holds all embedded workflow files.
// The workflows/ directory is mirrored from .agents/workflows by `go generate ./internal/skills`.
//
//go:embed all:workflows
var Workflows embed.FS

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

// WorkflowFS returns the filesystem rooted at the workflows directory.
func WorkflowFS() (fs.FS, error) {
	return fs.Sub(Workflows, "workflows")
}

// WorkflowFiles returns all file paths (relative) within the embedded workflows.
func WorkflowFiles() ([]string, error) {
	sub, err := WorkflowFS()
	if err != nil {
		return nil, fmt.Errorf("workflows not found in embedded files: %w", err)
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
		return nil, fmt.Errorf("walking workflows: %w", err)
	}
	return files, nil
}

// WorkflowSkill returns the skill a workflow runs, taken from the first
// ".agents/skills/<name>/" path it references ("" if none).
func WorkflowSkill(file string) string {
	sub, err := WorkflowFS()
	if err != nil {
		return ""
	}
	data, err := fs.ReadFile(sub, file)
	if err != nil {
		return ""
	}
	_, rest, ok := strings.Cut(string(data), ".agents/skills/")
	if !ok {
		return ""
	}
	name, _, _ := strings.Cut(rest, "/")
	return name
}

// ValidateEmbedded checks that all registry skills have at least one file
// in the embedded filesystem. Call during init to fail fast if build missed files.
func ValidateEmbedded() error {
	if len(discoveryErrors) > 0 {
		return fmt.Errorf("invalid embedded skills:\n  %s", strings.Join(discoveryErrors, "\n  "))
	}
	if len(Registry) == 0 {
		return fmt.Errorf("no embedded skills found (run 'go generate ./internal/skills' before building)")
	}
	var missing []string
	for _, skill := range Registry {
		files, err := SkillFiles(skill.Name)
		if err != nil || len(files) == 0 {
			missing = append(missing, skill.Name)
		}
	}
	if len(missing) > 0 {
		return fmt.Errorf("embedded skills missing files: %s (run 'go generate ./internal/skills' before building)", strings.Join(missing, ", "))
	}
	return nil
}
