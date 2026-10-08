package cli

import "syscall"

// isTerminal reports whether fd is a console. GetConsoleMode fails for
// NUL, files and pipes.
func isTerminal(fd uintptr) bool {
	var mode uint32
	return syscall.GetConsoleMode(syscall.Handle(fd), &mode) == nil
}
