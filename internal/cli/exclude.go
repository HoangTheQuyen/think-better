package cli

import (
	"flag"
	"fmt"
	"path"
	"slices"
	"strings"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// Slash commands you do not want can be excluded per install location:
// init and update then neither install nor restore them, and remove them
// when unmodified. The list is kept in the workflow manifest.

// commandFlags are the --exclude-command and --include-command flags.
type commandFlags struct {
	exclude, include listFlag
}

func addCommandFlags(fs *flag.FlagSet, cf *commandFlags) {
	fs.Var(&cf.exclude, "exclude-command",
		"Do not install or restore this slash `command` (e.g. code.perf), and remove it\nif unmodified; remembered for later updates (repeatable, comma-separated)")
	fs.Var(&cf.include, "include-command",
		"Install an excluded slash `command` again (repeatable, comma-separated)")
}

// commandNames returns the names of all slash commands ("code", "code.debug", ...).
func commandNames() []string {
	files, _ := skills.WorkflowFiles()
	names := make([]string, 0, len(files))
	for _, f := range files {
		names = append(names, strings.TrimSuffix(path.Base(f), ".md"))
	}
	return names
}

// normalizeCommand accepts "/code.perf", "code.perf", "code.perf.md" and
// "code.perf.prompt.md".
func normalizeCommand(name string) string {
	name = strings.TrimPrefix(strings.TrimSpace(name), "/")
	name = strings.TrimSuffix(name, ".md")
	return strings.TrimSuffix(name, ".prompt")
}

// validate normalizes the command names and checks they exist.
func (cf *commandFlags) validate() error {
	known := commandNames()
	for _, list := range []*listFlag{&cf.exclude, &cf.include} {
		for i, n := range *list {
			norm := normalizeCommand(n)
			if !slices.Contains(known, norm) {
				return fmt.Errorf("unknown slash command %q. Available: %s", n, strings.Join(known, ", "))
			}
			(*list)[i] = norm
		}
	}
	for _, n := range cf.exclude {
		if slices.Contains(cf.include, n) {
			return fmt.Errorf("slash command %q is both excluded and included", n)
		}
	}
	return nil
}

func (cf *commandFlags) set() bool {
	return len(cf.exclude) > 0 || len(cf.include) > 0
}

// apply updates the exclusion list of the target's workflow directory and
// returns it for Options.ExcludeWorkflows (nil when the flags are not used,
// so Install reads the saved list). The list is saved unless dryRun.
func (cf *commandFlags) apply(inst *installer.Installer, target *targets.AITarget, dryRun bool) ([]string, error) {
	if !cf.set() || !target.HasWorkflows() {
		return nil, nil
	}
	list, err := inst.ExcludedWorkflows(target)
	if err != nil {
		return nil, err
	}
	for _, n := range cf.exclude {
		if f := target.WorkflowFileName(n + ".md"); !slices.Contains(list, f) {
			list = append(list, f)
		}
	}
	list = slices.DeleteFunc(list, func(f string) bool {
		return slices.ContainsFunc(cf.include, func(n string) bool { return target.WorkflowFileName(n+".md") == f })
	})
	slices.Sort(list)
	if !dryRun {
		if err := inst.SetExcludedWorkflows(target, list); err != nil {
			return nil, err
		}
	}
	if list == nil {
		list = []string{} // not nil: overrides the saved list in a dry run
	}
	return list, nil
}

// excludedCommands returns the excluded slash command names for a target.
func excludedCommands(inst *installer.Installer, target *targets.AITarget) []string {
	files, _ := inst.ExcludedWorkflows(target)
	var names []string
	for _, f := range files {
		names = append(names, normalizeCommand(f))
	}
	return names
}

// restoredCommands lists the slash commands an update recreated although
// they had been installed before: the user (or something else) deleted them.
func restoredCommands(res *installer.Result, before *installer.InstallStatus) []string {
	if before == nil || res.WorkflowDir == "" {
		return nil
	}
	var names []string
	for _, c := range res.Workflows {
		if c.Action == installer.ActionCreate && slices.Contains(before.Missing, path.Join(res.WorkflowDir, c.Path)) {
			names = append(names, normalizeCommand(c.Path))
		}
	}
	return names
}

// printRestoredHint explains how to keep deleted slash commands removed.
func printRestoredHint(names []string, dryRun bool) {
	if len(names) == 0 {
		return
	}
	slices.Sort(names)
	names = slices.Compact(names)
	cmds := make([]string, len(names))
	for i, n := range names {
		cmds[i] = "/" + n
	}
	_, _ = fmt.Fprintf(stdout, "\nNote: %s deleted since install %s restored: %s.\n"+
		"To keep %s removed, run: think-better update --exclude-command %s\n",
		plural(len(names), "slash command", "slash commands"), pick(dryRun, "would be", pick(len(names) == 1, "was", "were")),
		strings.Join(cmds, ", "), pick(len(names) == 1, "it", "them"), strings.Join(names, ","))
}
