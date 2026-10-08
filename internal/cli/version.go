package cli

import (
	"fmt"
	"runtime/debug"
	"strings"
)

// BuildInfo identifies the running binary.
type BuildInfo struct {
	Version string // "v1.4.0", "dev", ...
	Commit  string // "" when unknown
	Date    string // "" when unknown
}

var build = BuildInfo{Version: "dev"}

// SetBuildInfo records the version injected at build time (-ldflags -X).
// Values left at their defaults ("dev", "unknown", "") are filled from the
// module build information, so `go install ...@latest` reports the module
// version and VCS builds report the commit and its time.
func SetBuildInfo(version, commit, date string) {
	build = resolveBuildInfo(version, commit, date, debug.ReadBuildInfo)
}

func resolveBuildInfo(version, commit, date string, read func() (*debug.BuildInfo, bool)) BuildInfo {
	unset := func(s string) bool { return s == "" || s == "unknown" || s == "dev" }
	b := BuildInfo{Version: version, Commit: commit, Date: date}
	if info, ok := read(); ok && info != nil {
		if unset(b.Version) && info.Main.Version != "" && info.Main.Version != "(devel)" {
			b.Version = info.Main.Version
		}
		for _, s := range info.Settings {
			switch {
			case s.Key == "vcs.revision" && unset(b.Commit):
				b.Commit = s.Value
				if len(b.Commit) > 12 {
					b.Commit = b.Commit[:12]
				}
			case s.Key == "vcs.time" && unset(b.Date):
				b.Date = s.Value
			}
		}
	}
	if unset(b.Version) {
		b.Version = "dev"
	}
	if unset(b.Commit) {
		b.Commit = ""
	}
	if unset(b.Date) {
		b.Date = ""
	}
	return b
}

// Version is the think-better version recorded in install manifests.
func Version() string {
	return build.Version
}

// VersionString is the one-line version banner.
func VersionString() string {
	s := "think-better " + build.Version
	var extra []string
	for _, v := range []string{build.Commit, build.Date} {
		if v != "" {
			extra = append(extra, v)
		}
	}
	if len(extra) > 0 {
		s += " (" + strings.Join(extra, " ") + ")"
	}
	return s
}

// RunVersion handles the "version" subcommand.
func RunVersion(args []string) int {
	flags := newFlagSet("version")
	if ok, code := parseFlags(flags, args, "Show version information.\n\nUsage:\n  think-better version"); !ok {
		return code
	}
	_, _ = fmt.Fprintln(stdout, VersionString())
	return 0
}
