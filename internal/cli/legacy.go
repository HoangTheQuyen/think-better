package cli

import (
	"fmt"
	"os"
	"path"
	"path/filepath"

	"github.com/HoangTheQuyen/think-better/internal/installer"
	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// Earlier releases installed some skills where the AI tool does not load
// them (Copilot: .github/prompts/<skill>/ instead of .github/skills/<skill>/).
// Such installs are reported as outdated, and update (or init) moves them.

// findLegacyLocations looks for a skill at the old install locations of
// every target in the project. A location counts when it holds the skill's
// manifest or its SKILL.md.
func findLegacyLocations(skill *skills.SkillPackage, projectDir string) []skillLocation {
	var found []skillLocation
	for i := range targets.Targets {
		for _, lt := range targets.Targets[i].Legacy() {
			if loc, ok := legacyLocation(skill, lt, projectDir); ok {
				found = append(found, loc)
			}
		}
	}
	return found
}

// legacyLocation checks one old location (lt from Target.Legacy()).
func legacyLocation(skill *skills.SkillPackage, lt *targets.AITarget, projectDir string) (skillLocation, bool) {
	dir := filepath.Join(projectDir, filepath.FromSlash(lt.InstallDir(skill.Name)))
	if !fileExists(filepath.Join(dir, installer.SkillManifestName)) && !fileExists(filepath.Join(dir, "SKILL.md")) {
		return skillLocation{}, false
	}
	st, err := installer.CheckStatus(skill, lt, projectDir, Version())
	if err != nil || st.Status == installer.StatusNotInstalled {
		return skillLocation{}, false
	}
	// Wherever its files stand, the install needs moving.
	st.Outdated = true
	if st.Status != installer.StatusIncomplete {
		st.Status = installer.StatusOutdated
	}
	return skillLocation{
		Label:  lt.Name + " (old location)",
		Target: lt,
		Base:   projectDir,
		Path:   lt.Display(lt.InstallDir(skill.Name)),
		Status: st,
	}, true
}

// legacyLocationsFor returns the old locations of one project target that
// hold the skill.
func legacyLocationsFor(skill *skills.SkillPackage, target *targets.AITarget, projectDir string) []skillLocation {
	var found []skillLocation
	for _, lt := range target.Legacy() {
		if loc, ok := legacyLocation(skill, lt, projectDir); ok {
			found = append(found, loc)
		}
	}
	return found
}

func fileExists(p string) bool {
	_, err := os.Stat(p)
	return err == nil
}

// migrateLocation moves a skill from an old location (loc) to the target's
// install directory and brings it up to date there, printing what happens.
func migrateLocation(skill *skills.SkillPackage, loc skillLocation, opts installer.Options) (*installer.Result, error) {
	target := targets.FindTarget(loc.Target.Name)
	inst := installer.NewInstaller(loc.Base, Version())
	m, err := inst.MigrateLegacy(skill, loc.Target, target, opts)
	if err != nil {
		return nil, err
	}
	from, to := loc.Target.Display(m.From)+"/", target.Display(m.To)+"/"
	_, _ = fmt.Fprintf(stdout, "%s skill %q from %s to %s (where %s loads skills)...\n",
		pick(opts.DryRun, "Would move", "Moving"), skill.Name, from, to, target.DisplayName)
	for _, rel := range m.Moved {
		_, _ = fmt.Fprintf(stdout, "  %s %s to %s (modified by you)\n",
			pick(opts.DryRun, "Would move", "Moved"), path.Join(m.From, rel), path.Join(m.To, rel))
	}
	for _, rel := range m.Kept {
		_, _ = fmt.Fprintf(stdout, "  Kept %s (modified by you; %s already exists, merge them yourself)\n",
			path.Join(m.From, rel), path.Join(m.To, rel))
	}
	if n := len(m.Removed); n > 0 {
		_, _ = fmt.Fprintf(stdout, "  %s %s from %s (installed anew below)\n",
			pick(opts.DryRun, "Would remove", "Removed"), plural(n, "unmodified file", "unmodified files"), from)
	}
	if m.DirRemoved {
		_, _ = fmt.Fprintf(stdout, "  Removed %s\n", from)
	} else if !opts.DryRun {
		_, _ = fmt.Fprintf(stdout, "  Kept %s (it still holds files you added or modified)\n", from)
	}

	res, err := inst.Install(skill, target, opts)
	if err != nil {
		return nil, err
	}
	printResult(target, res, opts.DryRun)
	return res, nil
}
