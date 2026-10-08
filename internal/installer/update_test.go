package installer

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"runtime"
	"testing"

	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// fixture is one skill installed for claude in a temporary project.
type fixture struct {
	t      *testing.T
	base   string
	skill  *skills.SkillPackage
	target *targets.AITarget
	inst   *Installer
}

func newFixture(t *testing.T) *fixture {
	t.Helper()
	f := &fixture{
		t:      t,
		base:   t.TempDir(),
		skill:  skills.FindSkill("code-solving"),
		target: targets.FindTarget("claude"),
	}
	f.inst = NewInstaller(f.base, testVersion)
	f.install(Options{})
	return f
}

func (f *fixture) install(opts Options) *Result {
	f.t.Helper()
	res, err := f.inst.Install(f.skill, f.target, opts)
	if err != nil {
		f.t.Fatalf("Install: %v", err)
	}
	return res
}

func (f *fixture) path(rel string) string {
	return filepath.Join(f.base, ".claude", "skills", f.skill.Name, filepath.FromSlash(rel))
}

func (f *fixture) read(rel string) string {
	f.t.Helper()
	data, err := os.ReadFile(f.path(rel))
	if err != nil {
		f.t.Fatal(err)
	}
	return string(data)
}

func (f *fixture) write(rel, content string) {
	f.t.Helper()
	if err := os.MkdirAll(filepath.Dir(f.path(rel)), 0o755); err != nil {
		f.t.Fatal(err)
	}
	if err := os.WriteFile(f.path(rel), []byte(content), 0o644); err != nil {
		f.t.Fatal(err)
	}
}

func (f *fixture) manifest() *SkillManifest {
	f.t.Helper()
	data, err := os.ReadFile(f.path(SkillManifestName))
	if err != nil {
		f.t.Fatal(err)
	}
	var m SkillManifest
	if err := json.Unmarshal(data, &m); err != nil {
		f.t.Fatal(err)
	}
	return &m
}

func (f *fixture) setManifest(m *SkillManifest) {
	f.t.Helper()
	data, err := json.Marshal(m)
	if err != nil {
		f.t.Fatal(err)
	}
	if err := os.WriteFile(f.path(SkillManifestName), data, 0o644); err != nil {
		f.t.Fatal(err)
	}
}

// simulateOld makes rel look like it was installed by an older release with
// content old; with userContent != "", the user then edited it.
func (f *fixture) simulateOld(rel, old, userContent string) {
	f.t.Helper()
	m := f.manifest()
	m.Files[rel] = hashBytes([]byte(old))
	f.setManifest(m)
	if userContent == "" {
		userContent = old
	}
	f.write(rel, userContent)
}

func onDisk(t *testing.T, p string) bool {
	t.Helper()
	_, err := os.Lstat(p)
	return err == nil
}

func actionOf(changes []Change, rel string) Action {
	for _, c := range changes {
		if c.Path == rel {
			return c.Action
		}
	}
	return ""
}

func TestInstallWritesManifest(t *testing.T) {
	f := newFixture(t)
	m := f.manifest()
	if m.Version != testVersion || m.Skill != "code-solving" || m.Target != "claude" {
		t.Errorf("manifest header = %+v", m)
	}
	files, _ := skills.SkillFiles(f.skill.Name)
	if len(m.Files) != len(files) {
		t.Errorf("manifest has %d files, skill has %d", len(m.Files), len(files))
	}
	for rel, h := range m.Files {
		if got := hashBytes([]byte(f.read(rel))); got != h {
			t.Errorf("%s: manifest hash %s, file hash %s", rel, h, got)
		}
	}

	wm, err := readWorkflowManifest(f.base, ".claude/commands")
	if err != nil || wm == nil {
		t.Fatalf("workflow manifest: %v", err)
	}
	e, ok := wm.Files["code.md"]
	if !ok || e.Skill != "code-solving" {
		t.Fatalf("code.md entry = %+v", e)
	}
	data, _ := os.ReadFile(filepath.Join(f.base, ".claude", "commands", "code.md"))
	if hashBytes(data) != e.SHA256 {
		t.Error("workflow hash does not match file")
	}
}

func TestReinstallIsNoOp(t *testing.T) {
	f := newFixture(t)
	res := f.install(Options{})
	if !res.Existing {
		t.Error("Existing = false on reinstall")
	}
	if n := res.Count(ActionUnchanged); n != len(res.Files)+len(res.Workflows) {
		t.Errorf("unchanged = %d of %d", n, len(res.Files)+len(res.Workflows))
	}
}

