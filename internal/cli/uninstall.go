package cli

import (
	"errors"
	"fmt"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

const uninstallUsage = `
Remove an installed decision-making or problem-solving skill.

Removes the skill's files and the slash commands that run it. Files you
modified since install are kept (and reported), as is any directory that
still holds other files. Asks for confirmation unless --force is given;
without a terminal, --force is required.

Usage:
  think-better uninstall [--ai <target>] --skill <name> [--global] [--force] [--dry-run]`

// RunUninstall handles the "uninstall" subcommand.
func RunUninstall(args []string) int {
	flags := newFlagSet("uninstall")
	var sf SharedFlags
	AddSharedFlags(flags, &sf, "Remove without asking for confirmation")
	flags.BoolVar(&sf.DryRun, "dry-run", false, "Show what would be removed without removing anything")
	if ok, code := parseFlags(flags, args, uninstallUsage); !ok {
		return code
	}

	if sf.Skill == "" {
		Errorf("--skill is required")
		return 1
	}
	selected, err := selectSkills(sf.Skill)
	if err != nil {
		Errorf("%v", err)
		return 1
	}
	skill := selected[0]
	projectTarget, err := resolveTarget(sf.AI)
	if err != nil {
		Errorf("%v", err)
		return 1
	}
	target, baseDir, err := ResolveScope(projectTarget, sf.Global)
	if err != nil {
		Errorf("%v", err)
		return 1
	}

	inst := installer.NewInstaller(baseDir, Version())
	plan, err := inst.Uninstall(skill, target, installer.Options{DryRun: true})
	if errors.Is(err, installer.ErrNotInstalled) {
		Errorf("%v%s", err, otherScopeHint(skill, projectTarget, sf.Global))
		return 1
	}
	if err != nil {
		Errorf("%v", err)
		return 1
	}

	shown := target.Display(target.InstallDir(skill.Name))
	if !sf.Force && !sf.DryRun {
		if !interactive() {
			Errorf("use --force to remove without confirmation")
			return 1
		}
		n := plan.Count(installer.ActionRemove)
		if !confirm(fmt.Sprintf("Remove skill %q from %s (%s)?", skill.Name, shown, plural(n, "file", "files"))) {
			_, _ = fmt.Fprintln(stdout, "Canceled.")
			return 0
		}
	}

	res := plan
	if !sf.DryRun {
		_, _ = fmt.Fprintf(stdout, "Removing skill %q for %s...\n", skill.Name, target.Name)
		if res, err = inst.Uninstall(skill, target, installer.Options{}); err != nil {
			Errorf("%v", err)
			return 1
		}
	} else {
		_, _ = fmt.Fprintf(stdout, "Would remove skill %q for %s:\n", skill.Name, target.Name)
	}

	printChanges(target.Display(res.Dir), res.Files, sf.DryRun)
	if res.DirRemoved {
		_, _ = fmt.Fprintf(stdout, "  Removed %s\n", shown)
	} else if !sf.DryRun {
		_, _ = fmt.Fprintf(stdout, "  Kept %s (it still holds files you added or modified)\n", shown)
	}
	if res.WorkflowDir != "" {
		printChanges(target.Display(res.WorkflowDir), res.Workflows, sf.DryRun)
	}

	removed := res.Count(installer.ActionRemove)
	kept := res.Count(installer.ActionKeepRemoved)
	if sf.DryRun {
		_, _ = fmt.Fprintf(stdout, "\nDry run: would remove %s.\n", plural(removed, "file", "files"))
	} else {
		_, _ = fmt.Fprintf(stdout, "\n✓ Removed %s\n", plural(removed, "file", "files"))
	}
	if kept > 0 {
		_, _ = fmt.Fprintf(stdout, "Kept %s you modified; delete %s yourself if you no longer need %s.\n",
			plural(kept, "file", "files"), pick(kept == 1, "it", "them"), pick(kept == 1, "it", "them"))
	}
	return 0
}

// otherScopeHint suggests the other scope when the skill is installed there:
// --global when it is only in the user account, and the reverse.
func otherScopeHint(skill *skills.SkillPackage, target *targets.AITarget, global bool) string {
	other, base, err := ResolveScope(target, !global)
	if err != nil {
		return ""
	}
	st, err := installer.CheckStatus(skill, other, base, Version())
	if err != nil || st.Status == installer.StatusNotInstalled {
		return ""
	}
	if global {
		return fmt.Sprintf("\n  It is installed in this project (%s); run without --global to remove it.", other.Display(other.InstallDir(skill.Name)))
	}
	return fmt.Sprintf("\n  It is installed for your user account (%s); add --global to remove it.", other.Display(other.InstallDir(skill.Name)))
}
