package main

import (
	"fmt"
	"io"
	"os"

	"github.com/HoangTheQuyen/think-better/internal/cli"
	"github.com/HoangTheQuyen/think-better/internal/skills"
)

// Injected at build time via -ldflags -X. When left unset, the version is
// read from the module build information (see cli.SetBuildInfo).
var (
	version   = "dev"
	commit    = "unknown"
	buildDate = "unknown"
)

func main() {
	cli.SetBuildInfo(version, commit, buildDate)
	os.Exit(run(os.Args[1:], os.Stdout, os.Stderr))
}

var commands = map[string]func([]string) int{
	"init":      cli.RunInit,
	"update":    cli.RunUpdate,
	"list":      cli.RunList,
	"uninstall": cli.RunUninstall,
	"check":     cli.RunCheck,
	"version":   cli.RunVersion,
}

func run(args []string, stdout, stderr io.Writer) int {
	// Validate embedded skills are present
	if err := skills.ValidateEmbedded(); err != nil {
		_, _ = fmt.Fprintf(stderr, "error: %v\n", err)
		return 1
	}

	if len(args) == 0 {
		printUsage(stderr)
		return 1
	}

	switch cmd := args[0]; cmd {
	case "-v", "--version", "-version":
		_, _ = fmt.Fprintln(stdout, cli.VersionString())
		return 0
	case "help", "--help", "-h", "-help":
		// "think-better help init" shows the help of a command
		if len(args) > 1 {
			if cmdFn, ok := commands[args[1]]; ok {
				return cmdFn([]string{"--help"})
			}
			_, _ = fmt.Fprintf(stderr, "error: unknown command %q\n\n", args[1])
			printUsage(stderr)
			return 1
		}
		printUsage(stdout)
		return 0
	default:
		if cmdFn, ok := commands[cmd]; ok {
			return cmdFn(args[1:])
		}
		_, _ = fmt.Fprintf(stderr, "error: unknown command %q\n\n", cmd)
		printUsage(stderr)
		return 1
	}
}

func printUsage(w io.Writer) {
	_, _ = fmt.Fprintln(w, `think-better — AI-powered decision-making framework & problem-solving toolkit

Install decision frameworks and critical thinking skills for Claude Code,
GitHub Copilot, Antigravity and OpenCode. Includes cognitive bias detection,
strategic planning frameworks, and systematic problem-solving methodologies.

Usage:
  think-better <command> [options]

Commands:
  init        Install AI assistant skills and slash commands (updates an existing install)
  update      Update installed skills everywhere they are installed (project and global)
  list        Show available frameworks and where they are installed
  uninstall   Remove an installed skill (keeps files you modified)
  check       Verify prerequisites (Python 3) and installed skills
  version     Show version information (also -v, --version)
  help        Show this help message (help <command> for command help)

Common options:
  --ai string     AI assistant target: claude, copilot, antigravity, opencode
  --skill string  Skill name (default: all for init and update, required for uninstall)
  --global        Use your user account (all projects); claude, opencode, antigravity
  --force         init/update: replace files you modified (saved as .bak first)
                  uninstall: do not ask for confirmation
  --dry-run       init/update/uninstall: show what would change

Files you modify in an installed skill are never overwritten silently: init
and update keep them and save the new version next to them as <file>.new.

Environment:
  THINK_BETTER_AI  Default for --ai (e.g. claude)

Run 'think-better <command> --help' for command-specific help.`)
}
