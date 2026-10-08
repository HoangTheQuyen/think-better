package cli

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
)

type listOutput struct {
	Skills []listSkill `json:"skills"`
}

type listSkill struct {
	Name        string   `json:"name"`
	Description string   `json:"description"`
	FileCount   int      `json:"fileCount"`
	Status      string   `json:"status"`
	InstallPath string   `json:"installPath"`
	InstalledIn []string `json:"installedIn"`
}

// RunList handles the "list" subcommand.
func RunList(args []string) int {
	fs := flag.NewFlagSet("list", flag.ContinueOnError)
	jsonFlag := fs.Bool("json", false, "Output JSON instead of table")

	fs.Usage = func() {
		fmt.Fprintln(os.Stderr, `Show available decision-making frameworks and problem-solving skills.

Lists all bundled AI assistant skills with installation status, file counts,
and descriptions. Status covers every AI tool, in this project and in your
user account (--global installs). Use --json for programmatic parsing.

Usage:
  think-better list [--json]

Flags:`)
		fs.PrintDefaults()
	}

	if err := fs.Parse(args); err != nil {
		return 1
	}

	cwd, err := os.Getwd()
	if err != nil {
		Errorf("getting working directory: %v", err)
		return 1
	}

	home := userHome()
	var entries []listSkill
	for i := range skills.Registry {
		skill := &skills.Registry[i]
		files, _ := skills.SkillFiles(skill.Name)

		entry := listSkill{
			Name:        skill.Name,
			Description: skill.Description,
			FileCount:   len(files),
			Status:      string(installer.StatusNotInstalled),
			InstalledIn: []string{},
		}
		for _, loc := range findSkillLocations(skill, cwd, home) {
			label := loc.Label
			if loc.Status == installer.StatusIncomplete {
				label += " [incomplete]"
			} else {
				entry.Status = string(installer.StatusInstalled)
			}
			if entry.InstallPath == "" {
				entry.InstallPath = loc.Path
			}
			entry.InstalledIn = append(entry.InstalledIn, label)
		}
		if entry.Status != string(installer.StatusInstalled) && len(entry.InstalledIn) > 0 {
			entry.Status = string(installer.StatusIncomplete)
		}
		entries = append(entries, entry)
	}

	if *jsonFlag {
		return printListJSON(entries)
	}
	return printListTable(entries)
}

func printListJSON(entries []listSkill) int {
	out := listOutput{Skills: entries}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(out); err != nil {
		Errorf("encoding JSON: %v", err)
		return 1
	}
	return 0
}

func printListTable(entries []listSkill) int {
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 4, ' ', 0)
	_, _ = fmt.Fprintln(w, "SKILL\tDESCRIPTION\tFILES\tINSTALLED IN")
	for _, e := range entries {
		where := "-"
		if len(e.InstalledIn) > 0 {
			where = strings.Join(e.InstalledIn, ", ")
		}
		_, _ = fmt.Fprintf(w, "%s\t%s\t%d\t%s\n", e.Name, e.Description, e.FileCount, where)
	}
	if err := w.Flush(); err != nil {
		Errorf("writing output: %v", err)
		return 1
	}
	return 0
}
