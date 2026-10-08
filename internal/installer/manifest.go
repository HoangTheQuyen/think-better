package installer

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

// Install manifests record what think-better wrote, so later runs can tell
// files the user edited from files it may safely replace or delete.
//
// Skill manifest: one per skill install directory, e.g.
// .claude/skills/<skill>/.think-better.json
//
//	{
//	  "version": "v1.4.0",            // think-better version that wrote it
//	  "skill": "code-solving",
//	  "target": "claude",
//	  "files": {"SKILL.md": "<sha256>", "scripts/search.py": "<sha256>"}
//	}
//
// Workflow manifest: one per workflow (slash command) directory, shared by
// every skill whose commands live there, e.g. .claude/commands/.think-better-workflows.json
//
//	{
//	  "version": "v1.4.0",
//	  "target": "claude",
//	  "files": {"code.md": {"skill": "code-solving", "sha256": "<sha256>"}}
//	}
//
// File paths are slash-separated and relative to the directory holding the
// manifest. Hashes are the SHA-256 of the content as written for that target
// (after path rewriting). For a file the user had modified and kept, the hash
// is the version think-better offered (written next to it as <file>.new), so
// the file keeps reading as modified until the user resolves it.
//
// Installs made before manifests existed ("legacy" installs) are handled by
// comparing each file with the content the current binary would write and
// with what every earlier release installed (known_hashes.json): a match
// counts as unmodified, anything else as modified by the user.
//
// When uninstall keeps files the user modified, the skill manifest stays
// behind as a tombstone ("uninstalled": true, listing the kept files with the
// hashes think-better had installed), so the leftovers are not mistaken for
// a damaged install.
const (
	SkillManifestName    = ".think-better.json"
	WorkflowManifestName = ".think-better-workflows.json"
)

// SkillManifest is the record of one installed skill.
type SkillManifest struct {
	Version string            `json:"version"`
	Skill   string            `json:"skill"`
	Target  string            `json:"target"`
	Files   map[string]string `json:"files"`
	// Uninstalled marks a tombstone: the skill was uninstalled and Files
	// lists only the modified files that were kept.
	Uninstalled bool `json:"uninstalled,omitempty"`
}

// WorkflowEntry records one installed workflow file and the skill it runs.
type WorkflowEntry struct {
	Skill  string `json:"skill"`
	SHA256 string `json:"sha256"`
}

// WorkflowManifest is the record of the workflows think-better wrote to a directory.
type WorkflowManifest struct {
	Version string                   `json:"version"`
	Target  string                   `json:"target"`
	Files   map[string]WorkflowEntry `json:"files"`
	Exclude []string                 `json:"exclude,omitempty"` // workflows not to install (see exclude.go)
}

// hashBytes returns the hex SHA-256 of data.
func hashBytes(data []byte) string {
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:])
}

