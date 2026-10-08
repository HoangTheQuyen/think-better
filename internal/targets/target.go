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
	WorkflowFormat  string // How workflows are written: "" (Markdown as is) or FormatCopilotPrompt

	// User-level ("--global") locations, relative to the home directory.
	// Empty GlobalInstallPattern means --global is not supported.
	GlobalInstallPattern  string
	GlobalWorkflowPattern string

	global bool // set on the copy returned by Global()
}

// FormatCopilotPrompt writes workflows as VS Code Copilot prompt files
// (<name>.prompt.md, run in agent mode, ${input:task} for the user's text).
const FormatCopilotPrompt = "copilot-prompt"

// sourceSkillsRoot is where workflows reference skills in the .agents/ sources.
const sourceSkillsRoot = ".agents/skills/"

// Targets contains all supported AI assistant targets.
var Targets = []AITarget{
	{
		Name:            "claude",
		DisplayName:     "Claude",
		InstallPattern:  ".claude/skills/{skill}/",
		WorkflowPattern: ".claude/commands/",
		// https://code.claude.com/docs/en/skills (personal skills)
		GlobalInstallPattern:  ".claude/skills/{skill}/",
		GlobalWorkflowPattern: ".claude/commands/",
	},
	{
		Name:            "copilot",
		DisplayName:     "GitHub Copilot",
		InstallPattern:  ".github/prompts/{skill}/",
		WorkflowPattern: ".github/prompts/",
		WorkflowFormat:  FormatCopilotPrompt,
	},
	{
		Name:            "antigravity",
		DisplayName:     "Antigravity (Gemini Antigravity)",
		InstallPattern:  ".agents/skills/{skill}/",
		WorkflowPattern: ".agents/workflows/",
		// Global scope per Google's Antigravity skills codelab and workflow migration guide
		GlobalInstallPattern:  ".gemini/config/skills/{skill}/",
		GlobalWorkflowPattern: ".gemini/config/workflows/",
	},
	{
		Name:            "opencode",
		DisplayName:     "OpenCode",
		InstallPattern:  ".opencode/skills/{skill}/",
		WorkflowPattern: ".opencode/commands/",
		// https://opencode.ai/docs/skills and https://opencode.ai/docs/commands
		GlobalInstallPattern:  ".config/opencode/skills/{skill}/",
		GlobalWorkflowPattern: ".config/opencode/commands/",
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

// SupportsGlobal reports whether skills can be installed for the whole user account.
func (t *AITarget) SupportsGlobal() bool {
	return t.GlobalInstallPattern != ""
}

// Global returns the user-level variant of this target: the same target with
// paths relative to the home directory instead of the project.
func (t *AITarget) Global() (*AITarget, error) {
	if !t.SupportsGlobal() {
		return nil, fmt.Errorf("--global is not supported for %s yet; install into the project instead", t.Name)
	}
	g := *t
	g.InstallPattern = t.GlobalInstallPattern
	g.WorkflowPattern = t.GlobalWorkflowPattern
	g.global = true
	return &g, nil
}

// IsGlobal reports whether this is the user-level variant from Global().
func (t *AITarget) IsGlobal() bool {
	return t.global
}

// Display formats a path relative to the install base for messages
// ("~/.claude/skills/x/" for global installs).
func (t *AITarget) Display(rel string) string {
	if t.global {
		return "~/" + rel
	}
	return rel
}

// RewriteSkillPaths points ".agents/skills/" paths, as written in the skill
// sources, at this target's skills root. Project installs use paths relative
// to the project root; global installs use "~/..." so they work from any project.
func (t *AITarget) RewriteSkillPaths(content string) string {
	return strings.ReplaceAll(content, sourceSkillsRoot, t.Display(t.SkillsRoot()))
}

// WorkflowFileName is the installed file name for a workflow source file
// (e.g. "code.debug.md" becomes "code.debug.prompt.md" for Copilot).
func (t *AITarget) WorkflowFileName(name string) string {
	if t.WorkflowFormat == FormatCopilotPrompt {
		return strings.TrimSuffix(name, ".md") + ".prompt.md"
	}
	return name
}

// AdaptWorkflow rewrites a workflow written for the .agents/ layout so it
// works for this target: skill paths point at the target's skills root, and
// Antigravity-only "// turbo" annotations are dropped elsewhere. Copilot
// prompt files also run in agent mode and take the user's text as ${input:task}.
func (t *AITarget) AdaptWorkflow(content string) string {
	content = t.RewriteSkillPaths(content)
	if t.Name == "antigravity" {
		return content
	}
	lines := strings.Split(content, "\n")
	kept := lines[:0]
	for _, l := range lines {
		if strings.TrimSpace(l) != "// turbo" {
			kept = append(kept, l)
		}
	}
	content = strings.Join(kept, "\n")

	if t.WorkflowFormat == FormatCopilotPrompt {
		content = strings.ReplaceAll(content, "$ARGUMENTS", "${input:task}")
		if rest, ok := strings.CutPrefix(content, "---\n"); ok {
			content = "---\nagent: agent\nargument-hint: Describe the task\n" + rest
		}
	}
	return content
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
