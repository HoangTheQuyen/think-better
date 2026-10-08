// Package cli provides subcommand handlers for the make-decision CLI.
package cli

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"strings"

	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// SharedFlags contains flags common to multiple subcommands.
type SharedFlags struct {
	AI     string
	Skill  string
	Force  bool
	Global bool
}

// AddSharedFlags registers the common flags on a FlagSet.
func AddSharedFlags(fs *flag.FlagSet, sf *SharedFlags) {
	fs.StringVar(&sf.AI, "ai", "", "AI target: "+strings.Join(targets.TargetNames(), ", "))
	fs.StringVar(&sf.Skill, "skill", "", "Skill name")
	fs.BoolVar(&sf.Force, "force", false, "Skip confirmation prompts")
	fs.BoolVar(&sf.Global, "global", false, "Use your user account (all projects) instead of the current project")
}

// ResolveScope returns the target and base directory to work in: the current
// project, or the home directory with the target's user-level paths for --global.
func ResolveScope(target *targets.AITarget, global bool) (*targets.AITarget, string, error) {
	if !global {
		cwd, err := os.Getwd()
		if err != nil {
			return nil, "", fmt.Errorf("getting working directory: %w", err)
		}
		return target, cwd, nil
	}
	g, err := target.Global()
	if err != nil {
		return nil, "", err
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return nil, "", fmt.Errorf("finding home directory: %w", err)
	}
	return g, home, nil
}

// IsTerminal returns true if stdin is connected to a terminal (not piped/redirected).
func IsTerminal() bool {
	fi, err := os.Stdin.Stat()
	if err != nil {
		return false
	}
	return fi.Mode()&os.ModeCharDevice != 0
}

// Confirm prompts the user with a y/N question via stderr.
// Returns true if the user answers "y" or "yes" (case-insensitive).
// In non-interactive mode, returns false.
func Confirm(prompt string) bool {
	if !IsTerminal() {
		return false
	}
	fmt.Fprintf(os.Stderr, "%s [y/N]: ", prompt)
	scanner := bufio.NewScanner(os.Stdin)
	if scanner.Scan() {
		answer := strings.TrimSpace(strings.ToLower(scanner.Text()))
		return answer == "y" || answer == "yes"
	}
	return false
}

// PromptChoice presents a list of options to the user via stderr and returns the selected value.
// Returns empty string in non-interactive mode.
func PromptChoice(prompt string, options []string) string {
	if !IsTerminal() {
		return ""
	}
	fmt.Fprintln(os.Stderr, prompt)
	for i, opt := range options {
		fmt.Fprintf(os.Stderr, "  %d) %s\n", i+1, opt)
	}
	fmt.Fprintf(os.Stderr, "Choose [1-%d]: ", len(options))
	scanner := bufio.NewScanner(os.Stdin)
	if scanner.Scan() {
		input := strings.TrimSpace(scanner.Text())
		// Try numeric
		for i, opt := range options {
			if input == fmt.Sprintf("%d", i+1) || strings.EqualFold(input, opt) {
				return opt
			}
		}
	}
	return ""
}

// ValidateAI resolves the --ai flag value: explicit flag > env var > interactive prompt > error.
func ValidateAI(aiFlag string) (string, error) {
	if aiFlag != "" {
		return strings.ToLower(aiFlag), targets.ValidateTarget(aiFlag)
	}

	// Check environment variables (MAKE_DECISION_AI is the legacy name)
	for _, name := range []string{"THINK_BETTER_AI", "MAKE_DECISION_AI"} {
		if env := os.Getenv(name); env != "" {
			if err := targets.ValidateTarget(env); err != nil {
				return "", fmt.Errorf("%s env var: %w", name, err)
			}
			return strings.ToLower(env), nil
		}
	}

	// Interactive prompt
	if IsTerminal() {
		choice := PromptChoice("Select AI target:", targets.TargetNames())
		if choice == "" {
			return "", fmt.Errorf("no AI target selected")
		}
		return choice, nil
	}

	return "", fmt.Errorf("--ai is required in non-interactive mode (or set THINK_BETTER_AI env var)")
}

// Errorf prints a formatted error to stderr.
func Errorf(format string, args ...interface{}) {
	fmt.Fprintf(os.Stderr, "error: "+format+"\n", args...)
}
