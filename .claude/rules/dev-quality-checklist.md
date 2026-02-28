# Dev Quality Checklist

Quality patterns learned during development. Apply these during implementation, not just review.

## AC-to-Test Traceability

Before marking a story or task done, verify every acceptance criterion has at least one test that directly verifies it. Write tests from the AC contract, not from the implementation.

## Assertion Strength

- Verify ALL relevant fields, not just the primary one (e.g., all session state keys after decryption, not just one)
- Use `assert_called_once_with(...)` not `assert_called_once()` — verify arguments, not just call count
- Add negative assertions where appropriate (e.g., decrypting with the correct key does NOT raise)
- Include `assert len(results) == N` to catch deduplication or serialization breakage

## Edge Case Coverage

- Proactively add boundary tests: empty bytes, empty dict state, single-character keys, max-size payloads
- Test mix scenarios: some valid + some invalid entries in same input
- Test skip conditions: inputs that should produce zero results or no-op behavior

## Task Tracking Accuracy

- Before marking a subtask `[x]` done, verify the code change actually exists
- Run the relevant test to confirm the change is real
- Do not mark implementation tasks done based on intent — only on verified code

## Encryption Path Verification

- Every new database read/write path MUST go through `encrypt_session`/`decrypt_session`
- An unencrypted data path is a security defect, not a TODO
- When adding new fields or state keys, verify they round-trip through the full encrypt/decrypt cycle
- Test that wrong-key decryption raises `DecryptionError`, not a generic exception

## Async Test Hygiene

- Test fixtures that create services with DB connections (e.g., `EncryptedSessionService`) MUST call `await svc.close()` in teardown
- Use async generator fixtures: `yield svc; await svc.close()`
- Verify no leaked database connections after test runs
- Wrap `cryptography` calls in `asyncio.to_thread()` — tests should catch missing wrappers by running under async
