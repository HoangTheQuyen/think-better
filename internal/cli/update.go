package cli

import (
	"fmt"
	"os"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

const updateUsage = `
Update installed skills to the version bundled with this binary.

Finds every place a skill is installed, in this project and in your user
account, and brings it up to date:
  - files you have not modified are replaced with the new version
  - files you modified are kept; the new version is saved next to them as
    <file>.new (with --force they are replaced, after saving yours as <file>.bak)
  - files no longer part of a skill are removed, unless you modified them
Slash commands (workflows) are updated the same way.

--ai and --skill limit the update to one target or skill; --global limits it
to installs in your user account.

Usage:
  think-better update [--ai <target>] [--skill <name>] [--global] [--dry-run] [--force]`

// RunUpdate handles the "update" subcommand.
func RunUpdate(args []string) int {
	flags := newFlagSet("update")
	var sf SharedFlags
	AddSharedFlags(flags, &sf, "Replace files you modified (your version is saved as <file>.bak)")
	flags.BoolVar(&sf.DryRun, "dry-run", false, "Show what would change without writing anything")
	if ok, code := parseFlags(flags, args, updateUsage); !ok {
		return code
	}

	if sf.AI != "" {
		if err := targets.ValidateTarget(sf.AI); err != nil {
			Errorf("%v", err)
			return 1
		}
	}
	selected, err := selectSkills(sf.Skill)
	if err != nil {
		Errorf("%v", err)
		return 1
	}
	cwd, err := os.Getwd()
	if err != nil {
		Errorf("getting working directory: %v", err)
		return 1
	}
	home := userHome()

	opts := installer.Options{Force: sf.Force, DryRun: sf.DryRun}
	var results []*installer.Result
	found, hasError := 0, false
	for _, skill := range selected {
		for _, loc := range findSkillLocations(skill, cwd, home) {
			if (sf.AI != "" && loc.Target.Name != targets.FindTarget(sf.AI).Name) || (sf.Global && !loc.Global()) {
				continue
			}
			if found > 0 {
				_, _ = fmt.Fprintln(stdout)
			}
			found++
			_, _ = fmt.Fprintf(stdout, "Updating skill %q for %s (%s, %s)...\n", skill.Name, loc.Label, loc.Path, statusLabel(loc.Status))
			res, err := installer.NewInstaller(loc.Base, Version()).Install(skill, loc.Target, opts)
			if err != nil {
				Errorf("%v", err)
				hasError = true
				continue
			}
			printResult(loc.Target, res, sf.DryRun)
			results = append(results, res)
		}
	}

	if found == 0 {
		if sf.AI != "" || sf.Skill != "" {
			Errorf("no matching installed skills found (install with: think-better init)")
			return 1
		}
		_, _ = fmt.Fprintln(stdout, "No installed skills found. Install them with: think-better init")
		return 0
	}
	printMergeHint(results, sf.DryRun)
	if sf.DryRun {
		_, _ = fmt.Fprintln(stdout, "\nDry run: nothing was changed.")
	}
	if hasError {
		return 1
	}
	return 0
}
