package cli

import (
	"fmt"
	"path"
	"strings"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

func plural(n int, one, many string) string {
	if n == 1 {
		return "1 " + one
	}
	return fmt.Sprintf("%d %s", n, many)
}

// selectSkills returns the named skill, or every skill when name is "".
func selectSkills(name string) ([]*skills.SkillPackage, error) {
	if name != "" {
		s := skills.FindSkill(name)
		if s == nil {
			return nil, fmt.Errorf("unknown skill %q. Available: %s", name, strings.Join(skills.SkillNames(), ", "))
		}
		return []*skills.SkillPackage{s}, nil
	}
	out := make([]*skills.SkillPackage, len(skills.Registry))
	for i := range skills.Registry {
		out[i] = &skills.Registry[i]
	}
	return out, nil
}

// printChanges lists file changes (unchanged files are not listed). dir is
// the display path of the directory the change paths are relative to.
func printChanges(dir string, changes []installer.Change, dryRun bool) {
	for _, c := range changes {
		p := path.Join(dir, c.Path)
		aside := path.Join(dir, c.Aside)
		var msg string
		switch c.Action {
		case installer.ActionCreate:
			msg = fmt.Sprintf(pick(dryRun, "Would create %s", "Created %s"), p)
		case installer.ActionUpdate:
			msg = fmt.Sprintf(pick(dryRun, "Would update %s", "Updated %s"), p)
		case installer.ActionKeepNew:
			msg = fmt.Sprintf(pick(dryRun,
				"Would keep %s (modified by you) and save the new version as %s",
				"Kept %s (modified by you); new version saved as %s"), p, aside)
		case installer.ActionKeep:
			msg = fmt.Sprintf("Kept %s (modified by you; no new changes to merge)", p)
		case installer.ActionReplace:
			msg = fmt.Sprintf(pick(dryRun,
				"Would replace %s (saving your version as %s)",
				"Replaced %s (your version saved as %s)"), p, aside)
		case installer.ActionRemove:
			msg = fmt.Sprintf(pick(dryRun, "Would remove %s", "Removed %s"), p)
		case installer.ActionKeepRemoved:
			msg = fmt.Sprintf(pick(dryRun,
				"Would keep %s (modified since install, so not removed)",
				"Kept %s (modified since install, so not removed)"), p)
		default:
			continue
		}
		_, _ = fmt.Fprintf(stdout, "  %s\n", msg)
	}
}

func pick(cond bool, a, b string) string {
	if cond {
		return a
	}
	return b
}

// summarize counts a result's changes, e.g. "2 updated, 1 kept (see .new), 40 unchanged".
func summarize(res *installer.Result) string {
	labels := []struct {
		action installer.Action
		label  string
	}{
		{installer.ActionCreate, "created"},
		{installer.ActionUpdate, "updated"},
		{installer.ActionReplace, "replaced (backup saved as .bak)"},
		{installer.ActionKeepNew, "kept (new version saved as .new)"},
		{installer.ActionKeep, "kept as modified"},
		{installer.ActionRemove, "removed"},
		{installer.ActionKeepRemoved, "kept (modified, not removed)"},
		{installer.ActionUnchanged, "unchanged"},
	}
	var parts []string
	for _, l := range labels {
		if n := res.Count(l.action); n > 0 {
			parts = append(parts, fmt.Sprintf("%d %s", n, l.label))
		}
	}
	if len(parts) == 0 {
		return "nothing to do"
	}
	return strings.Join(parts, ", ")
}

// printResult prints the changes of one Install call and a summary line.
func printResult(target *targets.AITarget, res *installer.Result, dryRun bool) {
	printChanges(target.Display(res.Dir), res.Files, dryRun)
	if res.WorkflowDir != "" {
		printChanges(target.Display(res.WorkflowDir), res.Workflows, dryRun)
	}
	if res.Count(installer.ActionUnchanged) == len(res.Files)+len(res.Workflows) {
		_, _ = fmt.Fprintf(stdout, "✓ %s is up to date (%s)\n", res.Skill, target.Display(res.Dir+"/"))
		return
	}
	_, _ = fmt.Fprintf(stdout, "✓ %s: %s\n", res.Skill, summarize(res))
}

// printMergeHint explains .new and .bak files when any were written.
func printMergeHint(results []*installer.Result, dryRun bool) {
	kept, replaced := 0, 0
	for _, r := range results {
		kept += r.Count(installer.ActionKeepNew)
		replaced += r.Count(installer.ActionReplace)
	}
	if dryRun {
		return
	}
	if kept > 0 {
		_, _ = fmt.Fprintf(stdout, "\nNote: %s you modified %s kept. See what changed with 'think-better diff' and merge,\n"+
			"or rerun with --force to take the new versions (yours are saved as .bak).\n", plural(kept, "file", "files"), pick(kept == 1, "was", "were"))
	}
	if replaced > 0 {
		_, _ = fmt.Fprintf(stdout, "\nNote: %s you modified %s replaced; %s saved as .bak.\n",
			plural(replaced, "file", "files"), pick(replaced == 1, "was", "were"), pick(replaced == 1, "your version is", "your versions are"))
	}
}
