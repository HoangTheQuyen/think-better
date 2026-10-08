// Package installer provides skill installation, update, uninstallation and
// status checking, driven by per-location manifests (see manifest.go).
package installer

import (
	"encoding/json"
	"errors"
	"io/fs"
	"os"
	"path"
	"path/filepath"

	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// Status represents the installation state of a skill in one location.
type Status string

const (
	// StatusInstalled: every file is present and matches this version.
	StatusInstalled Status = "installed"
	// StatusOutdated: installed by an older version, or content differs from this version.
	StatusOutdated Status = "outdated"
	// StatusModified: up to date, but the user edited some files.
	StatusModified Status = "modified"
	// StatusIncomplete: files that were installed are missing.
	StatusIncomplete Status = "incomplete"
	// StatusNotInstalled: nothing of the skill is there.
	StatusNotInstalled Status = "not-installed"
)

// InstallStatus describes a skill install in one location.
type InstallStatus struct {
	SkillName   string
	TargetName  string
	InstallPath string // resolved absolute path of the install directory
	// Status is the overall state; when several apply, incomplete wins over
	// outdated, which wins over modified. Outdated and Modified give the detail.
	Status      Status
	Version     string   // version recorded in the manifest ("" without one)
	HasManifest bool     // false for installs made before manifests existed
	Outdated    bool     // an update would change files
	Modified    []string // files the user changed (slash paths relative to the base)
	Missing     []string // installed files that are gone (slash paths relative to the base)
}

// readFollow reads a file for status checks (symlinks are followed: reading
// is harmless, and writes refuse them later). nil means it does not exist.
func readFollow(full string) []byte {
	data, err := os.ReadFile(full)
	if err != nil {
		return nil
	}
	if data == nil {
		data = []byte{}
	}
	return data
}

// CheckStatus computes the installation status of a skill for target under
// baseDir. version is the running think-better version: a manifest written
// by an older release makes the install outdated.
func CheckStatus(skill *skills.SkillPackage, target *targets.AITarget, baseDir, version string) (*InstallStatus, error) {
	dirRel := skillDir(target, skill.Name)
	installDir := filepath.Join(baseDir, filepath.FromSlash(dirRel))
	absPath, err := filepath.Abs(installDir)
	if err != nil {
		absPath = installDir
	}
	st := &InstallStatus{SkillName: skill.Name, TargetName: target.Name, InstallPath: absPath}

	desired, err := desiredSkillFiles(skill.Name, target)
	if err != nil {
		return nil, err
	}
	m := loadSkillManifest(filepath.Join(installDir, SkillManifestName))
	var recorded map[string]string
	if m != nil {
		recorded = m.Files
		st.HasManifest = true
		st.Version = m.Version
		if versionOlder(m.Version, version) {
			st.Outdated = true
		}
	}

	present := compare(st, baseDir, dirRel, desired, recorded, false)
	if m == nil && present == 0 {
		st.Status = StatusNotInstalled
		return st, nil
	}

	if wfDir := workflowDir(target); wfDir != "" {
		wdesired, err := desiredWorkflows(skill.Name, target)
		if err != nil {
			return nil, err
		}
		wm := loadWorkflowManifest(filepath.Join(baseDir, filepath.FromSlash(wfDir), WorkflowManifestName))
		compare(st, baseDir, wfDir, wdesired, workflowEntries(wm, skill.Name), true)
	}

	switch {
	case len(st.Missing) > 0:
		st.Status = StatusIncomplete
	case st.Outdated:
		st.Status = StatusOutdated
	case len(st.Modified) > 0:
		st.Status = StatusModified
	default:
		st.Status = StatusInstalled
	}
	return st, nil
}

// compare checks the files of dirRel against the desired content and the
// manifest hashes (recorded, nil without a manifest), filling st. It returns
// how many of the files are present. For workflows without a manifest entry,
// a missing file only makes the install outdated (an update adds it).
func compare(st *InstallStatus, base, dirRel string, desired map[string][]byte, recorded map[string]string, workflows bool) int {
	present := 0
	seen := map[string]bool{}
	names := append(sortedKeys(desired), sortedKeys(recorded)...)
	for _, rel := range names {
		if seen[rel] {
			continue
		}
		seen[rel] = true
		shown := path.Join(dirRel, rel)
		want, shipped := desired[rel]
		rec, hasRec := recorded[rel]
		cur := readFollow(filepath.Join(base, filepath.FromSlash(shown)))

		if cur == nil {
			switch {
			case hasRec || (recorded == nil && !workflows):
				st.Missing = append(st.Missing, shown) // was installed, now gone
			case shipped:
				st.Outdated = true // new in this version
			}
			continue
		}
		present++
		curHash := hashBytes(cur)
		switch {
		case hasRec:
			if curHash != rec {
				st.Modified = append(st.Modified, shown)
			}
			if !shipped || rec != hashBytes(want) {
				st.Outdated = true
			}
		case recorded == nil:
			// Legacy install: anything that differs from this version counts as modified.
			if curHash != hashBytes(want) {
				st.Modified = append(st.Modified, shown)
			}
		default:
			// Present but not in the manifest: written by someone else, and
			// an update would offer this version next to it.
			if curHash != hashBytes(want) {
				st.Modified = append(st.Modified, shown)
			}
			st.Outdated = true
		}
	}
	return present
}

// loadSkillManifest reads a skill manifest for status checks; nil if absent or invalid.
func loadSkillManifest(full string) *SkillManifest {
	data := readFollow(full)
	var m SkillManifest
	if data == nil || json.Unmarshal(data, &m) != nil {
		return nil
	}
	if m.Files == nil {
		m.Files = map[string]string{}
	}
	for rel := range m.Files {
		if !validRel(rel) {
			delete(m.Files, rel)
		}
	}
	return &m
}

// loadWorkflowManifest reads a workflow manifest for status checks; nil if absent or invalid.
func loadWorkflowManifest(full string) *WorkflowManifest {
	data := readFollow(full)
	var m WorkflowManifest
	if data == nil || json.Unmarshal(data, &m) != nil {
		return nil
	}
	for rel := range m.Files {
		if !validRel(rel) {
			delete(m.Files, rel)
		}
	}
	return &m
}

// exists reports whether a path exists (without following a final symlink).
func exists(full string) bool {
	_, err := os.Lstat(full)
	return !errors.Is(err, fs.ErrNotExist)
}
