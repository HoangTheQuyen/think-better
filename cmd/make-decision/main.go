package main

import (
	"fmt"
	"os"

	"github.com/htrbao/think-better/internal/cli"
	"github.com/htrbao/think-better/internal/skills"
)

// Injected at build time via -ldflags -X
var (
	version   = "dev"
	commit    = "unknown"
	buildDate = "unknown"
)

func main() {
	os.Exit(run())
}

func run() int {
	// Validate embedded skills are present
	if err := skills.ValidateEmbedded(); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		return 1
	}

	if len(os.Args) < 2 {
		printUsage()
		return 1
	}

	switch os.Args[1] {
	case "init":
		return cli.RunInit(os.Args[2:])
	case "list":
		return cli.RunList(os.Args[2:])
	case "uninstall":
		return cli.RunUninstall(os.Args[2:])
	case "check":
		return cli.RunCheck(os.Args[2:])
	case "version", "--version":
		printVersion()
		return 0
	case "help", "--help", "-h":
		printUsage()
		return 0
	default:
		fmt.Fprintf(os.Stderr, "error: unknown command %q\n\n", os.Args[1])
		printUsage()
		return 1
	}
}

func printVersion() {
	fmt.Printf("think-better %s (%s %s)\n", version, commit, buildDate)
}

func printUsage() {
	fmt.Fprintln(os.Stderr, `think-better — AI-powered decision-making framework & problem-solving toolkit

Install decision frameworks and critical thinking skills for Claude AI and GitHub Copilot.
Includes cognitive bias detection, strategic planning frameworks, and systematic problem-solving methodologies.

Usage:
  think-better <command> [options]

Commands:
  init        Install AI assistant skills (decision-making, problem-solving)
  list        Show available frameworks and installation status
  uninstall   Remove installed skills
  check       Verify prerequisites (Python 3 for analysis scripts)
  version     Show version information
  help        Show this help message

Global options:
  --ai string     AI assistant target: claude, copilot, antigravity
  --skill string  Skill name (default: all for init, required for uninstall)
  --force         Skip confirmation prompts

Run 'think-better <command> --help' for command-specific help.`)
}