func TestUpdate(t *testing.T) {
	f := newFixture(t)
	want := f.read("SKILL.md")
	wantPrompt := f.read("PROMPT.md")

	// SKILL.md changed upstream, user did not touch it: updated.
	f.simulateOld("SKILL.md", "old skill", "")
	// PROMPT.md changed upstream and the user edited it: kept, .new written.
	f.simulateOld("PROMPT.md", "old prompt", "my prompt")
	// A data file the user edited, unchanged upstream: kept, no .new.
	f.write("data/steps.csv", "my steps")
	// Files dropped from the skill: removed unless modified.
	m := f.manifest()
	m.Files["data/gone.csv"] = hashBytes([]byte("gone"))
	m.Files["old/edited.txt"] = hashBytes([]byte("orig"))
	f.setManifest(m)
	f.write("data/gone.csv", "gone")
	f.write("old/edited.txt", "edited")
	// A user-added file is never touched.
	f.write("notes.md", "mine")

	dry := f.install(Options{DryRun: true})
	if f.read("SKILL.md") != "old skill" || !onDisk(t, f.path("data/gone.csv")) || onDisk(t, f.path("PROMPT.md.new")) {
		t.Fatal("dry run changed files")
	}

	res := f.install(Options{})
	for _, r := range []*Result{dry, res} {
		checks := map[string]Action{
			"SKILL.md":        ActionUpdate,
			"PROMPT.md":       ActionKeepNew,
			"data/steps.csv":  ActionKeep,
			"data/gone.csv":   ActionRemove,
			"old/edited.txt":  ActionKeepRemoved,
			"scripts/core.py": ActionUnchanged,
		}
		for rel, a := range checks {
			if got := actionOf(r.Files, rel); got != a {
				t.Errorf("%s: action %q, want %q", rel, got, a)
			}
		}
	}

	if f.read("SKILL.md") != want {
		t.Error("SKILL.md not updated")
	}
	if f.read("PROMPT.md") != "my prompt" || f.read("PROMPT.md.new") != wantPrompt {
		t.Error("PROMPT.md: user version should stay, new version in PROMPT.md.new")
	}
	if f.read("data/steps.csv") != "my steps" || onDisk(t, f.path("data/steps.csv.new")) {
		t.Error("data/steps.csv should be kept without a .new")
	}
	if onDisk(t, f.path("data/gone.csv")) {
		t.Error("obsolete unmodified file not removed")
	}
	if f.read("old/edited.txt") != "edited" || f.read("notes.md") != "mine" {
		t.Error("user files changed")
	}

	m = f.manifest()
	if _, ok := m.Files["data/gone.csv"]; ok {
		t.Error("obsolete file still in manifest")
	}
	if m.Files["PROMPT.md"] != hashBytes([]byte(wantPrompt)) {
		t.Error("manifest should record the offered version of PROMPT.md")
	}

	// Still modified on the next run, but nothing more to write.
	res = f.install(Options{})
	if got := actionOf(res.Files, "PROMPT.md"); got != ActionKeep {
		t.Errorf("second update: PROMPT.md action %q, want keep", got)
	}
}

func TestUpdateForceBacksUp(t *testing.T) {
	f := newFixture(t)
	want := f.read("PROMPT.md")
	f.write("PROMPT.md.new", want) // left over from an earlier update
	f.write("PROMPT.md", "my prompt")
	f.write("SKILL.md.bak", "an older backup")
	f.write("SKILL.md", "my skill")

	res := f.install(Options{Force: true})
	if got := actionOf(res.Files, "PROMPT.md"); got != ActionReplace {
		t.Fatalf("PROMPT.md action %q, want replace", got)
	}
	if f.read("PROMPT.md") != want || f.read("PROMPT.md.bak") != "my prompt" {
		t.Error("force should replace PROMPT.md and save PROMPT.md.bak")
	}
	if onDisk(t, f.path("PROMPT.md.new")) {
		t.Error("stale PROMPT.md.new should be removed once applied")
	}
	if f.read("SKILL.md.bak") != "an older backup" || f.read("SKILL.md.bak.1") != "my skill" {
		t.Error("existing backup must not be overwritten")
	}
}

