package cli

import (
	"fmt"
	"os"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

const updateUsage = `
Update installed skills to the version bundled with this binary.

Finds every place a skill (decision-making, problem-solving or coding) is
installed, in this project and in your user account, and brings it up to date:
  - files you have not modified are replaced with the new version
  - files you modified are kept; the new version is saved next to them as
    <file>.new (with --force they are replaced, after saving yours as <file>.bak)
  - files no longer part of a skill are removed, unless you modified them
Slash commands (workflows) are updated the same way. A slash command you
deleted is restored; to keep it removed, exclude it with --exclude-command.
Skills found where an earlier release put them (Copilot: .github/prompts/)
are moved to where the AI tool loads them.

Review the .new files with 'think-better diff'.

--ai and --skill limit the update to one target or skill; --global limits it
to installs in your user account.

Usage:
  think-better update [--ai <target>] [--skill <name>] [--global] [--dry-run] [--force]
                      [--exclude-command <command>] [--include-command <command>]`

// RunUpdate handles the "update" subcommand.
func RunUpdate(args []string) int {
	flags := newFlagSet("update")
	var sf SharedFlags
	var cf commandFlags
	AddSharedFlags(flags, &sf, "Replace files you modified (your version is saved as <file>.bak)")
	flags.BoolVar(&sf.DryRun, "dry-run", false, "Show what would change without writing anything")
	addCommandFlags(flags, &cf)
	if ok, code := parseFlags(flags, args, updateUsage); !ok {
		return code
	}

	var only *targets.AITarget
	if sf.AI != "" {
		if err := targets.ValidateTarget(sf.AI); err != nil {
			Errorf("%v", err)
			return 1
		}
		only = targets.FindTarget(sf.AI)
	}
	if err := cf.validate(); err != nil {
		Errorf("%v", err)
		return 1
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

	var results []*installer.Result
	var restored []string
	found, hasError := 0, false
	// exclusions applies the command flags once per location.
	exclusions := map[string][]string{}
	optsFor := func(inst *installer.Installer, target *targets.AITarget) (installer.Options, error) {
		opts := installer.Options{Force: sf.Force, DryRun: sf.DryRun}
		key := inst.BaseDir + "\x00" + target.WorkflowDir()
		list, ok := exclusions[key]
		if !ok {
			var err error
			if list, err = cf.apply(inst, target, sf.DryRun); err != nil {
				return opts, err
			}
			exclusions[key] = list
		}
		opts.ExcludeWorkflows = list
		return opts, nil
	}
	separate := func() {
		if found > 0 {
			_, _ = fmt.Fprintln(stdout)
		}
		found++
	}

	for _, skill := range selected {
		// Installs at an old location are moved first; the project install
		// of that target is then up to date.
		moved := map[string]bool{}
		if !sf.Global {
			for _, loc := range findLegacyLocations(skill, cwd) {
				if only != nil && loc.Target.Name != only.Name {
					continue
				}
				separate()
				target := targets.FindTarget(loc.Target.Name)
				opts, err := optsFor(installer.NewInstaller(loc.Base, Version()), target)
				if err == nil {
					var res *installer.Result
					if res, err = migrateLocation(skill, loc, opts); err == nil {
						results = append(results, res)
					}
				}
				if err != nil {
					Errorf("%v", err)
					hasError = true
				}
				moved[loc.Target.Name] = true
			}
		}

		for _, loc := range findSkillLocations(skill, cwd, home) {
			if (only != nil && loc.Target.Name != only.Name) || (sf.Global && !loc.Global()) ||
				(!loc.Global() && moved[loc.Target.Name]) {
				continue
			}
			separate()
			_, _ = fmt.Fprintf(stdout, "Updating skill %q for %s (%s, %s)...\n", skill.Name, loc.Label, loc.Path, statusLabel(loc.Status))
			inst := installer.NewInstaller(loc.Base, Version())
			opts, err := optsFor(inst, loc.Target)
			if err != nil {
				Errorf("%v", err)
				hasError = true
				continue
			}
			res, err := inst.Install(skill, loc.Target, opts)
			if err != nil {
				Errorf("%v", err)
				hasError = true
				continue
			}
			printResult(loc.Target, res, sf.DryRun)
			results = append(results, res)
			restored = append(restored, restoredCommands(res, loc.Status)...)
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
	if !cf.set() {
		printRestoredHint(restored, sf.DryRun)
	}
	if sf.DryRun {
		_, _ = fmt.Fprintln(stdout, "\nDry run: nothing was changed.")
	}
	if hasError {
		return 1
	}
	return 0
}
