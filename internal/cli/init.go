package cli

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/HoangTheQuyen/think-better/internal/checker"
	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// RunInit handles the "init" subcommand.
func RunInit(args []string) int {
	fs := flag.NewFlagSet("init", flag.ContinueOnError)
	var sf SharedFlags
	AddSharedFlags(fs, &sf)

	fs.Usage = func() {
		fmt.Fprintln(os.Stderr, `Install decision-making frameworks and problem-solving skills for AI assistants.

Installs cognitive bias detection, strategic planning frameworks, and critical thinking
methodologies for Claude AI, GitHub Copilot, Antigravity, or OpenCode.

Usage:
  think-better init [--ai <target>] [--skill <name>] [--force]

Flags:`)
		fs.PrintDefaults()
	}

	if err := fs.Parse(args); err != nil {
		return 1
	}

	// Resolve AI target
	ai, err := ValidateAI(sf.AI)
	if err != nil {
		Errorf("%v", err)
		return 1
	}

	target := targets.FindTarget(ai)
	if target == nil {
		Errorf("invalid --ai value %q: must be %s", ai, strings.Join(targets.TargetNames(), " or "))
		return 1
	}

	// Resolve skill list
	var skillsToInstall []*skills.SkillPackage
	if sf.Skill != "" {
		s := skills.FindSkill(sf.Skill)
		if s == nil {
			Errorf("unknown skill %q. Available: %s", sf.Skill, strings.Join(skills.SkillNames(), ", "))
			return 1
		}
		skillsToInstall = append(skillsToInstall, s)
	} else {
		for i := range skills.Registry {
			skillsToInstall = append(skillsToInstall, &skills.Registry[i])
		}
	}

	cwd, err := os.Getwd()
	if err != nil {
		Errorf("getting working directory: %v", err)
		return 1
	}

	// Warn if target directory doesn't exist (only relevant for copilot which uses .github/)
	if ai == "copilot" {
		githubDir := filepath.Join(cwd, ".github")
		if _, err := os.Stat(githubDir); os.IsNotExist(err) {
			fmt.Fprintln(os.Stderr, "warning: .github/ directory does not exist (will be created)")
		}
	}

	inst := installer.NewInstaller(cwd)
	interactive := IsTerminal()
	totalFiles := 0
	hasError := false

	for _, skill := range skillsToInstall {
		fmt.Printf("Installing skill %q for %s...\n", skill.Name, ai)

		created, err := inst.Install(skill, target, sf.Force, interactive)
		if err != nil {
			Errorf("%v", err)
			hasError = true
			continue
		}

		if created == nil {
			// User declined overwrite
			fmt.Printf("Skipped %q\n", skill.Name)
			continue
		}

		installPath := target.InstallDir(skill.Name)
		for _, f := range created {
			fmt.Printf("  Created %s\n", filepath.ToSlash(filepath.Join(installPath, f)))
		}
		fmt.Printf("\n✓ Installed %d files to %s\n", len(created), installPath)
		totalFiles += len(created)
	}

	// Install workflow files (for targets that support them, e.g., Antigravity)
	// Always attempt workflow installation regardless of skill errors —
	// workflows are independent of skills and should not be blocked by them.
	if target.HasWorkflows() {
		wfCreated, err := inst.InstallWorkflows(target, sf.Force)
		if err != nil {
			Errorf("installing workflows: %v", err)
			hasError = true
		} else if len(wfCreated) > 0 {
			workflowDir := target.WorkflowDir()
			fmt.Printf("\nInstalling workflows to %s...\n", workflowDir)
			for _, f := range wfCreated {
				fmt.Printf("  Created %s\n", filepath.ToSlash(filepath.Join(workflowDir, f)))
			}
			fmt.Printf("✓ Installed %d workflow files\n", len(wfCreated))
			totalFiles += len(wfCreated)
		} else {
			fmt.Printf("\n✓ Workflows already up-to-date at %s\n", target.WorkflowDir())
		}
	}

	if hasError {
		return 1
	}

	// Next steps & prerequisite check
	if totalFiles > 0 {
		fmt.Println("\nNext steps:")
		if ai == "antigravity" {
			fmt.Println("  - Skills installed as Antigravity skills (SKILL.md entry points)")
			for _, s := range skillsToInstall {
				fmt.Printf("  - Skill %q is available in .agents/skills/%s/\n", s.Name, s.Name)
			}
			fmt.Println("  - Workflows installed: /solve, /solve.deep, /solve.exec, /solve.quick")
			fmt.Println("  - Workflows installed: /decide, /decide.deep, /decide.exec, /decide.quick")
		} else if ai == "opencode" {
			fmt.Println("  - Skills installed as OpenCode skills (SKILL.md entry points)")
			for _, s := range skillsToInstall {
				fmt.Printf("  - Skill %q is available in .opencode/skills/%s/\n", s.Name, s.Name)
			}
			fmt.Println("  - OpenCode will auto-discover skills via the native skill tool")
		} else if len(skillsToInstall) == 1 {
			fmt.Printf("  - Open your AI assistant and type /%s to start\n", skillsToInstall[0].Name)
		} else {
			for _, s := range skillsToInstall {
				fmt.Printf("  - Type /%s to use %s\n", s.Name, s.Description)
			}
		}

		// Check Python
		pyResult := checker.CheckPython()
		if !pyResult.Found {
			fmt.Println("  - Python 3 is required for skill scripts")
		} else {
			fmt.Printf("  - Python %s available for skill scripts\n", pyResult.Version)
		}
	}

	return 0
}
