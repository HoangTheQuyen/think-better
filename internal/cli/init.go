package cli

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path"
	"path/filepath"
	"slices"
	"sort"
	"strings"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
)

const initUsage = `
Install decision-making frameworks and problem-solving skills for AI assistants.

Installs the skills and their slash commands for Claude Code, GitHub Copilot,
Antigravity or OpenCode. Running init again updates an existing install, like
'think-better update': files you modified are kept and the new version is
saved next to them as <file>.new. With --force they are replaced, and your
version is saved as <file>.bak first.

Use --global to install for your user account so every project can use the
skills (supported for claude, opencode and antigravity).

Usage:
  think-better init [--ai <target>] [--skill <name>] [--global] [--force] [--dry-run]`

// RunInit handles the "init" subcommand.
func RunInit(args []string) int {
	flags := newFlagSet("init")
	var sf SharedFlags
	AddSharedFlags(flags, &sf, "Replace files you modified (your version is saved as <file>.bak)")
	flags.BoolVar(&sf.DryRun, "dry-run", false, "Show what would change without writing anything")
	if ok, code := parseFlags(flags, args, initUsage); !ok {
		return code
	}

	target, err := resolveTarget(sf.AI)
	if err != nil {
		Errorf("%v", err)
		return 1
	}
	ai := target.Name
	skillsToInstall, err := selectSkills(sf.Skill)
	if err != nil {
		Errorf("%v", err)
		return 1
	}
	target, baseDir, err := ResolveInstallScope(target, sf.Global)
	if err != nil {
		Errorf("%v", err)
		return 1
	}

	// Copilot installs into .github/, which a project may not have yet
	if ai == "copilot" && !target.IsGlobal() && !sf.DryRun {
		if _, err := os.Stat(filepath.Join(baseDir, ".github")); errors.Is(err, fs.ErrNotExist) {
			_, _ = fmt.Fprintln(stderr, "warning: .github/ directory does not exist (will be created)")
		}
	}

	inst := installer.NewInstaller(baseDir, Version())
	opts := installer.Options{Force: sf.Force, DryRun: sf.DryRun}
	var results []*installer.Result
	hasError := false
	for i, skill := range skillsToInstall {
		res, err := inst.Install(skill, target, opts)
		if i > 0 {
			_, _ = fmt.Fprintln(stdout)
		}
		if err != nil {
			Errorf("%v", err)
			hasError = true
			continue
		}
		verb := "Installing"
		if res.Existing {
			verb = "Updating"
		}
		_, _ = fmt.Fprintf(stdout, "%s skill %q for %s (%s)...\n", verb, skill.Name, ai, target.Display(target.InstallDir(skill.Name)))
		printResult(target, res, sf.DryRun)
		results = append(results, res)
	}
	printMergeHint(results, sf.DryRun)

	if hasError {
		return 1
	}
	if sf.DryRun {
		_, _ = fmt.Fprintln(stdout, "\nDry run: nothing was changed.")
		return 0
	}

	changed := 0
	for _, r := range results {
		changed += r.Count(installer.ActionCreate, installer.ActionUpdate, installer.ActionReplace)
	}
	if changed == 0 {
		return 0
	}

	installed := make([]string, len(skillsToInstall))
	for i, s := range skillsToInstall {
		installed[i] = s.Name
	}
	_, _ = fmt.Fprintln(stdout, "\nNext steps:")
	if target.IsGlobal() {
		_, _ = fmt.Fprintln(stdout, "  - Installed for your user account: available in every project")
	}
	switch ai {
	case "antigravity":
		_, _ = fmt.Fprintln(stdout, "  - Skills installed as Antigravity skills (SKILL.md entry points)")
	case "opencode":
		_, _ = fmt.Fprintln(stdout, "  - Skills installed as OpenCode skills (SKILL.md entry points)")
	}
	for _, s := range skillsToInstall {
		_, _ = fmt.Fprintf(stdout, "  - Skill %q is available in %s\n", s.Name, target.Display(target.InstallDir(s.Name)))
	}
	switch ai {
	case "antigravity":
		printSlashCommands("Workflows installed", installed)
	case "opencode":
		_, _ = fmt.Fprintln(stdout, "  - OpenCode will auto-discover skills via the native skill tool")
		printSlashCommands("Slash commands installed", installed)
	default:
		printSlashCommands("Slash commands installed", installed)
	}
	if ai == "copilot" {
		_, _ = fmt.Fprintln(stdout, "  - Use them in Copilot Chat (agent mode) by typing / and the command name")
	}

	if py := checkPython(); py.Found {
		_, _ = fmt.Fprintf(stdout, "  - Python %s available for skill scripts\n", py.Version)
	} else {
		_, _ = fmt.Fprintln(stdout, "  - Python 3 is required for skill scripts")
	}
	return 0
}

// printSlashCommands lists the workflows for the installed skills as slash
// commands, one line per group (/code, /code.debug, ... then /decide, ...).
func printSlashCommands(label string, installed []string) {
	files, err := skills.WorkflowFiles()
	if err != nil {
		return
	}
	groups := map[string][]string{}
	var order []string
	for _, f := range files {
		if !slices.Contains(installed, skills.WorkflowSkill(f)) {
			continue
		}
		name := strings.TrimSuffix(path.Base(f), ".md")
		group, _, _ := strings.Cut(name, ".")
		if _, ok := groups[group]; !ok {
			order = append(order, group)
		}
		groups[group] = append(groups[group], "/"+name)
	}
	sort.Strings(order)
	for _, group := range order {
		cmds := groups[group]
		sort.Strings(cmds)
		_, _ = fmt.Fprintf(stdout, "  - %s: %s\n", label, strings.Join(cmds, ", "))
	}
}
