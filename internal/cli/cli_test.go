package cli

import (
	"bufio"
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"runtime/debug"
	"strings"
	"testing"

	"github.com/HoangTheQuyen/think-better/internal/checker"
	"github.com/HoangTheQuyen/think-better/internal/installer"
)

// testEnv runs commands in a temporary project with a temporary home
// directory, capturing output, with Python reported as present and no
// terminal attached.
type testEnv struct {
	t             *testing.T
	project, home string
	out, err      bytes.Buffer
	python        bool
}

func newEnv(t *testing.T) *testEnv {
	t.Helper()
	e := &testEnv{t: t, project: t.TempDir(), home: t.TempDir(), python: true}
	// A repository root: commands never look for installs above it.
	if err := os.Mkdir(filepath.Join(e.project, ".git"), 0o755); err != nil {
		t.Fatal(err)
	}
	t.Chdir(e.project)
	t.Setenv("HOME", e.home)
	t.Setenv("USERPROFILE", e.home) // Windows
	t.Setenv("THINK_BETTER_AI", "")
	t.Setenv("MAKE_DECISION_AI", "")

	oldOut, oldErr, oldPy, oldInteractive, oldReader := stdout, stderr, checkPython, interactive, stdinReader
	stdout, stderr = &e.out, &e.err
	checkPython = func() checker.PythonResult {
		if !e.python {
			return checker.PythonResult{}
		}
		return checker.PythonResult{Found: true, Version: "3.12.0", Path: "/usr/bin/python3"}
	}
	interactive = func() bool { return false }
	t.Cleanup(func() {
		stdout, stderr, checkPython, interactive, stdinReader = oldOut, oldErr, oldPy, oldInteractive, oldReader
	})
	return e
}

// run runs a command and returns its exit code; output is in e.out / e.err.
func (e *testEnv) run(cmd func([]string) int, args ...string) int {
	e.t.Helper()
	e.out.Reset()
	e.err.Reset()
	return cmd(args)
}

// mustRun fails the test unless the command exits with want.
func (e *testEnv) mustRun(want int, cmd func([]string) int, args ...string) {
	e.t.Helper()
	if got := e.run(cmd, args...); got != want {
		e.t.Fatalf("%v: exit %d, want %d\nstdout:\n%s\nstderr:\n%s", args, got, want, e.out.String(), e.err.String())
	}
}

// answer makes the session interactive, with input as the user's answers.
func (e *testEnv) answer(input string) {
	interactive = func() bool { return true }
	stdinReader = bufio.NewReader(strings.NewReader(input))
}

func (e *testEnv) file(parts ...string) string {
	return filepath.Join(append([]string{e.project}, parts...)...)
}

func (e *testEnv) write(path, content string) {
	e.t.Helper()
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		e.t.Fatal(err)
	}
}

func (e *testEnv) read(path string) string {
	e.t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		e.t.Fatal(err)
	}
	return string(data)
}

// simulateOld makes a file of an installed skill look like it came from an
// older release (manifest hash of old), with the user's content on disk.
func (e *testEnv) simulateOld(skillDir, rel, old, onDisk string) {
	e.t.Helper()
	mpath := filepath.Join(skillDir, installer.SkillManifestName)
	var m installer.SkillManifest
	if err := json.Unmarshal([]byte(e.read(mpath)), &m); err != nil {
		e.t.Fatal(err)
	}
	m.Files[rel] = sha([]byte(old))
	data, _ := json.Marshal(m)
	e.write(mpath, string(data))
	e.write(filepath.Join(skillDir, filepath.FromSlash(rel)), onDisk)
}

func sha(data []byte) string {
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:])
}

func exists(path string) bool {
	_, err := os.Lstat(path)
	return err == nil
}

