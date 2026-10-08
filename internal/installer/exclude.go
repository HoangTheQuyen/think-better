package installer

import (
	"fmt"
	"path"
	"slices"

	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// Excluded workflows are slash commands the user does not want: they are
// listed by installed file name in the workflow manifest ("exclude"), are
// not installed or restored by Install, are removed (when unmodified) from
// an existing install, and do not count as missing or outdated in a status.

// withoutExcluded returns desired without the excluded workflow files: the
// override list when not nil, else the manifest's list.
func withoutExcluded(desired map[string][]byte, wm *WorkflowManifest, override []string) map[string][]byte {
	excluded := override
	if excluded == nil && wm != nil {
		excluded = wm.Exclude
	}
	if len(excluded) == 0 {
		return desired
	}
	out := make(map[string][]byte, len(desired))
	for name, data := range desired {
		if !slices.Contains(excluded, name) {
			out[name] = data
		}
	}
	return out
}

// ExcludedWorkflows returns the workflow file names excluded in target's
// workflow directory (nil when there are none or the target has no workflows).
func (inst *Installer) ExcludedWorkflows(target *targets.AITarget) ([]string, error) {
	dir := workflowDir(target)
	if dir == "" {
		return nil, nil
	}
	wm, err := readWorkflowManifest(inst.BaseDir, dir)
	if err != nil || wm == nil {
		return nil, err
	}
	return slices.Clone(wm.Exclude), nil
}

// SetExcludedWorkflows records the excluded workflow file names for target's
// workflow directory, creating the workflow manifest if needed. Pass the
// result as Options.ExcludeWorkflows to apply it in a dry run.
func (inst *Installer) SetExcludedWorkflows(target *targets.AITarget, names []string) error {
	dir := workflowDir(target)
	if dir == "" {
		return fmt.Errorf("%s has no slash commands to exclude", target.Name)
	}
	for _, n := range names {
		if !validRel(n) || path.Base(n) != n {
			return fmt.Errorf("invalid workflow name %q", n)
		}
	}
	wm, err := readWorkflowManifest(inst.BaseDir, dir)
	if err != nil {
		return err
	}
	if wm == nil {
		if len(names) == 0 {
			return nil
		}
		wm = &WorkflowManifest{Version: inst.Version, Target: target.Name, Files: map[string]WorkflowEntry{}}
	}
	sorted := slices.Clone(names)
	slices.Sort(sorted)
	sorted = slices.Compact(sorted)
	if slices.Equal(sorted, wm.Exclude) {
		return nil
	}
	wm.Exclude = sorted
	if len(wm.Exclude) == 0 {
		wm.Exclude = nil
	}
	return writeManifest(inst.BaseDir, path.Join(dir, WorkflowManifestName), wm)
}
