// Missing from wasi-sdk. See stubs/net/if.h: only needed if the bundled
// cpp-httplib is re-enabled. Provides the address-resolution types cpp-httplib
// references; the functions are never called under -DDUCKDB_DISABLE_BUILTIN_HTTPLIB
// and are left undefined (link with -Wl,--allow-undefined).
#pragma once
#include <sys/socket.h>

struct addrinfo {
  int ai_flags, ai_family, ai_socktype, ai_protocol;
  socklen_t ai_addrlen;
  struct sockaddr *ai_addr;
  char *ai_canonname;
  struct addrinfo *ai_next;
};
struct hostent {
  char *h_name;
  char **h_aliases;
  int h_addrtype, h_length;
  char **h_addr_list;
};

int getaddrinfo(const char *, const char *, const struct addrinfo *, struct addrinfo **);
void freeaddrinfo(struct addrinfo *);
const char *gai_strerror(int);
int getnameinfo(const struct sockaddr *, socklen_t, char *, socklen_t, char *, socklen_t, int);

#define AI_PASSIVE 1
#define AI_NUMERICHOST 4
#define AI_NUMERICSERV 16
#define NI_NUMERICHOST 1
#define NI_NUMERICSERV 2
#define NI_MAXHOST 1025
#define NI_MAXSERV 32
#define EAI_NONAME -2