func TestHelpExitsZero(t *testing.T) {
	e := newEnv(t)
	cmds := map[string]func([]string) int{
		"init": RunInit, "update": RunUpdate, "list": RunList,
		"uninstall": RunUninstall, "check": RunCheck, "version": RunVersion,
	}
	for name, cmd := range cmds {
		for _, flag := range []string{"--help", "-h"} {
			if code := e.run(cmd, flag); code != 0 {
				t.Errorf("%s %s: exit %d, want 0", name, flag, code)
			}
			if !strings.Contains(e.out.String(), "Usage:") || e.err.Len() != 0 {
				t.Errorf("%s %s: usage should go to stdout only\nstdout: %s\nstderr: %s", name, flag, e.out.String(), e.err.String())
			}
		}
	}
}

func TestBadArguments(t *testing.T) {
	e := newEnv(t)
	e.mustRun(1, RunInit, "claude")
	if !strings.Contains(e.err.String(), "did you mean --ai claude") {
		t.Errorf("stderr = %q", e.err.String())
	}
	e.mustRun(1, RunList, "extra")
	e.mustRun(1, RunCheck, "--bogus")
	if !strings.Contains(e.err.String(), "think-better check --help") {
		t.Errorf("stderr = %q", e.err.String())
	}
	e.mustRun(1, RunInit, "--ai", "nope")
	e.mustRun(1, RunInit, "--ai", "claude", "--skill", "nope")
	e.mustRun(1, RunUpdate, "--ai", "nope")
	e.mustRun(1, RunUninstall, "--ai", "claude")
}

func TestInitNeedsTargetWhenNonInteractive(t *testing.T) {
	e := newEnv(t)
	e.mustRun(1, RunInit)
	if !strings.Contains(e.err.String(), "--ai is required") {
		t.Errorf("stderr = %q", e.err.String())
	}

	t.Setenv("THINK_BETTER_AI", "bogus")
	e.mustRun(1, RunInit)
	if !strings.Contains(e.err.String(), "THINK_BETTER_AI") {
		t.Errorf("stderr = %q", e.err.String())
	}

	t.Setenv("THINK_BETTER_AI", "opencode")
	e.mustRun(0, RunInit, "--skill", "make-decision")
	if !exists(e.file(".opencode", "skills", "make-decision", "SKILL.md")) {
		t.Error("THINK_BETTER_AI target not used")
	}
}

func TestInitPromptsForTarget(t *testing.T) {
	e := newEnv(t)
	e.answer("2\n")
	e.mustRun(0, RunInit, "--skill", "make-decision")
	if !exists(e.file(".github", "skills", "make-decision", "SKILL.md")) {
		t.Error("choice 2 (copilot) not installed")
	}
}

func TestInitAgainUpdates(t *testing.T) {
	e := newEnv(t)
	e.mustRun(0, RunInit, "--ai", "claude")
	if !strings.Contains(e.out.String(), "Next steps") {
		t.Errorf("first install output:\n%s", e.out.String())
	}

	// Plain init on an existing install is not an error any more.
	e.mustRun(0, RunInit, "--ai", "claude")
	if !strings.Contains(e.out.String(), "is up to date") {
		t.Errorf("reinstall output:\n%s", e.out.String())
	}

	dir := e.file(".claude", "skills", "code-solving")
	want := e.read(filepath.Join(dir, "PROMPT.md"))
	e.simulateOld(dir, "PROMPT.md", "old", "mine")
	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "code-solving")
	if e.read(filepath.Join(dir, "PROMPT.md")) != "mine" || e.read(filepath.Join(dir, "PROMPT.md.new")) != want {
		t.Error("init should keep the user's file and write PROMPT.md.new")
	}
	if !strings.Contains(e.out.String(), "new version saved as .claude/skills/code-solving/PROMPT.md.new") {
		t.Errorf("output:\n%s", e.out.String())
	}

	// --force keeps a backup and says so.
	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "code-solving", "--force")
	if e.read(filepath.Join(dir, "PROMPT.md")) != want || e.read(filepath.Join(dir, "PROMPT.md.bak")) != "mine" {
		t.Error("--force should replace PROMPT.md and back it up")
	}
	if !strings.Contains(e.out.String(), "your version saved as .claude/skills/code-solving/PROMPT.md.bak") {
		t.Errorf("output:\n%s", e.out.String())
	}
}

