// Package cli provides subcommand handlers for the think-better CLI.
package cli

import (
	"bufio"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"

	"github.com/HoangTheQuyen/think-better/internal/checker"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// Output streams and hooks, replaceable in tests.
var (
	stdout      io.Writer = os.Stdout
	stderr      io.Writer = os.Stderr
	checkPython           = checker.CheckPython
	// interactive reports whether the user can answer prompts. Runs with
	// stdin redirected (pipes, files, /dev/null, CI) never prompt.
	interactive = func() bool { return isTerminal(os.Stdin.Fd()) }
	stdinReader *bufio.Reader
)

// SharedFlags contains flags common to multiple subcommands.
type SharedFlags struct {
	AI     string
	Skill  string
	Force  bool
	Global bool
	DryRun bool
}

// AddSharedFlags registers the common flags on a FlagSet. forceHelp
// describes what --force does for the command.
func AddSharedFlags(fs *flag.FlagSet, sf *SharedFlags, forceHelp string) {
	fs.StringVar(&sf.AI, "ai", "", "AI target: "+strings.Join(targets.TargetNames(), ", "))
	fs.StringVar(&sf.Skill, "skill", "", "Skill name")
	fs.BoolVar(&sf.Force, "force", false, forceHelp)
	fs.BoolVar(&sf.Global, "global", false, "Use your user account (all projects) instead of the current project")
}

// newFlagSet creates a flag set for a subcommand; parseFlags reports its errors.
func newFlagSet(name string) *flag.FlagSet {
	return flag.NewFlagSet(name, flag.ContinueOnError)
}

// parseFlags parses args for a subcommand. --help/-h prints the usage to
// stdout and exits 0; a bad flag or an unexpected positional argument
// prints an error to stderr and exits 1. ok is false when the command must
// stop and return code.
func parseFlags(fs *flag.FlagSet, args []string, usage string) (ok bool, code int) {
	fs.SetOutput(io.Discard) // errors are reported below
	fs.Usage = func() {}
	printUsage := func(w io.Writer) {
		_, _ = fmt.Fprintln(w, strings.TrimSpace(usage))
		hasFlags := false
		fs.VisitAll(func(*flag.Flag) { hasFlags = true })
		if hasFlags {
			_, _ = fmt.Fprintln(w, "\nFlags:")
			fs.SetOutput(w)
			fs.PrintDefaults()
			fs.SetOutput(io.Discard)
		}
	}

	err := fs.Parse(args)
	if errors.Is(err, flag.ErrHelp) {
		printUsage(stdout)
		return false, 0
	}
	if err == nil && fs.NArg() > 0 {
		arg := fs.Arg(0)
		err = fmt.Errorf("unexpected argument %q", arg)
		if targets.ValidTarget(arg) {
			err = fmt.Errorf("unexpected argument %q (did you mean --ai %s?)", arg, strings.ToLower(arg))
		}
	}
	if err != nil {
		Errorf("%v", err)
		_, _ = fmt.Fprintf(stderr, "Run 'think-better %s --help' for usage.\n", fs.Name())
		return false, 1
	}
	return true, 0
}

// ResolveScope returns the target and base directory an existing install is
// in: the home directory with the target's user-level paths for --global,
// otherwise the current project (see currentProject), so commands run from
// a subdirectory find the project's install.
func ResolveScope(target *targets.AITarget, global bool) (*targets.AITarget, string, error) {
	return resolveScope(target, global, false)
}

// ResolveInstallScope is ResolveScope for init: the project is the current
// directory, with a warning when a parent directory already has an install.
func ResolveInstallScope(target *targets.AITarget, global bool) (*targets.AITarget, string, error) {
	return resolveScope(target, global, true)
}

func resolveScope(target *targets.AITarget, global, install bool) (*targets.AITarget, string, error) {
	if !global {
		var dir string
		if install {
			cwd, err := os.Getwd()
			if err != nil {
				return nil, "", fmt.Errorf("getting working directory: %w", err)
			}
			dir = cwd
			if root := findProject(cwd, userHome()); root != "" && root != cwd && hasInstall(root) {
				_, _ = fmt.Fprintf(stderr, "warning: %s already has skills installed; installing into the current directory %s instead (run from %s to update that install)\n", root, cwd, root)
			}
		} else {
			var err error
			if dir, err = currentProject(); err != nil {
				return nil, "", err
			}
		}
		// In the home directory, a target whose project and user-level
		// paths are the same (claude: ~/.claude/skills) would write its
		// user-level install with project-relative paths. That directory is
		// the user-level install, so treat the command as --global.
		home := userHome()
		if home == "" || target.InstallPattern != target.GlobalInstallPattern || !isSameDir(dir, home) {
			return target, dir, nil
		}
		_, _ = fmt.Fprintf(stderr, "note: in your home directory, %s skills are your user-level install; using --global\n", target.Name)
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

// currentProject returns the project directory commands that look for an
// existing install work in: the nearest directory, from the current one up,
// that holds an install or is a repository root (see findProject), or else
// the current directory.
func currentProject() (string, error) {
	cwd, err := os.Getwd()
	if err != nil {
		return "", fmt.Errorf("getting working directory: %w", err)
	}
	root := findProject(cwd, userHome())
	if root == "" {
		return cwd, nil
	}
	if root != cwd {
		_, _ = fmt.Fprintf(stderr, "note: using the project at %s\n", root)
	}
	return root, nil
}

// readLine reads one answer line from stdin ("" on EOF or error).
func readLine() string {
	if stdinReader == nil {
		stdinReader = bufio.NewReader(os.Stdin)
	}
	line, _ := stdinReader.ReadString('\n')
	return strings.TrimSpace(line)
}

// confirm asks a y/N question on stderr. It returns false without asking
// when the session is not interactive.
func confirm(prompt string) bool {
	if !interactive() {
		return false
	}
	_, _ = fmt.Fprintf(stderr, "%s [y/N]: ", prompt)
	answer := strings.ToLower(readLine())
	return answer == "y" || answer == "yes"
}

// promptChoice asks the user to pick one of options (by number or name).
// It returns "" without asking when the session is not interactive.
func promptChoice(prompt string, options []string) string {
	if !interactive() {
		return ""
	}
	_, _ = fmt.Fprintln(stderr, prompt)
	for i, opt := range options {
		_, _ = fmt.Fprintf(stderr, "  %d) %s\n", i+1, opt)
	}
	_, _ = fmt.Fprintf(stderr, "Choose [1-%d]: ", len(options))
	input := readLine()
	for i, opt := range options {
		if input == strconv.Itoa(i+1) || strings.EqualFold(input, opt) {
			return opt
		}
	}
	return ""
}

// resolveTarget resolves the --ai flag: explicit flag > THINK_BETTER_AI
// (or the legacy MAKE_DECISION_AI) > interactive prompt > error.
func resolveTarget(aiFlag string) (*targets.AITarget, error) {
	name := aiFlag
	source := "--ai"
	if name == "" {
		for _, env := range []string{"THINK_BETTER_AI", "MAKE_DECISION_AI"} {
			if v := os.Getenv(env); v != "" {
				name, source = v, env+" env var"
				break
			}
		}
	}
	if name == "" {
		if !interactive() {
			return nil, fmt.Errorf("--ai is required in non-interactive mode (or set THINK_BETTER_AI env var)")
		}
		if name = promptChoice("Select AI target:", targets.TargetNames()); name == "" {
			return nil, fmt.Errorf("no AI target selected")
		}
	}
	if err := targets.ValidateTarget(name); err != nil {
		if source != "--ai" {
			return nil, fmt.Errorf("%s: %w", source, err)
		}
		return nil, err
	}
	return targets.FindTarget(name), nil
}

// Errorf prints a formatted error to stderr.
func Errorf(format string, args ...any) {
	_, _ = fmt.Fprintf(stderr, "error: "+format+"\n", args...)
}
