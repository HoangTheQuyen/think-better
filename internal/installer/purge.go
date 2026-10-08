package installer

import (
	"fmt"
	"path"
	"path/filepath"

	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// RemoveModified deletes the files an Uninstall kept because the user had
// modified them (ActionKeepRemoved in res), together with the <file>.new
// written next to them by an earlier update, then removes directories left
// empty. It is used by uninstall --force. It returns the deleted files as
// slash paths relative to the base (res is left as it was, except for
// DirRemoved); with dryRun it only lists them.
func (inst *Installer) RemoveModified(target *targets.AITarget, res *Result, dryRun bool) ([]string, error) {
	base := inst.BaseDir
	var removed []string
	purge := func(dirRel string, list []Change) error {
		for _, c := range list {
			if c.Action != ActionKeepRemoved {
				continue
			}
			rel := path.Join(dirRel, c.Path)
			removed = append(removed, rel)
			if dryRun {
				continue
			}
			for _, p := range []string{rel, rel + ".new"} {
				if err := removeFileSafe(base, p); err != nil {
					return fmt.Errorf("removing %s: %w", p, err)
				}
			}
			removeEmptyDirs(base, path.Dir(rel), dirRel)
		}
		return nil
	}
	if err := purge(res.Dir, res.Files); err != nil {
		return removed, err
	}
	if res.WorkflowDir != "" {
		if err := purge(res.WorkflowDir, res.Workflows); err != nil {
			return removed, err
		}
	}
	if dryRun || len(removed) == 0 {
		return removed, nil
	}
	// The tombstone only listed the kept files, which are now gone.
	if err := removeFileSafe(base, path.Join(res.Dir, SkillManifestName)); err != nil {
		return removed, fmt.Errorf("updating manifest: %w", err)
	}
	removeEmptyDirs(base, res.Dir, cleanupRoot(target, res.Dir))
	res.DirRemoved = !exists(filepath.Join(base, filepath.FromSlash(res.Dir)))
	if res.WorkflowDir != "" {
		removeEmptyDirs(base, res.WorkflowDir, cleanupRoot(target, res.WorkflowDir))
	}
	return removed, nil
}