func TestInitDryRun(t *testing.T) {
	e := newEnv(t)
	e.mustRun(0, RunInit, "--ai", "claude", "--dry-run")
	if exists(e.file(".claude")) {
		t.Error("dry run wrote files")
	}
	if !strings.Contains(e.out.String(), "Would create") {
		t.Errorf("output:\n%s", e.out.String())
	}
}

func TestUpdateCommand(t *testing.T) {
	e := newEnv(t)
	e.mustRun(0, RunUpdate)
	if !strings.Contains(e.out.String(), "No installed skills found") {
		t.Errorf("output:\n%s", e.out.String())
	}
	e.mustRun(1, RunUpdate, "--skill", "code-solving")

	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "code-solving")
	e.mustRun(0, RunInit, "--ai", "opencode", "--skill", "code-solving", "--global")
	project := e.file(".claude", "skills", "code-solving")
	global := filepath.Join(e.home, ".config", "opencode", "skills", "code-solving")
	wantProject := e.read(filepath.Join(project, "SKILL.md"))
	wantGlobal := e.read(filepath.Join(global, "SKILL.md"))
	e.simulateOld(project, "SKILL.md", "old", "old")
	e.simulateOld(global, "SKILL.md", "old", "old")

	e.mustRun(0, RunUpdate, "--dry-run")
	if e.read(filepath.Join(project, "SKILL.md")) != "old" || !strings.Contains(e.out.String(), "Would update") {
		t.Errorf("dry run changed files or did not report:\n%s", e.out.String())
	}

	e.mustRun(1, RunUpdate, "--ai", "copilot")

	e.mustRun(0, RunUpdate, "--global")
	if e.read(filepath.Join(global, "SKILL.md")) != wantGlobal || e.read(filepath.Join(project, "SKILL.md")) != "old" {
		t.Error("--global should update only the global install")
	}

	e.mustRun(0, RunUpdate)
	if e.read(filepath.Join(project, "SKILL.md")) != wantProject {
		t.Error("project install not updated")
	}
	if !strings.Contains(e.out.String(), "opencode (global)") {
		t.Errorf("output should mention every location:\n%s", e.out.String())
	}
}

func TestUninstallCommand(t *testing.T) {
	e := newEnv(t)
	e.mustRun(1, RunUninstall, "--ai", "claude", "--skill", "code-solving")

	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "code-solving", "--global")
	e.mustRun(1, RunUninstall, "--ai", "claude", "--skill", "code-solving")
	if !strings.Contains(e.err.String(), "add --global") {
		t.Errorf("should suggest --global:\n%s", e.err.String())
	}

	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "code-solving")
	e.mustRun(1, RunUninstall, "--ai", "claude", "--skill", "code-solving")
	if !strings.Contains(e.err.String(), "--yes") {
		t.Errorf("non-interactive uninstall should require --yes:\n%s", e.err.String())
	}

	dir := e.file(".claude", "skills", "code-solving")
	e.answer("n\n")
	e.mustRun(0, RunUninstall, "--ai", "claude", "--skill", "code-solving")
	if !strings.Contains(e.out.String(), "Canceled") || !exists(filepath.Join(dir, "SKILL.md")) {
		t.Error("answering no should cancel")
	}

	e.write(filepath.Join(dir, "SKILL.md"), "my notes")
	e.mustRun(0, RunUninstall, "--ai", "claude", "--skill", "code-solving", "--dry-run")
	if !exists(filepath.Join(dir, "PROMPT.md")) {
		t.Error("dry run removed files")
	}

	e.answer("y\n")
	e.mustRun(0, RunUninstall, "--ai", "claude", "--skill", "code-solving")
	if exists(filepath.Join(dir, "PROMPT.md")) || e.read(filepath.Join(dir, "SKILL.md")) != "my notes" {
		t.Error("uninstall should remove unmodified files and keep modified ones")
	}
	if !strings.Contains(e.out.String(), "Kept .claude/skills/code-solving/SKILL.md") {
		t.Errorf("output:\n%s", e.out.String())
	}

	e.mustRun(0, RunUninstall, "--ai", "claude", "--skill", "code-solving", "--global", "--force")
	if exists(filepath.Join(e.home, ".claude", "skills")) {
		t.Error("global uninstall should remove the emptied skills directory")
	}
	if !exists(filepath.Join(e.home, ".claude")) {
		t.Error("~/.claude must be kept")
	}
}

