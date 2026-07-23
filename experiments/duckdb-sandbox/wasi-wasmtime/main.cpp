// Minimal viability harness: open an in-memory DuckDB and run a query. Proves
// the wasm32-wasi build actually executes SQL in wasmtime. maximum_threads = 1
// pairs with -DDUCKDB_NO_THREADS so no background thread pool is created.
#include "duckdb.hpp"
#include <cstdio>

int main() {
  try {
    duckdb::DBConfig config;
    config.options.maximum_threads = 1;
    duckdb::DuckDB db(nullptr, &config);
    duckdb::Connection con(db);
    auto r = con.Query("SELECT 42 + count(*) AS answer FROM range(1000)");
    if (r->HasError()) {
      printf("QUERY_ERR: %s\n", r->GetError().c_str());
      return 1;
    }
    printf("DUCKDB_WASI_RESULT=%s\n", r->GetValue(0, 0).ToString().c_str());
  } catch (const std::exception &e) {
    printf("EXC: %s\n", e.what());
    return 2;
  }
  return 0;
}
