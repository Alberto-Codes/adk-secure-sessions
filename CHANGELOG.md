# Changelog

## [1.2.0](https://github.com/Alberto-Codes/adk-secure-sessions/compare/v1.1.0...v1.2.0) (2026-03-07)


### Features

* **backend:** add AES-256-GCM encryption backend ([#141](https://github.com/Alberto-Codes/adk-secure-sessions/issues/141)) ([9ea7881](https://github.com/Alberto-Codes/adk-secure-sessions/commit/9ea7881690b811b0d5e6512b810ac225bb2c05f1))
* **backend:** add per-key random salt key derivation to FernetBackend ([64f2a76](https://github.com/Alberto-Codes/adk-secure-sessions/commit/64f2a768ed0ee321d5b92a95de8846a318f57353))
* **backend:** add per-key random salt key derivation to FernetBackend ([#143](https://github.com/Alberto-Codes/adk-secure-sessions/issues/143)) ([64f2a76](https://github.com/Alberto-Codes/adk-secure-sessions/commit/64f2a768ed0ee321d5b92a95de8846a318f57353))
* **serialization:** add multi-backend coexistence and dispatch ([#144](https://github.com/Alberto-Codes/adk-secure-sessions/issues/144)) ([c971d33](https://github.com/Alberto-Codes/adk-secure-sessions/commit/c971d3392ea86cf5ef7886540d6f2afe7c88c1b3)), closes [#145](https://github.com/Alberto-Codes/adk-secure-sessions/issues/145)


### Bug Fixes

* **backend:** address code review findings for per-key random salt ([64f2a76](https://github.com/Alberto-Codes/adk-secure-sessions/commit/64f2a768ed0ee321d5b92a95de8846a318f57353))
* **backend:** tighten exception catch and add boundary tests ([64f2a76](https://github.com/Alberto-Codes/adk-secure-sessions/commit/64f2a768ed0ee321d5b92a95de8846a318f57353))

## [1.1.0](https://github.com/Alberto-Codes/adk-secure-sessions/compare/v1.0.3...v1.1.0) (2026-03-06)


### Features

* create EncryptedJSON TypeDecorator for transparent column ([dc70d5c](https://github.com/Alberto-Codes/adk-secure-sessions/commit/dc70d5c1b44ca8d444e761c4e787f70c8b30262a))
* **examples:** add encrypted ADK agent example with Ollama ([f898849](https://github.com/Alberto-Codes/adk-secure-sessions/commit/f8988490181c97d9018d7b0d0f269d7b61a8ccfb))
* **examples:** add encrypted ADK agent example with Ollama ([#139](https://github.com/Alberto-Codes/adk-secure-sessions/issues/139)) ([f898849](https://github.com/Alberto-Codes/adk-secure-sessions/commit/f8988490181c97d9018d7b0d0f269d7b61a8ccfb))
* **session:** rewrite EncryptedSessionService as DatabaseSessionService wrapper ([#134](https://github.com/Alberto-Codes/adk-secure-sessions/issues/134)) ([dc70d5c](https://github.com/Alberto-Codes/adk-secure-sessions/commit/dc70d5c1b44ca8d444e761c4e787f70c8b30262a)), closes [#133](https://github.com/Alberto-Codes/adk-secure-sessions/issues/133)
* **spike:** TypeDecorator wrapping spike — GO decision for Epic 7 ([#130](https://github.com/Alberto-Codes/adk-secure-sessions/issues/130)) ([b9919df](https://github.com/Alberto-Codes/adk-secure-sessions/commit/b9919df8cd8ae4c00f0535ef2dd371900fc56db2)), closes [#129](https://github.com/Alberto-Codes/adk-secure-sessions/issues/129)


### Documentation

* **adr:** add ADR-007 Architecture Migration decision ([#132](https://github.com/Alberto-Codes/adk-secure-sessions/issues/132)) ([d94f883](https://github.com/Alberto-Codes/adk-secure-sessions/commit/d94f88329c8768b8e2d151247483557586331a83)), closes [#131](https://github.com/Alberto-Codes/adk-secure-sessions/issues/131)
* **examples:** reference basic usage example in README and ([f898849](https://github.com/Alberto-Codes/adk-secure-sessions/commit/f8988490181c97d9018d7b0d0f269d7b61a8ccfb))
* **getting-started:** clarify swap is two changes, not three imports ([#127](https://github.com/Alberto-Codes/adk-secure-sessions/issues/127)) ([9296ae3](https://github.com/Alberto-Codes/adk-secure-sessions/commit/9296ae3f97cfa54758470a9f0208fb1c3ce24365))
* **session:** Epic 7 retrospective and sprint status update ([f898849](https://github.com/Alberto-Codes/adk-secure-sessions/commit/f8988490181c97d9018d7b0d0f269d7b61a8ccfb))
* **session:** revise Epic 4 scope and extract shared test fixture ([#138](https://github.com/Alberto-Codes/adk-secure-sessions/issues/138)) ([252ad4e](https://github.com/Alberto-Codes/adk-secure-sessions/commit/252ad4e74655f148727fa26898111c83614c2401))
* **session:** update docs for Epic 7 architecture migration ([#137](https://github.com/Alberto-Codes/adk-secure-sessions/issues/137)) ([c810c56](https://github.com/Alberto-Codes/adk-secure-sessions/commit/c810c56d7d925355772d298d8d1b08d38046420b))

## [1.0.3](https://github.com/Alberto-Codes/adk-secure-sessions/compare/v1.0.2...v1.0.3) (2026-03-05)


### Bug Fixes

* address code review findings for story 6.2 ([3ebeb6d](https://github.com/Alberto-Codes/adk-secure-sessions/commit/3ebeb6dd5866ab6424e3b7dbecdd92d7a37f9994))
* correct docstring template db_url to db_path ([3ebeb6d](https://github.com/Alberto-Codes/adk-secure-sessions/commit/3ebeb6dd5866ab6424e3b7dbecdd92d7a37f9994))
* correct schema independence claims and architecture ([3ebeb6d](https://github.com/Alberto-Codes/adk-secure-sessions/commit/3ebeb6dd5866ab6424e3b7dbecdd92d7a37f9994))
* **docs:** address code review findings for story 6.2 ([3ebeb6d](https://github.com/Alberto-Codes/adk-secure-sessions/commit/3ebeb6dd5866ab6424e3b7dbecdd92d7a37f9994))
* **docs:** correct docstring template db_url to db_path ([3ebeb6d](https://github.com/Alberto-Codes/adk-secure-sessions/commit/3ebeb6dd5866ab6424e3b7dbecdd92d7a37f9994))
* **docs:** correct schema independence claims and architecture characterization ([#123](https://github.com/Alberto-Codes/adk-secure-sessions/issues/123)) ([3ebeb6d](https://github.com/Alberto-Codes/adk-secure-sessions/commit/3ebeb6dd5866ab6424e3b7dbecdd92d7a37f9994)), closes [#121](https://github.com/Alberto-Codes/adk-secure-sessions/issues/121)
* **docs:** remove edit pencil icons from docs site ([8f44167](https://github.com/Alberto-Codes/adk-secure-sessions/commit/8f441672801d3bfa1bcc421de221133c556193f4))
* **docs:** replace inaccurate 'drop-in replacement' claims with BaseSessionService references ([f323d5e](https://github.com/Alberto-Codes/adk-secure-sessions/commit/f323d5e0ac8112a01fdc865d37169c32c410f84d))


### Documentation

* add superseded revision markers to planning artifacts and ADRs ([#125](https://github.com/Alberto-Codes/adk-secure-sessions/issues/125)) ([afbb53e](https://github.com/Alberto-Codes/adk-secure-sessions/commit/afbb53e228ea2e7c76b13a6256bf73d7b5f86fc5)), closes [#124](https://github.com/Alberto-Codes/adk-secure-sessions/issues/124)
* **branding:** add custom palette, logo, favicon, badges, and social links ([d71a38b](https://github.com/Alberto-Codes/adk-secure-sessions/commit/d71a38b568e53253d254928694391be62420ac91))

## [1.0.2](https://github.com/Alberto-Codes/adk-secure-sessions/compare/v1.0.1...v1.0.2) (2026-03-04)


### Bug Fixes

* **ci:** remove unsafe-best-match index strategy from smoke test ([592ebe1](https://github.com/Alberto-Codes/adk-secure-sessions/commit/592ebe1b427d860b81641658c77c735937e5be1b))
* **ci:** replace TestPyPI gate with local wheel smoke test ([#97](https://github.com/Alberto-Codes/adk-secure-sessions/issues/97)) ([cf932e8](https://github.com/Alberto-Codes/adk-secure-sessions/commit/cf932e8d1d71f8a4547030dbf7c7eeeebea68908))
* **docs:** apply code review fixes for Getting Started guide ([efb222e](https://github.com/Alberto-Codes/adk-secure-sessions/commit/efb222e5038a54f5a49507091364ff81cb61d7ab))
* **release:** guard fromJSON with short-circuit to prevent empty parse ([#90](https://github.com/Alberto-Codes/adk-secure-sessions/issues/90)) ([cd3eca5](https://github.com/Alberto-Codes/adk-secure-sessions/commit/cd3eca584094e57cf46aabe4dfa2788d88db28f3))


### Documentation

* **architecture:** add envelope protocol and algorithm specification pages ([#92](https://github.com/Alberto-Codes/adk-secure-sessions/issues/92)) ([f76555a](https://github.com/Alberto-Codes/adk-secure-sessions/commit/f76555a5afa8f7a5478603b5df121c254d369474)), closes [#91](https://github.com/Alberto-Codes/adk-secure-sessions/issues/91)
* **docstrings:** add Examples sections to 5 EncryptedSessionService ([44911c4](https://github.com/Alberto-Codes/adk-secure-sessions/commit/44911c4fecd7dfe99cf2bb64c8fbef7892e71af1))
* **docstrings:** add fenced examples to all public APIs and enforce docvet fail-on ([#85](https://github.com/Alberto-Codes/adk-secure-sessions/issues/85)) ([44911c4](https://github.com/Alberto-Codes/adk-secure-sessions/commit/44911c4fecd7dfe99cf2bb64c8fbef7892e71af1))
* **docstrings:** add missing See Also and Attributes sections ([44911c4](https://github.com/Alberto-Codes/adk-secure-sessions/commit/44911c4fecd7dfe99cf2bb64c8fbef7892e71af1))
* **faq:** add FAQ page with 6 required entries and nav integration ([#96](https://github.com/Alberto-Codes/adk-secure-sessions/issues/96)) ([f3e7ade](https://github.com/Alberto-Codes/adk-secure-sessions/commit/f3e7ade838d33f3e141b1b94acc6b185f5e93526)), closes [#95](https://github.com/Alberto-Codes/adk-secure-sessions/issues/95)
* **getting-started:** add Getting Started guide with full example and ([efb222e](https://github.com/Alberto-Codes/adk-secure-sessions/commit/efb222e5038a54f5a49507091364ff81cb61d7ab))
* **getting-started:** add Getting Started guide with full example and verification ([#101](https://github.com/Alberto-Codes/adk-secure-sessions/issues/101)) ([efb222e](https://github.com/Alberto-Codes/adk-secure-sessions/commit/efb222e5038a54f5a49507091364ff81cb61d7ab)), closes [#100](https://github.com/Alberto-Codes/adk-secure-sessions/issues/100)
* **mkdocs:** restructure nav, add strict builds, and complete site setup ([#88](https://github.com/Alberto-Codes/adk-secure-sessions/issues/88)) ([8544448](https://github.com/Alberto-Codes/adk-secure-sessions/commit/85444486d2c58c816dbdcd03a57b07fa650dd867)), closes [#86](https://github.com/Alberto-Codes/adk-secure-sessions/issues/86)
* **roadmap:** update completion status, add backend upgrade schedule ([#94](https://github.com/Alberto-Codes/adk-secure-sessions/issues/94)) ([1357afd](https://github.com/Alberto-Codes/adk-secure-sessions/commit/1357afd5698a1fab4c9d7f224c81962aeaa71ee1)), closes [#93](https://github.com/Alberto-Codes/adk-secure-sessions/issues/93)
* **templates:** prescribe fenced-blocks-everywhere in ([44911c4](https://github.com/Alberto-Codes/adk-secure-sessions/commit/44911c4fecd7dfe99cf2bb64c8fbef7892e71af1))

## [1.0.1](https://github.com/Alberto-Codes/adk-secure-sessions/compare/v1.0.0...v1.0.1) (2026-03-02)


### Bug Fixes

* **ci:** fix broken badges and add Codecov integration ([ab36b45](https://github.com/Alberto-Codes/adk-secure-sessions/commit/ab36b45b3ca8b0cd8a0f019b59bca227877b4db4))
* **ci:** upgrade classifier to Beta and add check-url to PyPI publish ([fc4f389](https://github.com/Alberto-Codes/adk-secure-sessions/commit/fc4f3897dcb7ffd2a669a634b31b325f290e8b3e))

## [1.0.0](https://github.com/Alberto-Codes/adk-secure-sessions/releases/tag/v1.0.0) (2026-03-01)

### Features

* **session:** EncryptedSessionService — drop-in replacement for ADK's BaseSessionService with field-level encryption at rest
* **encryption:** Fernet symmetric encryption backend (AES-128-CBC + HMAC-SHA256) with async-first design
* **serialization:** Self-describing binary envelope format with version and backend metadata for future key rotation
* **persistence:** Async SQLite persistence via aiosqlite with own schema, independent of ADK internals
* **validation:** ConfigurationError with startup-time passphrase and backend validation
* **security:** Coordinated disclosure policy (SECURITY.md), Apache-2.0 license, zero-CVE dependency audit
* **ci:** Automated PyPI releases via OIDC trusted publishing — no stored tokens, changelog generation via release-please