func TestCheckCommand(t *testing.T) {
	e := newEnv(t)
	// Nothing installed is not a failure.
	e.mustRun(0, RunCheck)
	if !strings.Contains(e.out.String(), "not installed") {
		t.Errorf("output:\n%s", e.out.String())
	}

	e.python = false
	e.mustRun(1, RunCheck)
	e.python = true

	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "code-solving")
	dir := e.file(".claude", "skills", "code-solving")
	e.write(filepath.Join(dir, "data", "steps.csv"), "mine")
	e.mustRun(0, RunCheck)
	if !strings.Contains(e.out.String(), "1 file modified") {
		t.Errorf("output:\n%s", e.out.String())
	}

	e.simulateOld(dir, "SKILL.md", "old", "old")
	e.mustRun(0, RunCheck)
	if !strings.Contains(e.out.String(), "outdated") || !strings.Contains(e.out.String(), "think-better update --ai claude --skill code-solving") {
		t.Errorf("output:\n%s", e.out.String())
	}
	e.mustRun(1, RunCheck, "--strict")

	e.mustRun(0, RunCheck, "--json")
	var out checkOutput
	if err := json.Unmarshal(e.out.Bytes(), &out); err != nil {
		t.Fatalf("invalid JSON: %v\n%s", err, e.out.String())
	}
	if !out.OK || !out.Python.Found || len(out.Skills) == 0 {
		t.Errorf("check JSON = %+v", out)
	}
	for _, s := range out.Skills {
		if s.Name != "code-solving" {
			if s.Installed {
				t.Errorf("%s reported installed", s.Name)
			}
			continue
		}
		if len(s.Locations) != 1 {
			t.Fatalf("locations = %+v", s.Locations)
		}
		loc := s.Locations[0]
		if loc.Status != "outdated" || loc.Target != "claude" || loc.Scope != "project" || len(loc.Modified) != 1 || !loc.Manifest {
			t.Errorf("location = %+v", loc)
		}
	}

	if err := os.Remove(filepath.Join(dir, "scripts", "core.py")); err != nil {
		t.Fatal(err)
	}
	e.mustRun(1, RunCheck, "--json")
	if err := json.Unmarshal(e.out.Bytes(), &out); err != nil || out.OK {
		t.Errorf("incomplete install should fail: %v %+v", err, out)
	}
}

func TestListCommand(t *testing.T) {
	e := newEnv(t)
	e.mustRun(0, RunInit, "--ai", "claude", "--skill", "code-solving")
	e.mustRun(0, RunInit, "--ai", "opencode", "--skill", "code-solving", "--global")
	e.write(e.file(".claude", "skills", "code-solving", "SKILL.md"), "mine")

	e.mustRun(0, RunList)
	if !strings.Contains(e.out.String(), "claude [1 modified file], opencode (global)") {
		t.Errorf("table:\n%s", e.out.String())
	}

	e.mustRun(0, RunList, "--json")
	var out listOutput
	if err := json.Unmarshal(e.out.Bytes(), &out); err != nil {
		t.Fatal(err)
	}
	for _, s := range out.Skills {
		if s.Name != "code-solving" {
			if s.Status != "not-installed" || len(s.Locations) != 0 {
				t.Errorf("%s = %+v", s.Name, s)
			}
			continue
		}
		if s.Status != "installed" || len(s.Locations) != 2 {
			t.Fatalf("code-solving = %+v", s)
		}
		if l := s.Locations[0]; l.Status != "modified" || l.Modified[0] != ".claude/skills/code-solving/SKILL.md" {
			t.Errorf("project location = %+v", l)
		}
		if l := s.Locations[1]; l.Scope != "global" || l.Status != "installed" || l.Path != "~/.config/opencode/skills/code-solving/" {
			t.Errorf("global location = %+v", l)
		}
	}
}

