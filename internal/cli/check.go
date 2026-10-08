package cli

import (
	"fmt"
	"strings"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
)

const checkUsage = `
Verify prerequisites and the state of installed skills.

Checks that Python 3 is available for the analysis scripts (bias detection,
framework search, data processing), and reports each installed skill, in
every AI tool, in this project and in your user account, as installed,
outdated, modified (you edited files) or incomplete.

Exits 1 when Python 3 is missing or an install is incomplete, and with
--strict also when an install is outdated. Skills that are not installed
anywhere are reported but are not an error.

Usage:
  think-better check [--json] [--strict]`

type checkOutput struct {
	OK     bool         `json:"ok"`
	Python pythonJSON   `json:"python"`
	Skills []checkSkill `json:"skills"`
}

type pythonJSON struct {
	Found   bool   `json:"found"`
	Version string `json:"version,omitempty"`
	Path    string `json:"path,omitempty"`
}

type checkSkill struct {
	Name      string         `json:"name"`
	Installed bool           `json:"installed"`
	Locations []locationJSON `json:"locations"`
}

// RunCheck handles the "check" subcommand.
func RunCheck(args []string) int {
	flags := newFlagSet("check")
	jsonFlag := flags.Bool("json", false, "Output JSON")
	strict := flags.Bool("strict", false, "Also fail when an installed skill is outdated")
	if ok, code := parseFlags(flags, args, checkUsage); !ok {
		return code
	}

	cwd, err := currentProject()
	if err != nil {
		Errorf("%v", err)
		return 1
	}

	py := checkPython()
	out := checkOutput{Python: pythonJSON{Found: py.Found, Version: py.Version, Path: py.Path}, Skills: []checkSkill{}}
	var lines []string
	problems := 0
	if py.Found {
		lines = append(lines, fmt.Sprintf("  ✓ Python %s found at %s", py.Version, py.Path))
	} else {
		lines = append(lines, "  ✗ Python 3 not found", "    Install from https://python.org or your package manager")
		problems++
	}

	home := userHome()
	for i := range skills.Registry {
		skill := &skills.Registry[i]
		entry := checkSkill{Name: skill.Name, Locations: []locationJSON{}}
		locations := findSkillLocations(skill, cwd, home)
		if len(locations) == 0 {
			lines = append(lines, fmt.Sprintf("  - Skill %q not installed (install with: think-better init --skill %s)", skill.Name, skill.Name))
		}
		for _, loc := range locations {
			entry.Installed = true
			entry.Locations = append(entry.Locations, toLocationJSON(loc))
			st := loc.Status
			where := fmt.Sprintf("for %s (%s)", loc.Label, loc.Path)
			fix := updateCommand(skill.Name, loc)
			switch {
			case st.Status == installer.StatusIncomplete:
				lines = append(lines, fmt.Sprintf("  ✗ Skill %q incomplete %s: %s missing (fix with: %s)",
					skill.Name, where, plural(len(st.Missing), "file", "files"), fix))
				problems++
			case st.Outdated:
				lines = append(lines, fmt.Sprintf("  ⚠ Skill %q %s %s (update with: %s)", skill.Name, statusLabel(st), where, fix))
				if *strict {
					problems++
				}
			case len(st.Modified) > 0:
				lines = append(lines, fmt.Sprintf("  ✓ Skill %q installed %s, %s by you", skill.Name, where, plural(len(st.Modified), "file", "files")+" modified"))
			default:
				lines = append(lines, fmt.Sprintf("  ✓ Skill %q installed %s", skill.Name, where))
			}
		}
		out.Skills = append(out.Skills, entry)
	}
	out.OK = problems == 0

	code := 0
	if problems > 0 {
		code = 1
	}
	if *jsonFlag {
		if printJSON(out) != 0 {
			return 1
		}
		return code
	}

	_, _ = fmt.Fprintln(stdout, "Checking prerequisites...")
	_, _ = fmt.Fprintln(stdout, strings.Join(lines, "\n"))
	if problems > 0 {
		_, _ = fmt.Fprintf(stdout, "\n%s found\n", plural(problems, "problem", "problems"))
		return code
	}
	_, _ = fmt.Fprintln(stdout, "\n✓ All prerequisites met")
	return code
}

// updateCommand is the command that brings one location up to date.
func updateCommand(skill string, loc skillLocation) string {
	cmd := fmt.Sprintf("think-better update --ai %s --skill %s", loc.Target.Name, skill)
	if loc.Global() {
		cmd += " --global"
	}
	return cmd
}
