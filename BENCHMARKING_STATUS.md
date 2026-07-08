# Benchmarking Status

Tracks indexing-performance benchmark runs over time. Each row is a commit;
each column is a file-count scenario run against it with `benchmark.py
--num-files N`. Add a column the first time a new N is benchmarked, and fill
in the cell for every commit tested at that N. Raw data lives in
`backend/benchmarking/benchmarks/results.csv`.

Cells show `total_s (chunks/s)`.

| Commit | Note | 1 file (~32 chunks) | 10 files (~2036 chunks) |
|---|---|---|---|---|
| 4d5d35e | baseline | 1.034s (30.94) | 69.753s (29.19) |
| 1b7a9db | Send all chunks together, rather than one at at time |  0.815s (39.2) | 53.871s (37.8)

## Improvement

| Commit | Note | 1 file (~32 chunks) | 10 files (~2036 chunks) | Speedup vs Baseline | Speedup vs Prev. Commit
|---|---|---|---|---|
| 4d5d35e | baseline | 1.034s (30.94) | 69.753s (29.19) | N/A | N/A
| 1b7a9db | Send all chunks together, rather than one at at time |  0.815s (39.2) | 53.871s (37.8) | 1.267 | 1.295