func TestLegacyInstallWithoutManifest(t *testing.T) {
	f := newFixture(t)
	if err := os.Remove(f.path(SkillManifestName)); err != nil {
		t.Fatal(err)
	}
	if err := os.Remove(filepath.Join(f.base, ".claude", "commands", WorkflowManifestName)); err != nil {
		t.Fatal(err)
	}
	f.write("SKILL.md", "edited or old")

	st, err := CheckStatus(f.skill, f.target, f.base, testVersion)
	if err != nil {
		t.Fatal(err)
	}
	if st.HasManifest || st.Status != StatusModified || len(st.Modified) != 1 {
		t.Errorf("legacy status = %+v", st)
	}

	res := f.install(Options{})
	if got := actionOf(res.Files, "SKILL.md"); got != ActionKeepNew {
		t.Errorf("SKILL.md action %q, want keep-new", got)
	}
	if got := actionOf(res.Files, "PROMPT.md"); got != ActionUnchanged {
		t.Errorf("PROMPT.md action %q, want unchanged", got)
	}
	if f.manifest().Version != testVersion {
		t.Error("manifest not written for legacy install")
	}
}

func TestCheckStatus(t *testing.T) {
	f := newFixture(t)
	status := func(version string) *InstallStatus {
		t.Helper()
		st, err := CheckStatus(f.skill, f.target, f.base, version)
		if err != nil {
			t.Fatal(err)
		}
		return st
	}

	if st := status(testVersion); st.Status != StatusInstalled || st.Outdated || !st.HasManifest {
		t.Errorf("fresh install: %+v", st)
	}
	if st := status("v1.1.0"); st.Status != StatusOutdated {
		t.Errorf("newer binary: %q, want outdated", st.Status)
	}
	if st := status("dev"); st.Status != StatusInstalled {
		t.Errorf("dev binary: %q, want installed", st.Status)
	}

	f.write("data/steps.csv", "mine")
	if st := status(testVersion); st.Status != StatusModified || len(st.Modified) != 1 {
		t.Errorf("modified: %+v", st)
	}

	f.simulateOld("SKILL.md", "old", "")
	if st := status(testVersion); st.Status != StatusOutdated || len(st.Modified) != 1 {
		t.Errorf("content outdated: %+v", st)
	}

	if err := os.Remove(f.path("scripts/core.py")); err != nil {
		t.Fatal(err)
	}
	if st := status(testVersion); st.Status != StatusIncomplete || len(st.Missing) != 1 {
		t.Errorf("incomplete: %+v", st)
	}

	f.install(Options{Force: true})
	if st := status(testVersion); st.Status != StatusInstalled {
		t.Errorf("after forced update: %+v", st)
	}

	if err := os.Remove(filepath.Join(f.base, ".claude", "commands", "code.md")); err != nil {
		t.Fatal(err)
	}
	if st := status(testVersion); st.Status != StatusIncomplete {
		t.Errorf("missing workflow: %+v", st)
	}
}

