package installer

import (
	"errors"
	"fmt"
	"path"
	"path/filepath"

	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// ErrNotInstalled is returned by Uninstall when nothing of the skill is installed.
var ErrNotInstalled = errors.New("not installed")

// planRemoval decides, for each file think-better installed in dirRel,
// whether it can be deleted: only when its content still matches the
// manifest (known) or the version this binary would install (desired).
// Modified files are kept. A <file>.new left by an update is deleted too
// when it holds the offered version.
func planRemoval(base, dirRel string, known map[string]string, desired map[string][]byte) ([]plannedOp, bool, error) {
	var ops []plannedOp
	found := false
	for _, rel := range sortedKeys(known) {
		cur, err := readRegular(base, path.Join(dirRel, rel))
		if err != nil {
			return nil, false, err
		}
		if cur == nil {
			continue
		}
		found = true
		h := hashBytes(cur)
		want, shipped := desired[rel]
		action := ActionKeepRemoved
		if h == known[rel] || (shipped && h == hashBytes(want)) {
			action = ActionRemove
		}
		ops = append(ops, plannedOp{Change: Change{Path: rel, Action: action}})

		side := rel + ".new"
		data, err := readRegular(base, path.Join(dirRel, side))
		if err != nil {
			return nil, false, err
		}
		if data != nil && (hashBytes(data) == known[rel] || (shipped && hashBytes(data) == hashBytes(want))) {
			ops = append(ops, plannedOp{Change: Change{Path: side, Action: ActionRemove}})
		}
	}
	return ops, found, nil
}

// Uninstall removes skill (and the workflows that run it) from target.
// Only files whose content is unchanged since install are deleted; files the
// user modified are kept and reported as ActionKeepRemoved. The manifest is
// removed, and so are directories left empty, up to the target's root.
// It returns ErrNotInstalled when there is nothing to remove.
func (inst *Installer) Uninstall(skill *skills.SkillPackage, target *targets.AITarget, opts Options) (*Result, error) {
	base := inst.BaseDir
	res := &Result{Skill: skill.Name, Dir: skillDir(target, skill.Name), WorkflowDir: workflowDir(target)}

	desired, err := desiredSkillFiles(skill.Name, target)
	if err != nil {
		return nil, err
	}
	m, err := readSkillManifest(base, res.Dir)
	if err != nil {
		return nil, fmt.Errorf("skill %q: %w", skill.Name, err)
	}
	known := manifestHashes(desired) // legacy install: what this version would have written
	if m != nil {
		known = m.Files
	}
	ops, found, err := planRemoval(base, res.Dir, known, desired)
	if err != nil {
		return nil, fmt.Errorf("skill %q: %w", skill.Name, err)
	}
	res.Files = changes(ops)

	var wops []plannedOp
	var wm *WorkflowManifest
	if res.WorkflowDir != "" {
		wdesired, err := desiredWorkflows(skill.Name, target)
		if err != nil {
			return nil, err
		}
		if wm, err = readWorkflowManifest(base, res.WorkflowDir); err != nil {
			return nil, fmt.Errorf("workflows for %q: %w", skill.Name, err)
		}
		wknown := workflowEntries(wm, skill.Name)
		if len(wknown) == 0 {
			wknown = manifestHashes(wdesired)
		}
		var wfound bool
		if wops, wfound, err = planRemoval(base, res.WorkflowDir, wknown, wdesired); err != nil {
			return nil, fmt.Errorf("workflows for %q: %w", skill.Name, err)
		}
		// Workflows alone do not make a skill "installed" unless recorded for it.
		found = found || (wfound && len(workflowEntries(wm, skill.Name)) > 0)
		res.Workflows = changes(wops)
	}

	if m == nil && !found {
		return nil, fmt.Errorf("skill %q is %w at %s", skill.Name, ErrNotInstalled, target.Display(target.InstallDir(skill.Name)))
	}
	res.Existing = true
	if opts.DryRun {
		return res, nil
	}

	root := cleanupRoot(target, res.Dir)
	if err := applySync(base, res.Dir, ops); err != nil {
		return res, fmt.Errorf("removing skill %q: %w", skill.Name, err)
	}
	if err := removeFileSafe(base, path.Join(res.Dir, SkillManifestName)); err != nil {
		return res, fmt.Errorf("removing manifest: %w", err)
	}
	removeEmptyDirs(base, res.Dir, root)
	res.DirRemoved = !exists(filepath.Join(base, filepath.FromSlash(res.Dir)))

	if res.WorkflowDir == "" {
		return res, nil
	}
	if err := applySync(base, res.WorkflowDir, wops); err != nil {
		return res, fmt.Errorf("removing workflows for %q: %w", skill.Name, err)
	}
	if wm != nil {
		for name, e := range wm.Files {
			if e.Skill == skill.Name {
				delete(wm.Files, name)
			}
		}
		manifestRel := path.Join(res.WorkflowDir, WorkflowManifestName)
		if len(wm.Files) == 0 {
			err = removeFileSafe(base, manifestRel)
		} else {
			err = writeManifest(base, manifestRel, wm)
		}
		if err != nil {
			return res, fmt.Errorf("updating workflow manifest: %w", err)
		}
	}
	removeEmptyDirs(base, res.WorkflowDir, cleanupRoot(target, res.WorkflowDir))
	return res, nil
}
