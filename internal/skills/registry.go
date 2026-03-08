// Package skills provides the skill registry and embedded file access.
package skills

import "strings"

// SkillPackage represents a self-contained collection of files that form an AI assistant skill.
type SkillPackage struct {
	Name                  string   // Unique identifier (e.g., "make-decision")
	Description           string   // Short human-readable summary shown in list output
	EntryPoint            string   // Relative path to the skill's main file (always "PROMPT.md")
	AntigravityEntryPoint string   // Relative path to the Antigravity entry point ("SKILL.md")
	Dependencies          []string // Runtime requirements (e.g., ["python3"])
}

// Registry contains all bundled skills. Files are discovered from embed.FS at runtime.
var Registry = []SkillPackage{
	{
		Name:                  "make-decision",
		Description:           "AI-powered decision-making framework: 10+ methodologies, cognitive bias detection, strategic planning, career & business decisions",
		EntryPoint:            "PROMPT.md",
		AntigravityEntryPoint: "SKILL.md",
		Dependencies:          []string{"python3"},
	},
	{
		Name:                  "problem-solving-pro",
		Description:           "Systematic problem-solving toolkit: root cause analysis, hypothesis testing, debugging strategies, critical thinking frameworks",
		EntryPoint:            "PROMPT.md",
		AntigravityEntryPoint: "SKILL.md",
		Dependencies:          []string{"python3"},
	},
}

// FindSkill returns the skill with the given name (case-insensitive), or nil if not found.
func FindSkill(name string) *SkillPackage {
	lower := strings.ToLower(name)
	for i := range Registry {
		if Registry[i].Name == lower {
			return &Registry[i]
		}
	}
	return nil
}

// SkillNames returns the names of all registered skills.
func SkillNames() []string {
	names := make([]string, len(Registry))
	for i, s := range Registry {
		names[i] = s.Name
	}
	return names
}
