package cli

import (
	"bytes"
	"fmt"
	"os"
	"path"
	"path/filepath"
	"strings"

	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
	"github.com/HoangTheQuyen/think-better/internal/textdiff"
)

const diffUsage = `
Show the changes waiting to be merged into files you modified.

When init or update finds a skill file or slash command you modified, it
keeps yours and saves the new version next to it as <file>.new. diff shows,
for every such file, in this project and in your user account, a unified
diff from your version (---) to the new one (+++).

Then, for each file:
  take the new version:  mv <file>.new <file>
  keep yours:            rm <file>.new
or take every new version with 'think-better update --force' (yours are
saved as <file>.bak).

Usage:
  think-better diff [--ai <target>] [--skill <name>] [--global] [--context <lines>]`

// RunDiff handles the "diff" subcommand.
func RunDiff(args []string) int {
	flags := newFlagSet("diff")
	ai := flags.String("ai", "", "Only installs for this AI target: "+strings.Join(targets.TargetNames(), ", "))
	skillName := flags.String("skill", "", "Only this skill")
	global := flags.Bool("global", false, "Only installs in your user account")
	context := flags.Int("context", 3, "Unchanged `lines` shown around each change")
	if ok, code := parseFlags(flags, args, diffUsage); !ok {
		return code
	}
	var only *targets.AITarget
	if *ai != "" {
		if err := targets.ValidateTarget(*ai); err != nil {
			Errorf("%v", err)
			return 1
		}
		only = targets.FindTarget(*ai)
	}
	if *context < 0 {
		Errorf("--context must not be negative")
		return 1
	}
	selected, err := selectSkills(*skillName)
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

	shown, identical := 0, 0
	seen := map[string]bool{} // workflow directories are shared by skills
	for _, skill := range selected {
		locations := findSkillLocations(skill, cwd, home)
		if !*global {
			locations = append(locations, findLegacyLocations(skill, cwd)...)
		}
		for _, loc := range locations {
			if (only != nil && loc.Target.Name != only.Name) || (*global && !loc.Global()) {
				continue
			}
			for _, rel := range pendingFiles(skill, loc.Target) {
				full := filepath.Join(loc.Base, filepath.FromSlash(rel))
				if seen[full] {
					continue
				}
				seen[full] = true
				newData, err := os.ReadFile(full + ".new")
				if err != nil {
					continue
				}
				mine, err := os.ReadFile(full)
				if err != nil && !os.IsNotExist(err) {
					Errorf("%v", err)
					return 1
				}
				name := loc.Target.Display(rel)
				if bytes.Equal(mine, newData) {
					identical++
					_, _ = fmt.Fprintf(stdout, "%s.new is identical to %s: remove it (rm %s.new)\n\n", name, name, name)
					continue
				}
				shown++
				_, _ = fmt.Fprint(stdout, textdiff.Unified(name+" (yours)", name+".new (new version)", string(mine), string(newData), *context))
				_, _ = fmt.Fprintln(stdout)
			}
		}
	}

	if shown+identical == 0 {
		_, _ = fmt.Fprintln(stdout, "No .new files: nothing is waiting to be merged.")
		return 0
	}
	if shown > 0 {
		_, _ = fmt.Fprintf(stdout, "%s with a new version to merge. For each one:\n", plural(shown, "file", "files"))
		_, _ = fmt.Fprintln(stdout, "  take the new version:  mv <file>.new <file>")
		_, _ = fmt.Fprintln(stdout, "  keep yours:            rm <file>.new")
		_, _ = fmt.Fprintln(stdout, "or take every new version with: think-better update --force (yours are saved as .bak)")
	}
	return 0
}

// pendingFiles lists, as slash paths relative to the install base, the
// files of a skill install that may have a .new version: its skill files
// and the slash commands that run it.
func pendingFiles(skill *skills.SkillPackage, target *targets.AITarget) []string {
	var out []string
	files, _ := skills.SkillFiles(skill.Name)
	dir := path.Clean(target.InstallDir(skill.Name))
	for _, f := range files {
		out = append(out, path.Join(dir, f))
	}
	if !target.HasWorkflows() {
		return out
	}
	workflows, _ := skills.WorkflowFiles()
	wdir := path.Clean(target.WorkflowDir())
	for _, f := range workflows {
		if skills.WorkflowSkill(f) == skill.Name {
			out = append(out, path.Join(wdir, target.WorkflowFileName(f)))
		}
	}
	return out
}
