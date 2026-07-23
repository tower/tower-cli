// Missing from wasi-sdk. Only pulled in when the bundled cpp-httplib is
// compiled; the build excludes that with -DDUCKDB_DISABLE_BUILTIN_HTTPLIB, so
// these declarations exist just in case httplib is re-enabled. Searched via
// -idirafter so real wasi-sdk headers always win where they exist.
#pragma once
unsigned int if_nametoindex(const char *);
char *if_indextoname(unsigned int, char *);
