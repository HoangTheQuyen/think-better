package cli

import (
	"encoding/json"
	"fmt"
	"io"
	"strings"
	"text/tabwriter"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
)

type listOutput struct {
	Skills []listSkill `json:"skills"`
}

type listSkill struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	FileCount   int    `json:"fileCount"`
	// Status is "installed" when at least one location is usable (installed,
	// outdated or modified), "incomplete" when every location is incomplete,
	// else "not-installed". Locations has the per-location detail.
	Status      string         `json:"status"`
	InstallPath string         `json:"installPath"`
	InstalledIn []string       `json:"installedIn"`
	Locations   []locationJSON `json:"locations"`
}

// locationJSON is one install location in list and check JSON output.
type locationJSON struct {
	Target   string   `json:"target"`
	Scope    string   `json:"scope"` // "project" or "global"
	Path     string   `json:"path"`
	Status   string   `json:"status"` // installed, outdated, modified, incomplete
	Version  string   `json:"version,omitempty"`
	Manifest bool     `json:"manifest"`
	Outdated bool     `json:"outdated"`
	Modified []string `json:"modified"`
	Missing  []string `json:"missing"`
}

func toLocationJSON(loc skillLocation) locationJSON {
	st := loc.Status
	scope := "project"
	if loc.Global() {
		scope = "global"
	}
	display := func(paths []string) []string {
		out := make([]string, len(paths))
		for i, p := range paths {
			out[i] = loc.Target.Display(p)
		}
		return out
	}
	return locationJSON{
		Target:   loc.Target.Name,
		Scope:    scope,
		Path:     loc.Path,
		Status:   string(st.Status),
		Version:  st.Version,
		Manifest: st.HasManifest,
		Outdated: st.Outdated,
		Modified: display(st.Modified),
		Missing:  display(st.Missing),
	}
}

const listUsage = `
Show available decision-making frameworks and problem-solving skills.

Lists all bundled AI assistant skills with file counts, descriptions and
where they are installed, in every AI tool, in this project and in your user
account (--global installs). Each location is marked when it is outdated
(run 'think-better update'), has files you modified, or is incomplete.
Use --json for programmatic parsing.

Usage:
  think-better list [--json]`

// RunList handles the "list" subcommand.
func RunList(args []string) int {
	flags := newFlagSet("list")
	jsonFlag := flags.Bool("json", false, "Output JSON instead of table")
	if ok, code := parseFlags(flags, args, listUsage); !ok {
		return code
	}

	cwd, err := currentProject()
	if err != nil {
		Errorf("%v", err)
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
			Locations:   []locationJSON{},
		}
		for _, loc := range findSkillLocations(skill, cwd, home) {
			label := loc.Label
			if loc.Status.Status != installer.StatusInstalled {
				label += " [" + statusLabel(loc.Status) + "]"
			}
			if loc.Status.Status != installer.StatusIncomplete {
				entry.Status = string(installer.StatusInstalled)
			}
			if entry.InstallPath == "" {
				entry.InstallPath = loc.Path
			}
			entry.InstalledIn = append(entry.InstalledIn, label)
			entry.Locations = append(entry.Locations, toLocationJSON(loc))
		}
		if entry.Status != string(installer.StatusInstalled) && len(entry.InstalledIn) > 0 {
			entry.Status = string(installer.StatusIncomplete)
		}
		entries = append(entries, entry)
	}

	if *jsonFlag {
		return printJSON(listOutput{Skills: entries})
	}
	return printListTable(entries)
}

// printJSON writes v as indented JSON to stdout, without HTML escaping.
func printJSON(v any) int {
	if err := encodeJSON(stdout, v); err != nil {
		Errorf("encoding JSON: %v", err)
		return 1
	}
	return 0
}

func encodeJSON(w io.Writer, v any) error {
	enc := json.NewEncoder(w)
	enc.SetEscapeHTML(false)
	enc.SetIndent("", "  ")
	return enc.Encode(v)
}

func printListTable(entries []listSkill) int {
	w := tabwriter.NewWriter(stdout, 0, 0, 4, ' ', 0)
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