func TestUninstallKeepsModifiedFiles(t *testing.T) {
	f := newFixture(t)
	f.write("SKILL.md", "my notes")
	cmdDir := filepath.Join(f.base, ".claude", "commands")
	if err := os.WriteFile(filepath.Join(cmdDir, "code.md"), []byte("my command"), 0o644); err != nil {
		t.Fatal(err)
	}

	res, err := f.inst.Uninstall(f.skill, f.target, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if actionOf(res.Files, "SKILL.md") != ActionKeepRemoved || actionOf(res.Workflows, "code.md") != ActionKeepRemoved {
		t.Error("modified files should be reported as kept")
	}
	if f.read("SKILL.md") != "my notes" {
		t.Error("modified SKILL.md was deleted")
	}
	if onDisk(t, f.path("PROMPT.md")) || onDisk(t, f.path("scripts")) || onDisk(t, f.path(SkillManifestName)) {
		t.Error("unmodified files, emptied directories and the manifest should be removed")
	}
	if res.DirRemoved {
		t.Error("install dir still holds SKILL.md and must not be removed")
	}
	if !onDisk(t, filepath.Join(cmdDir, "code.md")) || onDisk(t, filepath.Join(cmdDir, "code.debug.md")) {
		t.Error("only the modified workflow should remain")
	}
	if onDisk(t, filepath.Join(cmdDir, WorkflowManifestName)) {
		t.Error("workflow manifest should be removed with its last entry")
	}
}

func TestUninstallCleansEmptyDirs(t *testing.T) {
	f := newFixture(t)
	if err := os.WriteFile(filepath.Join(f.base, ".claude", "settings.json"), []byte("{}"), 0o644); err != nil {
		t.Fatal(err)
	}
	f.write("PROMPT.md.new", f.read("PROMPT.md")) // left by an update: ours to remove

	res, err := f.inst.Uninstall(f.skill, f.target, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if !res.DirRemoved || res.Count(ActionKeepRemoved) != 0 {
		t.Errorf("result = %+v", res)
	}
	for _, gone := range []string{".claude/skills", ".claude/commands"} {
		if onDisk(t, filepath.Join(f.base, filepath.FromSlash(gone))) {
			t.Errorf("%s should be removed once empty", gone)
		}
	}
	if !onDisk(t, filepath.Join(f.base, ".claude", "settings.json")) {
		t.Error(".claude holds other content and must stay")
	}

	if _, err := f.inst.Uninstall(f.skill, f.target, Options{}); !errors.Is(err, ErrNotInstalled) {
		t.Errorf("second uninstall: %v, want ErrNotInstalled", err)
	}
}

func TestUninstallGlobalKeepsTopDir(t *testing.T) {
	home := t.TempDir()
	target, err := targets.FindTarget("opencode").Global()
	if err != nil {
		t.Fatal(err)
	}
	inst := NewInstaller(home, testVersion)
	skill := skills.FindSkill("make-decision")
	if _, err := inst.Install(skill, target, Options{}); err != nil {
		t.Fatal(err)
	}
	if _, err := inst.Uninstall(skill, target, Options{}); err != nil {
		t.Fatal(err)
	}
	if onDisk(t, filepath.Join(home, ".config", "opencode")) {
		t.Error("~/.config/opencode should be removed once empty")
	}
	if !onDisk(t, filepath.Join(home, ".config")) {
		t.Error("~/.config must never be removed")
	}
}

func TestUninstallLegacy(t *testing.T) {
	f := newFixture(t)
	if err := os.Remove(f.path(SkillManifestName)); err != nil {
		t.Fatal(err)
	}
	f.write("PROMPT.md", "edited")
	res, err := f.inst.Uninstall(f.skill, f.target, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if actionOf(res.Files, "PROMPT.md") != ActionKeepRemoved || actionOf(res.Files, "SKILL.md") != ActionRemove {
		t.Errorf("legacy uninstall changes = %+v", res.Files)
	}
	if f.read("PROMPT.md") != "edited" || onDisk(t, f.path("SKILL.md")) {
		t.Error("legacy uninstall should remove only files identical to this version")
	}
}

func TestTamperedManifestCannotEscape(t *testing.T) {
	f := newFixture(t)
	outside := filepath.Join(f.base, "outside.txt")
	if err := os.WriteFile(outside, []byte("precious"), 0o644); err != nil {
		t.Fatal(err)
	}
	m := f.manifest()
	m.Files["../../../outside.txt"] = hashBytes([]byte("precious"))
	m.Files["/etc/passwd"] = "x"
	f.setManifest(m)

	f.install(Options{})
	if _, err := f.inst.Uninstall(f.skill, f.target, Options{}); err != nil {
		t.Fatal(err)
	}
	if !onDisk(t, outside) {
		t.Error("file outside the install dir was deleted")
	}
}

func symlinkOrSkip(t *testing.T, oldname, newname string) {
	t.Helper()
	if err := os.Symlink(oldname, newname); err != nil {
		t.Skipf("symlinks not supported: %v", err)
	}
}

func TestRefusesSymlinkedDirectory(t *testing.T) {
	base, elsewhere := t.TempDir(), t.TempDir()
	symlinkOrSkip(t, elsewhere, filepath.Join(base, ".claude"))

	inst := NewInstaller(base, testVersion)
	_, err := inst.Install(skills.FindSkill("code-solving"), targets.FindTarget("claude"), Options{})
	if !errors.Is(err, ErrUnsafePath) {
		t.Fatalf("Install through symlinked .claude: err = %v, want ErrUnsafePath", err)
	}
	entries, _ := os.ReadDir(elsewhere)
	if len(entries) != 0 {
		t.Errorf("wrote %d entries through the symlink", len(entries))
	}
}

func TestRefusesSymlinkedWorkflowDir(t *testing.T) {
	base, elsewhere := t.TempDir(), t.TempDir()
	if err := os.MkdirAll(filepath.Join(base, ".claude"), 0o755); err != nil {
		t.Fatal(err)
	}
	symlinkOrSkip(t, elsewhere, filepath.Join(base, ".claude", "commands"))

	_, err := NewInstaller(base, testVersion).Install(skills.FindSkill("code-solving"), targets.FindTarget("claude"), Options{})
	if !errors.Is(err, ErrUnsafePath) {
		t.Fatalf("err = %v, want ErrUnsafePath", err)
	}
	entries, _ := os.ReadDir(elsewhere)
	if len(entries) != 0 || onDisk(t, filepath.Join(base, ".claude", "skills")) {
		t.Error("nothing should be written when any path is unsafe")
	}
}

func TestRefusesSymlinkedFile(t *testing.T) {
	f := newFixture(t)
	outside := filepath.Join(t.TempDir(), "target.md")
	if err := os.WriteFile(outside, []byte("not yours"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.Remove(f.path("SKILL.md")); err != nil {
		t.Fatal(err)
	}
	symlinkOrSkip(t, outside, f.path("SKILL.md"))

	if _, err := f.inst.Install(f.skill, f.target, Options{Force: true}); !errors.Is(err, ErrUnsafePath) {
		t.Errorf("Install over symlinked file: err = %v, want ErrUnsafePath", err)
	}
	if _, err := f.inst.Uninstall(f.skill, f.target, Options{}); !errors.Is(err, ErrUnsafePath) {
		t.Errorf("Uninstall with symlinked file: err = %v, want ErrUnsafePath", err)
	}
	data, _ := os.ReadFile(outside)
	if string(data) != "not yours" {
		t.Error("symlink target was modified")
	}
}

func TestInstallFixesMode(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("file modes are not meaningful on Windows")
	}
	f := newFixture(t)
	if err := os.Chmod(f.path("scripts/core.py"), 0o600); err != nil {
		t.Fatal(err)
	}
	f.simulateOld("scripts/search.py", "old", "")
	if err := os.Chmod(f.path("scripts/search.py"), 0o600); err != nil {
		t.Fatal(err)
	}
	f.install(Options{})
	for _, rel := range []string{"scripts/core.py", "scripts/search.py"} {
		fi, err := os.Stat(f.path(rel))
		if err != nil {
			t.Fatal(err)
		}
		if fi.Mode().Perm() != 0o755 {
			t.Errorf("%s mode = %o, want 755", rel, fi.Mode().Perm())
		}
	}
	if fi, _ := os.Stat(f.path("SKILL.md")); fi.Mode().Perm() != 0o644 {
		t.Errorf("SKILL.md mode = %o, want 644", fi.Mode().Perm())
	}
	// No temporary files are left behind.
	entries, _ := os.ReadDir(f.path("scripts"))
	for _, e := range entries {
		if filepath.Ext(e.Name()) != ".py" {
			t.Errorf("unexpected file %s", e.Name())
		}
	}
}

func TestVersionOlder(t *testing.T) {
	tests := []struct {
		a, b string
		want bool
	}{
		{"v1.2.3", "v1.3.0", true},
		{"v1.3.0", "v1.2.9", false},
		{"v1.3.0", "v1.3.0", false},
		{"v1.3.0-rc1", "v1.3.0", true},
		{"1.9.0", "v1.10.0", true},
		{"dev", "v1.0.0", false},
		{"v1.0.0", "dev", false},
		{"", "v1.0.0", false},
		{"v1.0.0+dirty", "v1.0.1", true},
	}
	for _, tt := range tests {
		if got := versionOlder(tt.a, tt.b); got != tt.want {
			t.Errorf("versionOlder(%q, %q) = %v, want %v", tt.a, tt.b, got, tt.want)
		}
	}
}

func TestValidRel(t *testing.T) {
	for _, ok := range []string{"SKILL.md", "scripts/a.py", "a.b/c"} {
		if !validRel(ok) {
			t.Errorf("validRel(%q) = false", ok)
		}
	}
	for _, bad := range []string{"", "../x", "a/../../x", "/abs", `a\b`, "a//b", "./a", "."} {
		if validRel(bad) {
			t.Errorf("validRel(%q) = true", bad)
		}
	}
}

func TestResultCount(t *testing.T) {
	r := &Result{
		Files:     []Change{{Action: ActionCreate}, {Action: ActionUpdate}},
		Workflows: []Change{{Action: ActionCreate}},
	}
	if r.Count(ActionCreate) != 2 || r.Count(ActionCreate, ActionUpdate) != 3 || r.Count(ActionRemove) != 0 {
		t.Error("Count is wrong")
	}
}