// validRel reports whether a manifest path is a plain relative path that
// stays inside the manifest's directory. Anything else is ignored, so a
// tampered manifest cannot make think-better touch files elsewhere.
func validRel(rel string) bool {
	if rel == "" || rel == "." || strings.Contains(rel, `\`) || path.Clean(rel) != rel {
		return false
	}
	return filepath.IsLocal(filepath.FromSlash(rel))
}

// readSkillManifest loads dir/.think-better.json. It returns nil (and no
// error) when the file is missing or unreadable as JSON: the install is then
// treated as a legacy install.
func readSkillManifest(base, dirRel string) (*SkillManifest, error) {
	data, err := readRegular(base, path.Join(dirRel, SkillManifestName))
	if err != nil || data == nil {
		return nil, err
	}
	var m SkillManifest
	if json.Unmarshal(data, &m) != nil {
		return nil, nil
	}
	files := map[string]string{}
	for rel, h := range m.Files {
		if validRel(rel) && rel != SkillManifestName {
			files[rel] = h
		}
	}
	m.Files = files
	return &m, nil
}

// readWorkflowManifest loads dir/.think-better-workflows.json; nil when absent or invalid.
func readWorkflowManifest(base, dirRel string) (*WorkflowManifest, error) {
	data, err := readRegular(base, path.Join(dirRel, WorkflowManifestName))
	if err != nil || data == nil {
		return nil, err
	}
	var m WorkflowManifest
	if json.Unmarshal(data, &m) != nil {
		return nil, nil
	}
	files := map[string]WorkflowEntry{}
	for rel, e := range m.Files {
		if validRel(rel) && rel != WorkflowManifestName {
			files[rel] = e
		}
	}
	m.Files = files
	return &m, nil
}

// writeManifest writes v as indented JSON to base/rel, atomically.
func writeManifest(base, rel string, v any) error {
	data, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	return writeFileSafe(base, rel, append(data, '\n'), 0o644)
}

// readRegular reads base/rel without following symlinks anywhere below base.
// It returns (nil, nil) when the file does not exist.
func readRegular(base, rel string) ([]byte, error) {
	full, err := checkPath(base, rel)
	if err != nil {
		return nil, err
	}
	fi, err := os.Lstat(full)
	if errors.Is(err, fs.ErrNotExist) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if !isFileLike(fi.Mode()) {
		return nil, fmt.Errorf("refusing to use %s: not a regular file", full)
	}
	data, err := os.ReadFile(full)
	if err == nil && data == nil {
		data = []byte{} // exists but empty: distinct from "missing"
	}
	return data, err
}

// sortedKeys returns the keys of m in order.
func sortedKeys[V any](m map[string]V) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

// versionOlder reports whether version a is older than b. Versions are
// compared as semantic versions ("v1.2.3", optional pre-release suffix);
// when either is not a release-style version ("dev", a commit hash) it
// returns false and callers fall back to comparing content.
//
// `git describe` versions of development builds (`make build`), such as
// v1.4.0-3-gabc1234 or v1.4.0-dirty, are commits after v1.4.0: newer than
// v1.4.0 and older than the next release, not a v1.4.0 pre-release.
func versionOlder(a, b string) bool {
	va, okA := parseVersion(a)
	vb, okB := parseVersion(b)
	if !okA || !okB {
		return false
	}
	for i := 0; i < 3; i++ {
		if va.core[i] != vb.core[i] {
			return va.core[i] < vb.core[i]
		}
	}
	// v1.2.3-rc1 < v1.2.3-rc1-2-gabc < v1.2.3 < v1.2.3-2-gabc
	return va.rank() < vb.rank()
}

type semver struct {
	core [3]int
	pre  bool // pre-release (v1.2.3-rc1)
	post bool // git describe: commits after the tag (v1.2.3-4-gabc1234, -dirty)
}

func (s semver) rank() int {
	r := 0
	if !s.pre {
		r += 2
	}
	if s.post {
		r++
	}
	return r
}

// gitDescribe matches the suffix `git describe --tags --dirty` adds after
// the tag name: -<commits>-g<hash> and/or -dirty.
var gitDescribe = regexp.MustCompile(`(-[0-9]+-g[0-9a-f]+)?(-dirty)?$`)

func parseVersion(v string) (semver, bool) {
	v = strings.TrimPrefix(strings.TrimSpace(v), "v")
	v, _, _ = strings.Cut(v, "+")
	var s semver
	if loc := gitDescribe.FindStringIndex(v); loc != nil && loc[0] < loc[1] {
		v, s.post = v[:loc[0]], true
	}
	core, pre, hasPre := strings.Cut(v, "-")
	parts := strings.Split(core, ".")
	if len(parts) != 3 {
		return semver{}, false
	}
	for i, p := range parts {
		n, err := strconv.Atoi(p)
		if err != nil || n < 0 {
			return semver{}, false
		}
		s.core[i] = n
	}
	s.pre = hasPre && pre != ""
	return s, true
}