func TestEncodeJSONDoesNotEscapeHTML(t *testing.T) {
	var buf bytes.Buffer
	if err := encodeJSON(&buf, map[string]string{"d": "a <b> & c"}); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(buf.String(), "a <b> & c") {
		t.Errorf("got %s", buf.String())
	}
}

func TestIsTerminal(t *testing.T) {
	null, err := os.Open(os.DevNull)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = null.Close() }()
	if isTerminal(null.Fd()) {
		t.Error("the null device is not a terminal")
	}
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = r.Close(); _ = w.Close() }()
	if isTerminal(r.Fd()) {
		t.Error("a pipe is not a terminal")
	}
}

func TestConfirmNeverPromptsWhenNonInteractive(t *testing.T) {
	e := newEnv(t)
	stdinReader = bufio.NewReader(strings.NewReader("y\n"))
	if confirm("Proceed?") || e.err.Len() != 0 {
		t.Error("confirm must not prompt without a terminal")
	}
	if promptChoice("Pick", []string{"a"}) != "" {
		t.Error("promptChoice must not prompt without a terminal")
	}
	e.answer("YES\n")
	if !confirm("Proceed?") {
		t.Error("confirm should accept YES")
	}
}

func TestResolveBuildInfo(t *testing.T) {
	info := &debug.BuildInfo{
		Main: debug.Module{Version: "v1.4.0"},
		Settings: []debug.BuildSetting{
			{Key: "vcs.revision", Value: "0123456789abcdef0123"},
			{Key: "vcs.time", Value: "2026-01-02T03:04:05Z"},
		},
	}
	read := func() (*debug.BuildInfo, bool) { return info, true }

	b := resolveBuildInfo("dev", "unknown", "unknown", read)
	if b.Version != "v1.4.0" || b.Commit != "0123456789ab" || b.Date != "2026-01-02T03:04:05Z" {
		t.Errorf("from build info: %+v", b)
	}
	b = resolveBuildInfo("v2.0.0", "abc1234", "2026-02-02", read)
	if b.Version != "v2.0.0" || b.Commit != "abc1234" || b.Date != "2026-02-02" {
		t.Errorf("ldflags must win: %+v", b)
	}
	info.Main.Version = "(devel)"
	info.Settings = nil
	b = resolveBuildInfo("dev", "unknown", "unknown", read)
	if b.Version != "dev" || b.Commit != "" || b.Date != "" {
		t.Errorf("no info: %+v", b)
	}
	b = resolveBuildInfo("", "", "", func() (*debug.BuildInfo, bool) { return nil, false })
	if b.Version != "dev" {
		t.Errorf("unreadable info: %+v", b)
	}
}

func TestVersionCommand(t *testing.T) {
	e := newEnv(t)
	old := build
	t.Cleanup(func() { build = old })
	build = BuildInfo{Version: "v9.9.9", Commit: "abc", Date: "2026-01-01"}
	e.mustRun(0, RunVersion)
	if strings.TrimSpace(e.out.String()) != "think-better v9.9.9 (abc 2026-01-01)" {
		t.Errorf("version = %q", e.out.String())
	}
	build = BuildInfo{Version: "v9.9.9"}
	if VersionString() != "think-better v9.9.9" {
		t.Errorf("VersionString = %q", VersionString())
	}
	e.mustRun(1, RunVersion, "extra")
}
