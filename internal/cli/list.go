package cli

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/htrbao/think-better/internal/installer"
	"github.com/htrbao/think-better/internal/skills"
	"github.com/htrbao/think-better/internal/targets"
)

type listOutput struct {
	Skills []listSkill `json:"skills"`
}

type listSkill struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	FileCount   int    `json:"fileCount"`
	Status      string `json:"status"`
	InstallPath string `json:"installPath"`
}

// RunList handles the "list" subcommand.
func RunList(args []string) int {
	fs := flag.NewFlagSet("list", flag.ContinueOnError)
	jsonFlag := fs.Bool("json", false, "Output JSON instead of table")

	fs.Usage = func() {
		fmt.Fprintln(os.Stderr, `Show available decision-making frameworks and problem-solving skills.

Lists all bundled AI assistant skills with installation status, file counts,
and descriptions. Use --json for programmatic parsing.

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

	// Use first target for status check (both use same path pattern)
	defaultTarget := &targets.Targets[0]

	var entries []listSkill
	for _, skill := range skills.Registry {
		files, _ := skills.SkillFiles(skill.Name)
		fileCount := len(files)

		status, err := installer.CheckStatus(&skill, defaultTarget, cwd)
		statusStr := "not-installed"
		installPath := ""
		if err == nil {
			statusStr = string(status.Status)
			if status.Status != installer.StatusNotInstalled {
				installPath = defaultTarget.InstallDir(skill.Name)
			}
		}

		entries = append(entries, listSkill{
			Name:        skill.Name,
			Description: skill.Description,
			FileCount:   fileCount,
			Status:      statusStr,
			InstallPath: installPath,
		})
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
	fmt.Fprintln(w, "SKILL\tDESCRIPTION\tFILES\tSTATUS")
	for _, e := range entries {
		fmt.Fprintf(w, "%s\t%s\t%d\t%s\n", e.Name, e.Description, e.FileCount, e.Status)
	}
	w.Flush()
	return 0
}
