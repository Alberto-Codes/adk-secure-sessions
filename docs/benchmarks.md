# Benchmarks

## Why Benchmarks

adk-secure-sessions adds field-level encryption to every ADK session operation. NFR1 requires that this encryption overhead stays below 20% of total operation time — fast enough that developers don't have to choose between security and performance.

This page documents the performance characteristics of each encryption backend so you can make an informed choice based on real data, not assumptions.

## Methodology

All benchmarks use the same measurement approach:

- **Timer**: `time.perf_counter()` for high-resolution wall-clock timing
- **Iterations**: 20 per measurement, with the median used for comparison (resistant to outliers from OS scheduling or GC pauses)
- **Warm-up**: One throwaway iteration before measurement to eliminate cold-start effects
- **Payloads**: Four representative sizes — empty dict (`{}`), ~1KB, ~10KB, ~100KB — covering the range from minimal sessions to 10x realistic payloads
- **Environment modes**:
    - **Local**: Hard assertion failure if round-trip overhead exceeds 1.20x (developer feedback)
    - **CI** (`CI=true`): Emits a warning but passes (shared runner hardware varies too much for hard assertions)

### Why not pytest-benchmark?

The `pytest-benchmark` plugin expects synchronous callables. Since all adk-secure-sessions APIs are `async def`, using it would require `asyncio.run()` wrappers that add measurement artifacts and misrepresent actual async performance. We use direct `time.perf_counter()` instrumentation instead.

## Backend Comparison

Results below are **relative ratios**, not absolute times. Ratios are hardware-independent — they reflect algorithmic differences between backends, not your machine's clock speed. Run the benchmarks on your own hardware for absolute values.

### Encryption Speed (Fernet / AES-256-GCM ratio)

| Payload Size | Encrypt | Decrypt |
|-------------|---------|---------|
| Empty       | ~1.5x   | ~1.4x   |
| 1 KB        | ~1.5x   | ~1.0x   |
| 10 KB       | ~1.1x   | ~2.5x   |
| 100 KB      | ~10-25x | ~9x     |

!!! note "Ratios are approximate"
    These ratios were measured on a single development machine and will vary
    by hardware. The trend is consistent: AES-256-GCM is faster than Fernet,
    and the gap widens significantly at larger payload sizes.

### Key Observations

- **AES-256-GCM is consistently faster** than Fernet for raw encrypt/decrypt operations
- **The performance gap grows with payload size** — at 100KB, AES-256-GCM can be 10-25x faster for encryption
- **At small payloads (empty, 1KB)**, both backends are fast enough that the difference is negligible in practice
- **Fernet's overhead** comes from HMAC-SHA256 computation and base64 encoding, which scales linearly with payload size
- **AES-256-GCM** uses hardware-accelerated AES-NI instructions on modern CPUs, giving it a significant advantage at larger payloads

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
Benchmark [fernet/10KB]: baseline=0.0003s, encrypted=0.0024s, overhead=7.51x
Encrypt-only [aesgcm/100KB]: median=0.000058s
Comparison [encrypt/100KB]: fernet=0.000633s, aesgcm=0.000025s, fernet/aesgcm=25.53x
```

- **Benchmark lines**: Show round-trip overhead (encrypted service vs. raw SQL baseline)
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

- **Baseline**: Raw aiosqlite INSERT + SELECT + DELETE with JSON serialization (no encryption)
- **Encrypted**: Full `EncryptedSessionService` create + get + delete (SQLAlchemy + encryption)

The ratio includes the entire service layer overhead, not just encryption. This is intentional — it measures the real-world cost of using `EncryptedSessionService` compared to raw database access.

### Round-Trip vs. Per-Operation

- **Round-trip tests** measure end-to-end overhead including database, ORM, and encryption. These have the 1.20x assertion threshold (NFR1).
- **Per-operation tests** (encrypt-only, decrypt-only) measure raw backend performance in isolation. These are informational — useful for backend comparison but not subject to NFR thresholds.
