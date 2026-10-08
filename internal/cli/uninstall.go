package cli

import (
	"errors"
	"fmt"
	"os"
	"slices"
	"strings"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

const uninstallUsage = `
Remove an installed decision-making, problem-solving or coding skill.

Removes the skill's files and the slash commands that run it, from every AI
tool it is installed for in this project (with --global: in your user
account). When it is installed for several AI tools, choose one with --ai
(you are asked when a terminal is attached; THINK_BETTER_AI also decides).

Files you modified since install are kept (and reported), as is any
directory that still holds other files. Asks for confirmation unless --yes
is given; without a terminal, --yes is required.

  -y, --yes   remove without asking; files you modified are still kept
  --force     also delete files you modified (implies --yes)

Usage:
  think-better uninstall (--skill <name> | --all) [--ai <target>] [--global]
                         [--yes] [--force] [--dry-run]`

// uninstallJob is one skill install to remove.
type uninstallJob struct {
	skill *skills.SkillPackage
	loc   skillLocation
	plan  *installer.Result
}

// RunUninstall handles the "uninstall" subcommand.
func RunUninstall(args []string) int {
	flags := newFlagSet("uninstall")
	var sf SharedFlags
	var all, yes bool
	AddSharedFlags(flags, &sf, "Also delete files you modified since install (implies --yes)")
	flags.BoolVar(&all, "all", false, "Remove every installed skill")
	addYesFlag(flags, &yes, "Remove without asking for confirmation (files you modified are kept)")
	flags.BoolVar(&sf.DryRun, "dry-run", false, "Show what would be removed without removing anything")
	if ok, code := parseFlags(flags, args, uninstallUsage); !ok {
		return code
	}

	switch {
	case sf.Skill != "" && all:
		Errorf("use either --skill or --all")
		return 1
	case sf.Skill == "" && !all:
		Errorf("--skill is required (or --all to remove every skill); installed skills: think-better list")
		return 1
	}
	var only *targets.AITarget
	if sf.AI != "" {
		if err := targets.ValidateTarget(sf.AI); err != nil {
			Errorf("%v", err)
			return 1
		}
		only = targets.FindTarget(sf.AI)
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
	if sf.Global && home == "" {
		Errorf("finding home directory failed")
		return 1
	}

	var jobs []uninstallJob
	for _, skill := range selected {
		for _, loc := range scopeLocations(skill, cwd, home, sf.Global) {
			if only == nil || loc.Target.Name == only.Name {
				jobs = append(jobs, uninstallJob{skill: skill, loc: loc})
			}
		}
	}
	if len(jobs) == 0 {
		where := pick(sf.Global, "for your user account", "in this project")
		if only != nil {
			where += " for " + only.Name
		}
		if all && only == nil {
			_, _ = fmt.Fprintf(stdout, "No installed skills found %s.%s\n", where, otherScopeHint(selected, cwd, home, sf.Global, only))
			return 0
		}
		what := "no skills are"
		if sf.Skill != "" {
			what = fmt.Sprintf("skill %q is", selected[0].Name)
		}
		Errorf("%s not installed %s%s", what, where, otherScopeHint(selected, cwd, home, sf.Global, only))
		return 1
	}

	if jobs, err = chooseTarget(jobs); err != nil {
		Errorf("%v", err)
		return 1
	}

	// Plan everything first, so the confirmation can say what goes.
	removeCount, modifiedCount := 0, 0
	for i := range jobs {
		j := &jobs[i]
		inst := installer.NewInstaller(j.loc.Base, Version())
		if j.plan, err = inst.Uninstall(j.skill, j.loc.Target, installer.Options{DryRun: true}); err != nil {
			if errors.Is(err, installer.ErrNotInstalled) {
				err = fmt.Errorf("%w (run 'think-better check' to see what is installed)", err)
			}
			Errorf("%v", err)
			return 1
		}
		removeCount += j.plan.Count(installer.ActionRemove)
		modifiedCount += j.plan.Count(installer.ActionKeepRemoved)
	}

	if !yes && !sf.Force && !sf.DryRun {
		if !interactive() {
			Errorf("use --yes (-y) to remove without confirmation")
			return 1
		}
		var what string
		if len(jobs) == 1 {
			j := jobs[0]
			what = fmt.Sprintf("skill %q from %s (%s)", j.skill.Name, j.loc.Path, plural(removeCount, "file", "files"))
		} else {
			_, _ = fmt.Fprintln(stderr, "Installed:")
			for _, j := range jobs {
				_, _ = fmt.Fprintf(stderr, "  - %s for %s (%s)\n", j.skill.Name, j.loc.Label, j.loc.Path)
			}
			what = fmt.Sprintf("these %s (%s)", plural(len(jobs), "install", "installs"), plural(removeCount, "file", "files"))
		}
		if modifiedCount > 0 {
			what += fmt.Sprintf(", keeping %s you modified", plural(modifiedCount, "file", "files"))
		}
		if !confirm("Remove " + what + "?") {
			_, _ = fmt.Fprintln(stdout, "Canceled.")
			return 0
		}
	}

	removed, kept, deleted := 0, 0, 0
	hasError := false
	for i, j := range jobs {
		if i > 0 {
			_, _ = fmt.Fprintln(stdout)
		}
		target := j.loc.Target
		inst := installer.NewInstaller(j.loc.Base, Version())
		res := j.plan
		if sf.DryRun {
			_, _ = fmt.Fprintf(stdout, "Would remove skill %q for %s (%s):\n", j.skill.Name, j.loc.Label, j.loc.Path)
		} else {
			_, _ = fmt.Fprintf(stdout, "Removing skill %q for %s (%s)...\n", j.skill.Name, j.loc.Label, j.loc.Path)
			if res, err = inst.Uninstall(j.skill, target, installer.Options{}); err != nil {
				Errorf("%v", err)
				hasError = true
				continue
			}
		}
		var purged []string
		if sf.Force {
			if purged, err = inst.RemoveModified(target, res, sf.DryRun); err != nil {
				Errorf("%v", err)
				hasError = true
			}
		}

		// With --force, the files kept as modified are listed as deleted instead.
		notPurged := func(list []installer.Change) []installer.Change {
			if !sf.Force {
				return list
			}
			return slices.DeleteFunc(slices.Clone(list), func(c installer.Change) bool { return c.Action == installer.ActionKeepRemoved })
		}
		printChanges(target.Display(res.Dir), notPurged(res.Files), sf.DryRun)
		if res.WorkflowDir != "" {
			printChanges(target.Display(res.WorkflowDir), notPurged(res.Workflows), sf.DryRun)
		}
		for _, p := range purged {
			_, _ = fmt.Fprintf(stdout, "  %s %s (modified by you; --force)\n", pick(sf.DryRun, "Would delete", "Deleted"), target.Display(p))
		}
		if res.DirRemoved {
			_, _ = fmt.Fprintf(stdout, "  Removed %s\n", j.loc.Path)
		} else if !sf.DryRun {
			_, _ = fmt.Fprintf(stdout, "  Kept %s (it still holds files you added or modified)\n", j.loc.Path)
		}
		removed += res.Count(installer.ActionRemove)
		deleted += len(purged)
		if !sf.Force {
			kept += res.Count(installer.ActionKeepRemoved)
		}
	}

	if sf.DryRun {
		_, _ = fmt.Fprintf(stdout, "\nDry run: would remove %s.\n", plural(removed+deleted, "file", "files"))
	} else {
		_, _ = fmt.Fprintf(stdout, "\n✓ Removed %s\n", plural(removed+deleted, "file", "files"))
	}
	if kept > 0 {
		_, _ = fmt.Fprintf(stdout, "Kept %s you modified; delete %s yourself if you no longer need %s (or rerun with --force).\n",
			plural(kept, "file", "files"), pick(kept == 1, "it", "them"), pick(kept == 1, "it", "them"))
	}
	if hasError {
		return 1
	}
	return 0
}

// scopeLocations returns where a skill is installed in one scope: the
// project (including old locations) or, with global, the user account.
func scopeLocations(skill *skills.SkillPackage, cwd, home string, global bool) []skillLocation {
	if global {
		var out []skillLocation
		for _, loc := range findSkillLocations(skill, cwd, home) {
			if loc.Global() {
				out = append(out, loc)
			}
		}
		return out
	}
	return append(findSkillLocations(skill, cwd, ""), findLegacyLocations(skill, cwd)...)
}

// chooseTarget narrows the jobs to one AI tool when the skills are installed
// for several: THINK_BETTER_AI decides when it names one of them, else the
// user is asked; without a terminal it is an error.
func chooseTarget(jobs []uninstallJob) ([]uninstallJob, error) {
	var names []string
	for _, j := range jobs {
		if !slices.Contains(names, j.loc.Target.Name) {
			names = append(names, j.loc.Target.Name)
		}
	}
	if len(names) < 2 {
		return jobs, nil
	}
	choice := ""
	for _, env := range []string{"THINK_BETTER_AI", "MAKE_DECISION_AI"} {
		if v := strings.ToLower(os.Getenv(env)); v != "" {
			if slices.Contains(names, v) {
				choice = v
			}
			break
		}
	}
	if choice == "" {
		if !interactive() {
			return nil, fmt.Errorf("installed for several AI tools (%s): choose one with --ai", strings.Join(names, ", "))
		}
		const allChoice = "all of them"
		choice = promptChoice("Installed for several AI tools. Remove from:", append(slices.Clone(names), allChoice))
		switch choice {
		case "":
			return nil, fmt.Errorf("no AI target selected")
		case allChoice:
			return jobs, nil
		}
	}
	return slices.DeleteFunc(jobs, func(j uninstallJob) bool { return j.loc.Target.Name != choice }), nil
}

// otherScopeHint points at the other scope when the skills are installed
// there: --global when they are only in the user account, and the reverse.
func otherScopeHint(selected []*skills.SkillPackage, cwd, home string, global bool, only *targets.AITarget) string {
	if home == "" {
		return ""
	}
	var paths []string
	for _, skill := range selected {
		for _, loc := range scopeLocations(skill, cwd, home, !global) {
			if only == nil || loc.Target.Name == only.Name {
				paths = append(paths, loc.Path)
			}
		}
	}
	if len(paths) == 0 {
		return ""
	}
	if global {
		return fmt.Sprintf("\n  It is installed in this project (%s); run without --global to remove it.", strings.Join(paths, ", "))
	}
	return fmt.Sprintf("\n  It is installed for your user account (%s); add --global to remove it.", strings.Join(paths, ", "))
}
