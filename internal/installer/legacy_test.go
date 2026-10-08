package installer

import (
	"encoding/hex"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/HoangTheQuyen/think-better/internal/skills"
	"github.com/HoangTheQuyen/think-better/internal/targets"
)

// legacyFixture is make-decision installed for claude the way v1.3.0 left
// it: no manifests, files v1.3.0 shipped with their v1.3.0 content (real
// copies in testdata/v1.3.0), and none of the files added since.
func legacyFixture(t *testing.T) *fixture {
	t.Helper()
	f := &fixture{
		t:      t,
		base:   t.TempDir(),
		skill:  skills.FindSkill("make-decision"),
		target: targets.FindTarget("claude"),
	}
	f.inst = NewInstaller(f.base, testVersion)
	f.install(Options{})
	cmdDir := filepath.Join(f.base, ".claude", "commands")
	for _, p := range []string{f.path(SkillManifestName), filepath.Join(cmdDir, WorkflowManifestName)} {
		if err := os.Remove(p); err != nil {
			t.Fatal(err)
		}
	}

	// Files added after v1.3.0 were never installed.
	hist := skillHistory(f.skill.Name)
	files, err := desiredSkillFiles(f.skill.Name, f.target)
	if err != nil {
		t.Fatal(err)
	}
	for rel := range files {
		if !hist.versions(rel)["v1.3.0"] {
			if err := os.Remove(f.path(rel)); err != nil {
				t.Fatal(err)
			}
		}
	}
	wf := workflowHistory(f.skill.Name)
	wfiles, err := desiredWorkflows(f.skill.Name, f.target)
	if err != nil {
		t.Fatal(err)
	}
	for name := range wfiles {
		if !wf.versions(name)["v1.3.0"] {
			if err := os.Remove(filepath.Join(cmdDir, name)); err != nil {
				t.Fatal(err)
			}
		}
	}

	// Real v1.3.0 content for files that changed since.
	copyFile(t, filepath.Join("testdata", "v1.3.0", "claude", "skills", "make-decision", "data", "decision-types.csv"), f.path("data/decision-types.csv"))
	copyFile(t, filepath.Join("testdata", "v1.3.0", "claude", "commands", "decide.quick.md"), filepath.Join(cmdDir, "decide.quick.md"))
	return f
}

func copyFile(t *testing.T, from, to string) {
	t.Helper()
	data, err := os.ReadFile(from)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(to, data, 0o644); err != nil {
		t.Fatal(err)
	}
}

func TestFixtureIsRealOldContent(t *testing.T) {
	f := legacyFixture(t)
	for rel, want := range map[string]bool{"data/decision-types.csv": true, "scripts/journal.py": false} {
		data, err := os.ReadFile(f.path(rel))
		if want != (err == nil) {
			t.Fatalf("%s present = %v, want %v", rel, err == nil, want)
		}
		if want && !skillHistory(f.skill.Name).versions(rel)["v1.3.0"] {
			t.Fatalf("%s: v1.3.0 not recorded in known_hashes.json", rel)
		}
		if want {
			files, _ := desiredSkillFiles(f.skill.Name, f.target)
			if string(files[rel]) == string(data) {
				t.Fatalf("%s: fixture should differ from the current version", rel)
			}
		}
	}
}

func TestLegacyUpgradeStatus(t *testing.T) {
	f := legacyFixture(t)
	st, err := CheckStatus(f.skill, f.target, f.base, testVersion)
	if err != nil {
		t.Fatal(err)
	}
	if st.HasManifest || st.Status != StatusOutdated || len(st.Missing) != 0 || len(st.Modified) != 0 {
		t.Errorf("v1.3.0 install: status %q, missing %v, modified %v; want outdated, nothing missing or modified",
			st.Status, st.Missing, st.Modified)
	}

	// A file every release shipped that is gone was deleted: incomplete.
	if err := os.Remove(f.path("SKILL.md")); err != nil {
		t.Fatal(err)
	}
	if st, _ := CheckStatus(f.skill, f.target, f.base, testVersion); st.Status != StatusIncomplete || len(st.Missing) != 1 {
		t.Errorf("deleted SKILL.md: status %q, missing %v", st.Status, st.Missing)
	}
}

func TestLegacyUpgradeUpdates(t *testing.T) {
	f := legacyFixture(t)
	f.write("PROMPT.md", "my own prompt") // a real edit
	res := f.install(Options{})

	if got := actionOf(res.Files, "data/decision-types.csv"); got != ActionUpdate {
		t.Errorf("old decision-types.csv: %q, want update", got)
	}
	if got := actionOf(res.Workflows, "decide.quick.md"); got != ActionUpdate {
		t.Errorf("old decide.quick.md: %q, want update", got)
	}
	if got := actionOf(res.Files, "scripts/journal.py"); got != ActionCreate {
		t.Errorf("new journal.py: %q, want create", got)
	}
	if got := actionOf(res.Files, "PROMPT.md"); got != ActionKeepNew {
		t.Errorf("edited PROMPT.md: %q, want keep-new", got)
	}
	if n := res.Count(ActionKeepNew); n != 1 {
		t.Errorf("%d files kept as modified, want only PROMPT.md: %+v", n, res)
	}
	if asides := sideFiles(t, f.base); len(asides) != 1 || !strings.HasSuffix(asides[0], "PROMPT.md.new") {
		t.Errorf(".new/.bak files = %v, want only PROMPT.md.new", asides)
	}
	if st, _ := CheckStatus(f.skill, f.target, f.base, testVersion); st.Status != StatusModified {
		t.Errorf("after update: %+v", st)
	}
}

