package cli

import (
	"flag"
	"fmt"
	"os"

	"github.com/HoangTheQuyen/think-better/internal/checker"
	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
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

	// Check skill installation status across all AI tools, project and global
	home := userHome()
	for i := range skills.Registry {
		skill := &skills.Registry[i]
		locations := findSkillLocations(skill, cwd, home)
		if len(locations) == 0 {
			fmt.Printf("  ✗ Skill %q not installed (run: think-better init)\n", skill.Name)
			warnings++
			continue
		}
		for _, loc := range locations {
			if loc.Status == installer.StatusIncomplete {
				fmt.Printf("  ⚠ Skill %q incomplete in %s (run: think-better init --force)\n", skill.Name, loc.Path)
				warnings++
			} else {
				fmt.Printf("  ✓ Skill %q installed for %s (%s)\n", skill.Name, loc.Label, loc.Path)
			}
		}
	}

	if warnings > 0 {
		fmt.Printf("\n%d warning(s)\n", warnings)
		return 1
	}

	fmt.Println("\n✓ All prerequisites met")
	return 0
}
