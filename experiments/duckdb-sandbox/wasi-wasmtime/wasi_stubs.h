// POSIX bits DuckDB core references that wasi-libc does not provide. These are
// all in code paths a sandboxed catalog query never takes (file locking on the
// local filesystem, terminal size, CPU affinity), so stubbing the declarations
// is enough. Force-included via -include on the compile line.
#pragma once
#include <fcntl.h>

#ifndef F_SETLK
#define F_GETLK 5
#define F_SETLK 6
#define F_SETLKW 7
#endif

#ifndef TIOCGWINSZ
#define TIOCGWINSZ 0x5413
struct winsize {
  unsigned short ws_row, ws_col, ws_xpixel, ws_ypixel;
};
#endif

#ifndef MADV_DONTNEED
#define MADV_DONTNEED 4
#define MADV_NORMAL 0
#define MADV_RANDOM 1
extern "C" int madvise(void *, unsigned long, int);
#endif

#ifndef F_RDLCK
#define F_RDLCK 0
#define F_WRLCK 1
#define F_UNLCK 2
#endif

extern "C" int sched_getcpu(void);