func TestLegacyUpgradeForce(t *testing.T) {
	f := legacyFixture(t)
	res := f.install(Options{Force: true})
	if n := res.Count(ActionReplace, ActionKeepNew); n != 0 {
		t.Errorf("--force on an unmodified v1.3.0 install backed up %d files", n)
	}
	if asides := sideFiles(t, f.base); len(asides) != 0 {
		t.Errorf("unexpected backups: %v", asides)
	}
	if st, _ := CheckStatus(f.skill, f.target, f.base, testVersion); st.Status != StatusInstalled {
		t.Errorf("after update: %+v", st)
	}
}

func TestLegacyUninstall(t *testing.T) {
	f := legacyFixture(t)
	res, err := f.inst.Uninstall(f.skill, f.target, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if n := res.Count(ActionKeepRemoved); n != 0 {
		t.Errorf("kept %d files of an unmodified v1.3.0 install: %+v", n, res)
	}
	if !res.DirRemoved || onDisk(t, filepath.Join(f.base, ".claude")) {
		t.Error("everything think-better installed should be gone")
	}
}

// sideFiles lists the .new and .bak files under base.
func sideFiles(t *testing.T, base string) []string {
	t.Helper()
	var out []string
	err := filepath.WalkDir(base, func(p string, d os.DirEntry, err error) error {
		if err == nil && (strings.HasSuffix(p, ".new") || strings.Contains(filepath.Base(p), ".bak")) {
			out = append(out, p)
		}
		return err
	})
	if err != nil {
		t.Fatal(err)
	}
	return out
}

// An earlier release's file that this version no longer ships is removed by
// update and uninstall when unmodified, and left alone otherwise.
func TestObsoleteReleasedFile(t *testing.T) {
	base := t.TempDir()
	hist := shipped{"old.py": {hashBytes([]byte("v1 content")): {"v1.0.0"}}}
	desired := map[string][]byte{"SKILL.md": []byte("new")}
	write := func(rel, content string) {
		if err := os.WriteFile(filepath.Join(base, rel), []byte(content), 0o644); err != nil {
			t.Fatal(err)
		}
	}

	write("old.py", "v1 content")
	ops, err := planSync(base, ".", desired, nil, hist, false)
	if err != nil {
		t.Fatal(err)
	}
	if got := actionOf(changes(ops), "old.py"); got != ActionRemove {
		t.Errorf("unmodified old file: %q, want remove", got)
	}
	ops, _, err = planRemoval(base, ".", manifestHashes(desired), desired, hist)
	if err != nil {
		t.Fatal(err)
	}
	if got := actionOf(changes(ops), "old.py"); got != ActionRemove {
		t.Errorf("uninstall, unmodified old file: %q, want remove", got)
	}

	write("old.py", "my version")
	ops, err = planSync(base, ".", desired, nil, hist, false)
	if err != nil {
		t.Fatal(err)
	}
	if got := actionOf(changes(ops), "old.py"); got != "" {
		t.Errorf("modified old file without a manifest entry: %q, want left alone", got)
	}
	ops, _, err = planRemoval(base, ".", manifestHashes(desired), desired, hist)
	if err != nil {
		t.Fatal(err)
	}
	if got := actionOf(changes(ops), "old.py"); got != "" {
		t.Errorf("uninstall, modified old file: %q, want left alone", got)
	}
}

func TestKnownHashesData(t *testing.T) {
	kh := loadKnownHashes()
	if len(kh.Versions) == 0 || kh.Versions[0] != "v1.0.0" {
		t.Errorf("versions = %v", kh.Versions)
	}
	for i := 1; i < len(kh.Versions); i++ {
		if !versionOlder(kh.Versions[i-1], kh.Versions[i]) {
			t.Errorf("versions not in release order: %v", kh.Versions)
		}
	}
	have := map[string]bool{}
	for _, v := range kh.Versions {
		have[v] = true
	}
	for _, group := range []map[string]shipped{kh.Skills, kh.Workflows} {
		for skill, files := range group {
			for rel, hashes := range files {
				if !validRel(rel) {
					t.Errorf("%s: invalid path %q", skill, rel)
				}
				for h, versions := range hashes {
					if b, err := hex.DecodeString(h); err != nil || len(b) != 32 {
						t.Errorf("%s/%s: bad hash %q", skill, rel, h)
					}
					for _, v := range versions {
						if !have[v] {
							t.Errorf("%s/%s: unknown version %q", skill, rel, v)
						}
					}
				}
			}
		}
	}
	for _, skill := range []string{"make-decision", "problem-solving-pro", "code-solving"} {
		if len(skillHistory(skill)) == 0 || len(workflowHistory(skill)) == 0 {
			t.Errorf("no release history for %s", skill)
		}
	}
}
