package installer

import (
	_ "embed"
	"encoding/json"
	"sync"
)

// known_hashes.json records, for every released version, the SHA-256 of each
// file that version installed (for every target and scope, after its path
// rewriting). It lets think-better tell a file the user edited from one a
// release wrote, even in installs made before manifests existed.
// Regenerate it with `make known-hashes` (go run ./internal/installer/gen).
//
//go:embed known_hashes.json
var knownHashesJSON []byte

// shipped is what released versions installed for one skill: file path
// (relative to the skill or workflow directory) -> SHA-256 -> versions.
type shipped map[string]map[string][]string

// has reports whether a release installed rel with content hash.
func (s shipped) has(rel, hash string) bool {
	_, ok := s[rel][hash]
	return ok
}

// versions returns the releases that installed rel (any content).
func (s shipped) versions(rel string) map[string]bool {
	out := map[string]bool{}
	for _, vs := range s[rel] {
		for _, v := range vs {
			out[v] = true
		}
	}
	return out
}

// alwaysShipped reports whether every release that had this skill also
// installed rel, so even the oldest install of the skill should have it.
func (s shipped) alwaysShipped(rel string) bool {
	all := map[string]bool{}
	for f := range s {
		for v := range s.versions(f) {
			all[v] = true
		}
	}
	return len(all) > 0 && len(s.versions(rel)) == len(all)
}

type knownHashes struct {
	Versions  []string           `json:"versions"`
	Skills    map[string]shipped `json:"skills"`
	Workflows map[string]shipped `json:"workflows"`
}

var loadKnownHashes = sync.OnceValue(func() *knownHashes {
	var kh knownHashes
	if err := json.Unmarshal(knownHashesJSON, &kh); err != nil {
		panic("installer: invalid known_hashes.json: " + err.Error())
	}
	return &kh
})

// skillHistory returns what released versions installed for skill's files.
func skillHistory(skill string) shipped {
	return loadKnownHashes().Skills[skill]
}

// workflowHistory returns what released versions installed as workflows for skill.
func workflowHistory(skill string) shipped {
	return loadKnownHashes().Workflows[skill]
}
