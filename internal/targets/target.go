// Package targets provides the AI assistant target registry.
package targets

import (
	"fmt"
	"strings"
)

// AITarget represents a supported AI assistant platform.
type AITarget struct {
	Name            string // Canonical identifier (e.g., "claude", "copilot")
	DisplayName     string // Human-friendly name
	InstallPattern  string // Path template with {skill} placeholder
	WorkflowPattern string // Directory for workflow (slash command) files (empty = no workflow support)
}

// sourceSkillsRoot is where workflows reference skills in the .agents/ sources.
const sourceSkillsRoot = ".agents/skills/"

// Targets contains all supported AI assistant targets.
var Targets = []AITarget{
	{
		Name:            "claude",
		DisplayName:     "Claude",
		InstallPattern:  ".claude/skills/{skill}/",
		WorkflowPattern: ".claude/commands/",
	},
	{
		Name:            "copilot",
		DisplayName:     "GitHub Copilot",
		InstallPattern:  ".github/prompts/{skill}/",
		WorkflowPattern: "",
	},
	{
		Name:            "antigravity",
		DisplayName:     "Antigravity (Gemini Antigravity)",
		InstallPattern:  ".agents/skills/{skill}/",
		WorkflowPattern: ".agents/workflows/",
	},
	{
		Name:            "opencode",
		DisplayName:     "OpenCode",
		InstallPattern:  ".opencode/skills/{skill}/",
		WorkflowPattern: "",
	},
}

// FindTarget returns the target with the given name (case-insensitive), or nil if not found.
func FindTarget(name string) *AITarget {
	lower := strings.ToLower(name)
	for i := range Targets {
		if Targets[i].Name == lower {
			return &Targets[i]
		}
	}
	return nil
}

// ValidTarget returns true if the name matches a registered target (case-insensitive).
func ValidTarget(name string) bool {
	return FindTarget(name) != nil
}

// TargetNames returns all valid target names.
func TargetNames() []string {
	names := make([]string, len(Targets))
	for i, t := range Targets {
		names[i] = t.Name
	}
	return names
}

// InstallDir resolves the install directory for a skill on this target.
func (t *AITarget) InstallDir(skillName string) string {
	return strings.ReplaceAll(t.InstallPattern, "{skill}", skillName)
}

// WorkflowDir returns the workflow directory for this target, or empty string if not supported.
func (t *AITarget) WorkflowDir() string {
	return t.WorkflowPattern
}

// SkillsRoot returns the directory that contains all skills for this target
// (e.g., ".claude/skills/").
func (t *AITarget) SkillsRoot() string {
	return strings.TrimSuffix(t.InstallPattern, "{skill}/")
}

// AdaptWorkflow rewrites a workflow written for the .agents/ layout so it
// works for this target: skill paths point at the target's skills root, and
// Antigravity-only "// turbo" annotations are dropped elsewhere.
func (t *AITarget) AdaptWorkflow(content string) string {
	if t.SkillsRoot() == sourceSkillsRoot {
		return content
	}
	content = strings.ReplaceAll(content, sourceSkillsRoot, t.SkillsRoot())
	lines := strings.Split(content, "\n")
	kept := lines[:0]
	for _, l := range lines {
		if strings.TrimSpace(l) != "// turbo" {
			kept = append(kept, l)
		}
	}
	return strings.Join(kept, "\n")
}

// HasWorkflows returns true if this target supports workflow installation.
func (t *AITarget) HasWorkflows() bool {
	return t.WorkflowPattern != ""
}

// ValidateTarget checks a target name and returns a clear error if invalid.
func ValidateTarget(name string) error {
	if name == "" {
		return fmt.Errorf("--ai is required")
	}
	if !ValidTarget(name) {
		return fmt.Errorf("invalid --ai value %q: must be %s", name, strings.Join(TargetNames(), " or "))
	}
	return nil
}
