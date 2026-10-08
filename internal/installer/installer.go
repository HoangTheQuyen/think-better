package installer

import (
	"bytes"
	"fmt"
	"io/fs"
	"os"
	"path"
	"strconv"
	"strings"

	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// Installer installs, updates and removes skills under a base directory
// (the project directory, or the home directory for --global installs).
type Installer struct {
	BaseDir string // Directory the target's paths are relative to
	Version string // think-better version recorded in manifests
}

// NewInstaller creates an Installer rooted at baseDir that records version in manifests.
func NewInstaller(baseDir, version string) *Installer {
	return &Installer{BaseDir: baseDir, Version: version}
}

// Options control how Install and Uninstall treat existing files.
type Options struct {
	// Force replaces files the user modified, after saving each one as
	// <file>.bak. Without it, modified files are kept and the new version
	// is written next to them as <file>.new.
	Force bool
	// DryRun computes the changes without touching the disk.
	DryRun bool
}

// Action says what happens (or would happen, in a dry run) to one file.
type Action string

const (
	ActionCreate      Action = "create"       // file did not exist; written
	ActionUpdate      Action = "update"       // unmodified file replaced by the new version
	ActionUnchanged   Action = "unchanged"    // already up to date
	ActionKeepNew     Action = "keep-new"     // user-modified file kept; new version written to Aside (<file>.new)
	ActionKeep        Action = "keep"         // user-modified file kept; the new version brings no change to it
	ActionReplace     Action = "replace"      // user-modified file saved to Aside (<file>.bak), then replaced
	ActionRemove      Action = "remove"       // unmodified file deleted (obsolete, or uninstall)
	ActionKeepRemoved Action = "keep-removed" // would be deleted, but the user modified it, so it is kept
)

// Change is one file operation.
type Change struct {
	Path   string // slash path relative to the install (or workflow) directory
	Action Action
	Aside  string // the .new or .bak file, relative to the same directory
}

// Result describes what Install or Uninstall did (or would do) for one skill.
type Result struct {
	Skill       string
	Dir         string   // skill install directory, slash path relative to the base
	WorkflowDir string   // workflow directory, "" when the target has none
	Files       []Change // skill files, relative to Dir
	Workflows   []Change // workflow files, relative to WorkflowDir
	Existing    bool     // the skill was already (at least partly) installed
	DirRemoved  bool     // Uninstall removed the install directory
}

// Count returns how many changes (files and workflows) have one of the actions.
func (r *Result) Count(actions ...Action) int {
	n := 0
	for _, list := range [][]Change{r.Files, r.Workflows} {
		for _, c := range list {
			for _, a := range actions {
				if c.Action == a {
					n++
				}
			}
		}
	}
	return n
}

// plannedOp is a Change plus the data needed to carry it out.
type plannedOp struct {
	Change
	data    []byte // new content (create, update, keep-new, replace)
	current []byte // content on disk (replace: saved as the backup)
	hash    string // hash of data
}

// skillDir is the cleaned install directory of a skill for a target.
func skillDir(target *targets.AITarget, skill string) string {
	return path.Clean(target.InstallDir(skill))
}

// workflowDir is the cleaned workflow directory of a target ("" if none).
func workflowDir(target *targets.AITarget) string {
	if !target.HasWorkflows() {
		return ""
	}
	return path.Clean(target.WorkflowDir())
}

// cleanupRoot is the directory empty-directory cleanup stops at: the base
// for project installs, and the first directory under home (~/.claude,
// ~/.config, ...) for global installs, which is never removed.
func cleanupRoot(target *targets.AITarget, dirRel string) string {
	if target.IsGlobal() {
		first, _, _ := strings.Cut(dirRel, "/")
		return first
	}
	return "."
}

// fileMode is the mode files are written with: .py scripts are executable.
func fileMode(rel string) os.FileMode {
	if strings.HasSuffix(rel, ".py") {
		return 0o755
	}
	return 0o644
}

// desiredSkillFiles returns the content of every skill file as installed
// for target (Markdown paths rewritten for the target), keyed by slash path.
func desiredSkillFiles(skill string, target *targets.AITarget) (map[string][]byte, error) {
	sub, err := skills.SkillFS(skill)
	if err != nil {
		return nil, fmt.Errorf("accessing embedded skill %q: %w", skill, err)
	}
	files, err := skills.SkillFiles(skill)
	if err != nil {
		return nil, err
	}
	out := make(map[string][]byte, len(files))
	for _, f := range files {
		if f == SkillManifestName {
			continue
		}
		data, err := fs.ReadFile(sub, f)
		if err != nil {
			return nil, fmt.Errorf("reading embedded %s: %w", f, err)
		}
		// Skill docs reference scripts by their .agents/ path; point them at this target
		if strings.HasSuffix(f, ".md") {
			data = []byte(target.RewriteSkillPaths(string(data)))
		}
		out[f] = data
	}
	return out, nil
}

// desiredWorkflows returns the workflows (slash commands) that run skill,
// adapted for target and keyed by their installed file name.
func desiredWorkflows(skill string, target *targets.AITarget) (map[string][]byte, error) {
	out := map[string][]byte{}
	if !target.HasWorkflows() {
		return out, nil
	}
	sub, err := skills.WorkflowFS()
	if err != nil {
		return nil, fmt.Errorf("accessing embedded workflows: %w", err)
	}
	files, err := skills.WorkflowFiles()
	if err != nil {
		return nil, err
	}
	for _, f := range files {
		if skills.WorkflowSkill(f) != skill {
			continue
		}
		data, err := fs.ReadFile(sub, f)
		if err != nil {
			return nil, fmt.Errorf("reading embedded workflow %s: %w", f, err)
		}
		out[target.WorkflowFileName(f)] = []byte(target.AdaptWorkflow(string(data)))
	}
	return out, nil
}

// workflowEntries returns the manifest entries (name → hash) owned by skill.
func workflowEntries(m *WorkflowManifest, skill string) map[string]string {
	if m == nil {
		return nil
	}
	var out map[string]string
	for name, e := range m.Files {
		if e.Skill == skill {
			if out == nil {
				out = map[string]string{}
			}
			out[name] = e.SHA256
		}
	}
	return out // nil when the skill has no entries: treated like a legacy install
}

// planSync decides what to do with each file in dirRel so it matches desired.
// recorded holds the hashes from the manifest (nil for a legacy install).
//
//   - missing file: create
//   - same content as the new version: unchanged
//   - content matches the manifest (not modified by the user): update
//   - modified by the user: with force, back up to <file>.bak and replace;
//     otherwise keep it and write the new version to <file>.new (nothing is
//     written when the new version equals what was installed)
//   - recorded but no longer shipped: remove if unmodified, else keep
//
// A file with no manifest entry counts as modified unless it already equals
// the new version.
func planSync(base, dirRel string, desired map[string][]byte, recorded map[string]string, force bool) ([]plannedOp, error) {
	var ops []plannedOp
	for _, rel := range sortedKeys(desired) {
		data := desired[rel]
		op := plannedOp{Change: Change{Path: rel}, data: data, hash: hashBytes(data)}
		cur, err := readRegular(base, path.Join(dirRel, rel))
		if err != nil {
			return nil, err
		}
		rec, hasRec := recorded[rel]
		switch curHash := hashBytes(cur); {
		case cur == nil:
			op.Action = ActionCreate
		case bytes.Equal(cur, data):
			op.Action = ActionUnchanged
		case hasRec && curHash == rec:
			op.Action = ActionUpdate
		case force:
			op.Action = ActionReplace
			op.current = cur
			aside, err := backupName(base, dirRel, rel, cur)
			if err != nil {
				return nil, err
			}
			op.Aside = aside
		case hasRec && rec == op.hash:
			op.Action = ActionKeep
		default:
			op.Action = ActionKeepNew
			op.Aside = rel + ".new"
			if _, err := checkPath(base, path.Join(dirRel, op.Aside)); err != nil {
				return nil, err
			}
		}
		ops = append(ops, op)
	}

	for _, rel := range sortedKeys(recorded) {
		if _, ok := desired[rel]; ok {
			continue
		}
		cur, err := readRegular(base, path.Join(dirRel, rel))
		if err != nil {
			return nil, err
		}
		if cur == nil {
			continue
		}
		action := ActionRemove
		if hashBytes(cur) != recorded[rel] {
			action = ActionKeepRemoved
		}
		ops = append(ops, plannedOp{Change: Change{Path: rel, Action: action}})
	}
	return ops, nil
}

// backupName picks where to save a modified file before replacing it:
// <file>.bak, or <file>.bak.N if that holds something else already.
func backupName(base, dirRel, rel string, content []byte) (string, error) {
	for i := 0; ; i++ {
		name := rel + ".bak"
		if i > 0 {
			name += "." + strconv.Itoa(i)
		}
		existing, err := readRegular(base, path.Join(dirRel, name))
		if err != nil {
			return "", err
		}
		if existing == nil || bytes.Equal(existing, content) {
			return name, nil
		}
	}
}

// applySync carries out planned operations in dirRel. Directories emptied by
// removals are cleaned up, but dirRel itself is kept.
func applySync(base, dirRel string, ops []plannedOp) error {
	for _, op := range ops {
		rel := path.Join(dirRel, op.Path)
		mode := fileMode(op.Path)
		var err error
		switch op.Action {
		case ActionCreate, ActionUpdate:
			err = writeFileSafe(base, rel, op.data, mode)
		case ActionUnchanged:
			err = setModeSafe(base, rel, mode)
		case ActionReplace:
			if err = writeFileSafe(base, path.Join(dirRel, op.Aside), op.current, mode); err == nil {
				err = writeFileSafe(base, rel, op.data, mode)
			}
		case ActionKeepNew:
			err = writeFileSafe(base, path.Join(dirRel, op.Aside), op.data, mode)
		case ActionRemove:
			if err = removeFileSafe(base, rel); err == nil {
				removeEmptyDirs(base, path.Dir(rel), dirRel)
			}
		}
		if err != nil {
			return fmt.Errorf("%s: %w", rel, err)
		}
		if op.Action == ActionCreate || op.Action == ActionUpdate || op.Action == ActionUnchanged || op.Action == ActionReplace {
			removeStaleNew(base, path.Join(dirRel, op.Path+".new"), op.hash)
		}
	}
	return nil
}

// removeStaleNew deletes a <file>.new left by an earlier run once the file
// itself holds that content, so it no longer needs merging.
func removeStaleNew(base, rel, hash string) {
	data, err := readRegular(base, rel)
	if err == nil && data != nil && hashBytes(data) == hash {
		_ = removeFileSafe(base, rel)
	}
}

// manifestHashes maps each file to the hash of its content.
func manifestHashes(files map[string][]byte) map[string]string {
	out := make(map[string]string, len(files))
	for rel, data := range files {
		out[rel] = hashBytes(data)
	}
	return out
}

func changes(ops []plannedOp) []Change {
	out := make([]Change, len(ops))
	for i, op := range ops {
		out[i] = op.Change
	}
	return out
}

// Install installs skill for target, or brings an existing install up to
// date with the embedded version (see planSync for how each file is handled),
// together with the workflows (slash commands) that run the skill. It then
// records what was written in the skill and workflow manifests.
func (inst *Installer) Install(skill *skills.SkillPackage, target *targets.AITarget, opts Options) (*Result, error) {
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
	var recorded map[string]string
	if m != nil {
		recorded = m.Files
	}
	ops, err := planSync(base, res.Dir, desired, recorded, opts.Force)
	if err != nil {
		return nil, fmt.Errorf("skill %q: %w", skill.Name, err)
	}
	res.Files = changes(ops)
	res.Existing = m != nil || res.Count(ActionCreate) < len(res.Files)

	var wops []plannedOp
	var wm *WorkflowManifest
	var wdesired map[string][]byte
	if res.WorkflowDir != "" {
		if wdesired, err = desiredWorkflows(skill.Name, target); err != nil {
			return nil, err
		}
		if wm, err = readWorkflowManifest(base, res.WorkflowDir); err != nil {
			return nil, fmt.Errorf("workflows for %q: %w", skill.Name, err)
		}
		if wops, err = planSync(base, res.WorkflowDir, wdesired, workflowEntries(wm, skill.Name), opts.Force); err != nil {
			return nil, fmt.Errorf("workflows for %q: %w", skill.Name, err)
		}
		res.Workflows = changes(wops)
	}

	if opts.DryRun {
		return res, nil
	}

	if err := ensureDir(base, res.Dir); err != nil {
		return nil, fmt.Errorf("skill %q: %w", skill.Name, err)
	}
	if err := applySync(base, res.Dir, ops); err != nil {
		return res, fmt.Errorf("installing skill %q: %w", skill.Name, err)
	}
	manifest := SkillManifest{Version: inst.Version, Skill: skill.Name, Target: target.Name, Files: manifestHashes(desired)}
	if err := writeManifest(base, path.Join(res.Dir, SkillManifestName), manifest); err != nil {
		return res, fmt.Errorf("writing manifest for %q: %w", skill.Name, err)
	}

	if res.WorkflowDir == "" || len(wops) == 0 {
		return res, nil
	}
	if err := applySync(base, res.WorkflowDir, wops); err != nil {
		return res, fmt.Errorf("installing workflows for %q: %w", skill.Name, err)
	}
	if wm == nil {
		wm = &WorkflowManifest{Files: map[string]WorkflowEntry{}}
	}
	for name, e := range wm.Files {
		if e.Skill == skill.Name {
			delete(wm.Files, name)
		}
	}
	for name, data := range wdesired {
		wm.Files[name] = WorkflowEntry{Skill: skill.Name, SHA256: hashBytes(data)}
	}
	wm.Version, wm.Target = inst.Version, target.Name
	if err := writeManifest(base, path.Join(res.WorkflowDir, WorkflowManifestName), wm); err != nil {
		return res, fmt.Errorf("writing workflow manifest: %w", err)
	}
	return res, nil
}
