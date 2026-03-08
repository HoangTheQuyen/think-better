// Package targets provides the AI assistant target registry.
package targets

import (
	"fmt"
	"strings"
)

// AITarget represents a supported AI assistant platform.
type AITarget struct {
	Name           string // Canonical identifier (e.g., "claude", "copilot")
	DisplayName    string // Human-friendly name
	InstallPattern string // Path template with {skill} placeholder
}

// Targets contains all supported AI assistant targets.
var Targets = []AITarget{
	{
		Name:           "claude",
		DisplayName:    "Claude",
		InstallPattern: ".claude/skills/{skill}/",
	},
	{
		Name:           "copilot",
		DisplayName:    "GitHub Copilot",
		InstallPattern: ".github/prompts/{skill}/",
	},
	{
		Name:           "antigravity",
		DisplayName:    "Antigravity (Gemini Antigravity)",
		InstallPattern: ".agents/skills/{skill}/",
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
