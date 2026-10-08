//go:build linux || darwin || freebsd

package cli

import (
	"syscall"
	"unsafe"
)

// isTerminal reports whether fd is a terminal: the terminal-attributes
// ioctl succeeds only on a tty, not on /dev/null, files or pipes (a plain
// character-device check would accept /dev/null).
func isTerminal(fd uintptr) bool {
	var t syscall.Termios
	_, _, errno := syscall.Syscall(syscall.SYS_IOCTL, fd, ioctlReadTermios, uintptr(unsafe.Pointer(&t)))
	return errno == 0
}
