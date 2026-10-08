package cli

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// RunUninstall handles the "uninstall" subcommand.
func RunUninstall(args []string) int {
	fs := flag.NewFlagSet("uninstall", flag.ContinueOnError)
	var sf SharedFlags
	AddSharedFlags(fs, &sf)

	fs.Usage = func() {
		fmt.Fprintln(os.Stderr, `Remove an installed decision-making or problem-solving skill.

Removes all skill files from AI assistant installation directory.
Use --force to skip confirmation prompt.

Usage:
  think-better uninstall [--ai <target>] --skill <name> [--global] [--force]

Flags:`)
		fs.PrintDefaults()
	}

	if err := fs.Parse(args); err != nil {
		return 1
	}

	// --skill is required for uninstall
	if sf.Skill == "" {
		Errorf("--skill is required")
		return 1
	}

	skill := skills.FindSkill(sf.Skill)
	if skill == nil {
		Errorf("unknown skill %q. Available: %s", sf.Skill, strings.Join(skills.SkillNames(), ", "))
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

	target, baseDir, err := ResolveScope(target, sf.Global)
	if err != nil {
		Errorf("%v", err)
		return 1
	}

	uninst := installer.NewUninstaller(baseDir)
	interactive := IsTerminal()

	fmt.Printf("Removing skill %q for %s...\n", skill.Name, ai)

	removed, err := uninst.Uninstall(skill, target, sf.Force, interactive)
	if err != nil {
		Errorf("%v", err)
		return 1
	}

	if removed == nil {
		fmt.Println("Canceled.")
		return 0
	}

	installPath := target.InstallDir(skill.Name)
	shown := target.Display(installPath)
	for _, f := range removed {
		fmt.Printf("  Removed %s\n", filepath.ToSlash(filepath.Join(shown, f)))
	}

	// Check if skill directory was removed
	installDir := filepath.Join(baseDir, filepath.FromSlash(installPath))
	if _, err := os.Stat(installDir); os.IsNotExist(err) {
		fmt.Printf("  Removed %s\n", shown)
	}

	// Remove the slash commands that run this skill
	wfRemoved, err := uninst.UninstallWorkflows(skill, target)
	for _, f := range wfRemoved {
		fmt.Printf("  Removed %s\n", filepath.ToSlash(filepath.Join(target.Display(target.WorkflowDir()), f)))
	}
	if err != nil {
		Errorf("%v", err)
		return 1
	}

	fmt.Printf("\n✓ Removed %d files\n", len(removed)+len(wfRemoved))
	return 0
}
