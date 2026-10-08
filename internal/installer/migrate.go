package installer

import (
	"bytes"
	"fmt"
	"path"
	"path/filepath"

	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// MigrateResult describes how MigrateLegacy moved a skill out of a location
// used by an earlier release (paths are slash paths relative to From/To).
type MigrateResult struct {
	Skill      string
	From       string   // old install directory, relative to the base
	To         string   // new install directory, relative to the base
	Removed    []string // unmodified files deleted (the new install recreates them)
	Moved      []string // files the user modified, moved to the new location
	Kept       []string // modified files left at the old location: the new one already has a different file there
	DirRemoved bool     // the old directory was removed
}

// MigrateLegacy moves skill from legacy (a variant from target.Legacy()) to
// target's install directory, before Install brings it up to date there:
//
//   - files unchanged since install are deleted; Install writes them anew
//   - files the user modified are moved to the new directory, where Install
//     treats them like any modified file (kept, with the new version saved as
//     <file>.new, or replaced with --force after a .bak backup)
//   - a modified file is left in place when the new directory already holds
//     a different file with that name
//   - <file>.new files from an earlier update are deleted when they hold the
//     version that was offered; files think-better did not install are left
//
// The old manifest is removed, and so is the old directory once it is empty.
// With opts.DryRun nothing is written. It returns ErrNotInstalled when
// nothing of the skill is at the legacy location.
func (inst *Installer) MigrateLegacy(skill *skills.SkillPackage, legacy, target *targets.AITarget, opts Options) (*MigrateResult, error) {
	base := inst.BaseDir
	res := &MigrateResult{Skill: skill.Name, From: skillDir(legacy, skill.Name), To: skillDir(target, skill.Name)}
	if res.From == res.To {
		return nil, fmt.Errorf("skill %q: legacy location %s is the install location", skill.Name, res.From)
	}

	desired, err := desiredSkillFiles(skill.Name, legacy)
	if err != nil {
		return nil, err
	}
	m, err := readSkillManifest(base, res.From)
	if err != nil {
		return nil, fmt.Errorf("skill %q: %w", skill.Name, err)
	}
	known := manifestHashes(desired) // no manifest: what this version would have written there
	if m != nil {
		known = m.Files
	}

	type move struct {
		rel  string
		data []byte
	}
	var removes []string
	var moves []move
	found := m != nil
	for _, rel := range sortedKeys(known) {
		cur, err := readRegular(base, path.Join(res.From, rel))
		if err != nil {
			return nil, fmt.Errorf("skill %q: %w", skill.Name, err)
		}
		want, shipped := desired[rel]
		unmodified := func(data []byte) bool {
			h := hashBytes(data)
			return h == known[rel] || (shipped && bytes.Equal(data, want))
		}
		if cur != nil {
			found = true
			dest, err := readRegular(base, path.Join(res.To, rel))
			if err != nil {
				return nil, fmt.Errorf("skill %q: %w", skill.Name, err)
			}
			switch {
			case unmodified(cur), dest != nil && bytes.Equal(dest, cur):
				removes = append(removes, rel)
				res.Removed = append(res.Removed, rel)
			case dest == nil:
				moves = append(moves, move{rel, cur})
				res.Moved = append(res.Moved, rel)
			default:
				res.Kept = append(res.Kept, rel)
			}
		}
		side := rel + ".new"
		data, err := readRegular(base, path.Join(res.From, side))
		if err != nil {
			return nil, fmt.Errorf("skill %q: %w", skill.Name, err)
		}
		if data != nil && unmodified(data) {
			removes = append(removes, side)
		}
	}
	if !found {
		return nil, fmt.Errorf("skill %q is %w at %s", skill.Name, ErrNotInstalled, legacy.Display(legacy.InstallDir(skill.Name)))
	}
	if opts.DryRun {
		return res, nil
	}

	for _, mv := range moves {
		if err := writeFileSafe(base, path.Join(res.To, mv.rel), mv.data, fileMode(mv.rel)); err != nil {
			return res, fmt.Errorf("moving %s: %w", path.Join(res.From, mv.rel), err)
		}
		removes = append(removes, mv.rel)
	}
	for _, rel := range removes {
		full := path.Join(res.From, rel)
		if err := removeFileSafe(base, full); err != nil {
			return res, fmt.Errorf("removing %s: %w", full, err)
		}
		removeEmptyDirs(base, path.Dir(full), res.From)
	}
	if err := removeFileSafe(base, path.Join(res.From, SkillManifestName)); err != nil {
		return res, fmt.Errorf("removing old manifest: %w", err)
	}
	// Stop below the legacy skills root: it may hold other files (Copilot
	// prompt files live next to the old skill directories).
	removeEmptyDirs(base, res.From, path.Dir(res.From))
	res.DirRemoved = !exists(filepath.Join(base, filepath.FromSlash(res.From)))
	return res, nil
}
