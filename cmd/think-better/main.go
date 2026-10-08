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
	"diff":      cli.RunDiff,
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
	_, _ = fmt.Fprintln(w, `think-better — decision-making, problem-solving and coding skills for AI assistants

Install skills and slash commands for Claude Code, GitHub Copilot, Antigravity
and OpenCode: decision frameworks with cognitive bias detection (make-decision),
systematic problem-solving methods (problem-solving-pro) and coding workflows
for debugging, features, refactoring, reviews, tests and performance (code-solving).

Usage:
  think-better <command> [options]

Commands:
  init        Install skills and slash commands (updates an existing install)
  update      Update installed skills everywhere they are installed (project and global)
  diff        Show the new versions (.new files) waiting to be merged into files you modified
  list        Show available skills and where they are installed
  uninstall   Remove installed skills (keeps files you modified unless --force)
  check       Verify prerequisites (Python 3) and installed skills
  version     Show version information (also -v, --version)
  help        Show this help message (help <command> for command help)

Common options:
  --ai <target>    AI assistant target: claude, copilot, antigravity, opencode
  --skill <name>   Skill name (default: all for init and update; uninstall needs --skill or --all)
  --global         Use your user account (all projects) instead of the current project
  --dry-run        init/update/uninstall: show what would change
  --force          init/update: replace files you modified (yours are saved as .bak)
                   uninstall: also delete files you modified (implies --yes)
  -y, --yes        uninstall: do not ask for confirmation (files you modified are kept)
  --exclude-command <command>
                   init/update: leave out a slash command, e.g. code.perf (remembered)

Files you modify in an installed skill are never overwritten silently: init
and update keep them and save the new version next to them as <file>.new
(see them with 'think-better diff').

Environment:
  THINK_BETTER_AI  Default for --ai (e.g. claude)

Run 'think-better <command> --help' for command-specific help.`)
}
