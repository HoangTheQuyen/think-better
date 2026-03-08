package cli

import (
	"flag"
	"fmt"
	"os"

	"github.com/htrbao/think-better/internal/checker"
	"github.com/htrbao/think-better/internal/installer"
	"github.com/htrbao/think-better/internal/skills"
	"github.com/htrbao/think-better/internal/targets"
)

// RunCheck handles the "check" subcommand.
func RunCheck(args []string) int {
	fs := flag.NewFlagSet("check", flag.ContinueOnError)

	fs.Usage = func() {
		fmt.Fprintln(os.Stderr, `Verify runtime prerequisites for decision-making and problem-solving skills.

Checks Python 3 availability for analysis scripts (bias detection, framework search, data processing).

Usage:
  think-better check

Flags:`)
		fs.PrintDefaults()
	}

	if err := fs.Parse(args); err != nil {
		return 1
	}

	fmt.Println("Checking prerequisites...")

	warnings := 0

	// Check Python
	pyResult := checker.CheckPython()
	if pyResult.Found {
		fmt.Printf("  ✓ Python %s found at %s\n", pyResult.Version, pyResult.Path)
	} else {
		fmt.Println("  ✗ Python 3 not found")
		fmt.Println("    Install from https://python.org or your package manager")
		warnings++
	}

	cwd, err := os.Getwd()
	if err != nil {
		Errorf("getting working directory: %v", err)
		return 1
	}

	// Check skill installation status
	defaultTarget := &targets.Targets[0]
	for _, skill := range skills.Registry {
		status, err := installer.CheckStatus(&skill, defaultTarget, cwd)
		if err != nil {
			fmt.Printf("  ✗ Skill %q: error checking status\n", skill.Name)
			warnings++
			continue
		}

		switch status.Status {
		case installer.StatusInstalled:
			files, _ := skills.SkillFiles(skill.Name)
			fmt.Printf("  ✓ Skill %q installed (%d files)\n", skill.Name, len(files))
		case installer.StatusIncomplete:
			fmt.Printf("  ⚠ Skill %q incomplete (%d missing files)\n", skill.Name, len(status.MissingFiles))
			warnings++
		case installer.StatusNotInstalled:
			fmt.Printf("  ✗ Skill %q not installed\n", skill.Name)
			warnings++
		}
	}

	if warnings > 0 {
		fmt.Printf("\n%d warning(s)\n", warnings)
		return 1
	}

	fmt.Println("\n✓ All prerequisites met")
	return 0
}
