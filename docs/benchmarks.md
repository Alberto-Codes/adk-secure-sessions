# Benchmarks

## Why Benchmarks

adk-secure-sessions adds field-level encryption to every ADK session operation. NFR1 requires that this encryption overhead stays below 20% of total operation time — fast enough that developers don't have to choose between security and performance.

This page documents the performance characteristics of each encryption backend so you can make an informed choice based on real data, not assumptions.

## Methodology

All benchmarks use the same measurement approach:

- **Timer**: `time.perf_counter()` for high-resolution wall-clock timing
- **Iterations**: 30 per measurement (meets the Central Limit Theorem threshold for reliable estimates)
- **Batch size**: 10 round-trips per timing sample — produces ~20ms samples, well above the ~10ms threshold where `perf_counter()` gives stable results. Individual ~2ms operations are too short relative to OS scheduling noise (~0.5-2ms)
- **Interleaved measurement**: Baseline and encrypted batches alternate on each iteration to cancel out time-varying system effects (CPU throttling, SQLite page-cache drift). Per-pair overhead ratios are computed, then the median of those ratios is reported — preserving the pairing information for maximum noise rejection
- **Warm-up**: 5 passes before measurement to stabilize SQLite's page cache and eliminate cold-start effects
- **Payloads**: Four representative sizes — empty dict (`{}`), ~1KB, ~10KB, ~100KB — covering the range from minimal sessions to 10x realistic payloads
- **Environment modes**:
    - **Local**: Hard assertion failure if AES-256-GCM round-trip overhead exceeds 1.20x (developer feedback). Fernet tests are informational (warn-only) — see below
    - **CI** (`CI=true`): Emits a warning but passes (shared runner hardware varies too much for hard assertions)

### Why not pytest-benchmark?

The `pytest-benchmark` plugin expects synchronous callables. Since all adk-secure-sessions APIs are `async def`, using it would require `asyncio.run()` wrappers that add measurement artifacts and misrepresent actual async performance. We use direct `time.perf_counter()` instrumentation instead.

## Backend Comparison

Results below are **relative ratios**, not absolute times. Ratios are more stable across hardware than raw timings, but they do vary depending on CPU instruction set support (AES-NI, CLMUL, ARMv8 crypto extensions). Run the benchmarks on your own hardware for accurate values.

### Encryption Speed (Fernet / AES-256-GCM ratio)

Measured on AMD Ryzen AI 9 HX 370 (x86_64, AES-NI + VAES + CLMUL). On CPUs without vectorized AES instructions, expect smaller ratios at large payload sizes.

| Payload Size | Encrypt | Decrypt |
|-------------|---------|---------|
| Empty       | ~1.4x   | ~1.5x   |
| 1 KB        | ~1.5x   | ~1.5x   |
| 10 KB       | ~2.5x   | ~2.5x   |
| 100 KB      | ~28x    | ~10x    |

!!! note "Ratios are approximate"
    The trend is consistent across hardware: AES-256-GCM is faster than
    Fernet, and the gap widens significantly at larger payload sizes. The
    exact ratios depend on hardware crypto acceleration — CPUs with VAES
    (vectorized AES) show larger gaps because AES-GCM's counter mode is
    parallelizable while Fernet's CBC mode is inherently sequential.

### Key Observations

- **AES-256-GCM is consistently faster** than Fernet for raw encrypt/decrypt operations
- **The performance gap grows with payload size** — at 100KB, AES-256-GCM can be an order of magnitude faster for encryption
- **At small payloads (empty, 1KB)**, both backends are fast enough that the difference is negligible in practice
- **Fernet implements Encrypt-then-MAC** (AES-128-CBC + HMAC-SHA256) with base64url output encoding. The two cryptographic operations are inherently sequential — CBC block chaining prevents parallelism, and HMAC must process the full ciphertext linearly. Both scale linearly with payload size
- **AES-256-GCM combines encryption and authentication in a single pass** (AEAD), with hardware acceleration where available (x86 AES-NI + CLMUL, ARMv8 crypto extensions). Counter mode is parallelizable across CPU pipelines, which is why the performance gap widens dramatically at larger payloads

## How to Run

Benchmark tests are excluded from the default test run. To run them explicitly:

```bash
# Run all benchmarks with verbose output and logging
uv run pytest tests/benchmarks/ -m benchmark -v --log-cli-level=INFO

# Run only the per-operation tests (informational, no assertions)
uv run pytest tests/benchmarks/ -m benchmark -v -k "encrypt_only or decrypt_only or comparison"

# Run only the round-trip overhead tests (assertive, < 1.20x threshold)
uv run pytest tests/benchmarks/ -m benchmark -v -k "round_trip"

# Run in CI mode (warnings instead of failures for overhead threshold)
CI=true uv run pytest tests/benchmarks/ -m benchmark -v
```

### Reading the Output

Benchmark results are logged at `INFO` level. Look for lines like:

```
Benchmark [aesgcm/10KB]: baseline=0.0234s, encrypted=0.0237s, overhead=1.03x
Encrypt-only [aesgcm/100KB]: median=0.000046s
Comparison [encrypt/100KB]: fernet=0.000684s, aesgcm=0.000024s, fernet/aesgcm=27.98x
```

- **Benchmark lines**: Show round-trip overhead (encrypted service vs. no-op baseline)
- **Encrypt/Decrypt-only lines**: Show raw backend operation cost
- **Comparison lines**: Show Fernet-to-AES-GCM ratio for each operation and size

## Interpreting Results

### Choosing a Backend

| Priority | Recommendation |
|----------|---------------|
| **Maximum security** | AES-256-GCM — authenticated encryption with associated data (AEAD), hardware-accelerated |
| **Maximum compatibility** | Fernet — well-known, simple key management, adequate for sessions under 10KB |
| **Large payloads (>10KB)** | AES-256-GCM — significantly faster at larger sizes |
| **Small payloads (<1KB)** | Either — both are fast enough that the difference is negligible |

### What the Overhead Ratio Means

The round-trip overhead test compares:

- **Baseline**: `EncryptedSessionService` with a no-op (passthrough) backend — same ORM, schema, and service stack, but no cryptographic work
- **Encrypted**: `EncryptedSessionService` with a real backend (Fernet or AES-256-GCM)

Because both paths use the same service stack, the ratio isolates pure encryption cost. ORM overhead, schema complexity, and connection handling cancel out.

### Round-Trip vs. Per-Operation

- **Round-trip tests** compare encrypted service vs. no-op service on the same stack, isolating encryption cost:
    - **AES-256-GCM**: Assertive — hard failure locally if overhead exceeds 1.20x. This backend reliably meets NFR1 across all payload sizes (typical overhead: 1.00-1.05x)
    - **Fernet**: Informational — warns but does not fail. Fernet's Encrypt-then-MAC architecture (AES-128-CBC + HMAC-SHA256) produces overhead that is borderline at the 1.20x threshold for small payloads and exceeds it at 100KB (~1.25x). AES-256-GCM is recommended for NFR1 compliance
- **Per-operation tests** (encrypt-only, decrypt-only) measure raw backend performance in isolation. These are informational — useful for backend comparison but not subject to NFR thresholds.

## Related

- [Algorithm documentation](./algorithms.md)
- [Getting started](./getting-started.md)
- [Roadmap](./ROADMAP.md)
- [FAQ](./faq.md)
