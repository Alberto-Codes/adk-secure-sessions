# Changelog

## [0.1.2](https://github.com/Alberto-Codes/adk-secure-sessions/compare/v0.1.1...v0.1.2) (2026-03-01)


### Features

* add .gitignore file to exclude unnecessary files and directories ([8290133](https://github.com/Alberto-Codes/adk-secure-sessions/commit/82901338bcd75e99bd4953404bdd7763be30d69a))
* add .python-version file for Python version management ([9096552](https://github.com/Alberto-Codes/adk-secure-sessions/commit/9096552efe00361127e6299b2ccce01800cc217d))
* add ADR-000 for Strategy + Decorator Architecture documentation ([f37c797](https://github.com/Alberto-Codes/adk-secure-sessions/commit/f37c797ea5114e4f9e418b50da26a6d8f4abcd89))
* add ADR-001 for Protocol-Based Interfaces documentation ([2a917c8](https://github.com/Alberto-Codes/adk-secure-sessions/commit/2a917c848caa45e29ef21eb89e9731e70e39768b))
* add ADR-002 for Async-First Design documentation ([2d5d131](https://github.com/Alberto-Codes/adk-secure-sessions/commit/2d5d1317e2354f65faea7bfa730f9a3098299795))
* add ADR-003 for Field-Level Encryption by Default documentation ([a5b7ee1](https://github.com/Alberto-Codes/adk-secure-sessions/commit/a5b7ee180a8c11ae57b5e040b23b9d858f995152))
* add ADR-004 for ADK Schema Compatibility Strategy documentation ([ebb48dc](https://github.com/Alberto-Codes/adk-secure-sessions/commit/ebb48dcf6db41de1e712156d6abafacd998fb60d))
* add ADR-005 for Exception Hierarchy and error handling guidelines ([a5d0261](https://github.com/Alberto-Codes/adk-secure-sessions/commit/a5d02617855f30e743650a3d69e651ea8ff2635c))
* add bug report issue template for reporting bugs and unexpected behavior ([5a031e3](https://github.com/Alberto-Codes/adk-secure-sessions/commit/5a031e38c7549657427712a7db325680ae0dea43))
* add CONTRIBUTING.md with guidelines for project contributions ([651d998](https://github.com/Alberto-Codes/adk-secure-sessions/commit/651d9988a681384b11b24c34f7088626e0011506))
* add detailed README.md for project overview and usage instructions ([d2c098b](https://github.com/Alberto-Codes/adk-secure-sessions/commit/d2c098b0216a4d0158ec0c6ee4963db79aa24ec5))
* add docstring templates for Google-style documentation guidance ([53f5652](https://github.com/Alberto-Codes/adk-secure-sessions/commit/53f565262266f8e9d60fa7809c5ffd0878a36b8a))
* add feature request issue template for suggesting new features ([cc4b309](https://github.com/Alberto-Codes/adk-secure-sessions/commit/cc4b309ee2c7d421e4b9a48a952cc91c19fae9c6))
* add google-adk dependency for enhanced functionality ([6617d69](https://github.com/Alberto-Codes/adk-secure-sessions/commit/6617d6910db2e5f09c96cf6b950438f54475c1ed))
* add initial roadmap outlining project phases and features ([19618c0](https://github.com/Alberto-Codes/adk-secure-sessions/commit/19618c06bb9f1f2a35f9ce4d7b5fd378d0fd03a7))
* add pull request template for consistent contributions ([0edf361](https://github.com/Alberto-Codes/adk-secure-sessions/commit/0edf361e27d253686ef8240200e179aae8c09223))
* add pyproject.toml for project configuration and dependencies ([982b848](https://github.com/Alberto-Codes/adk-secure-sessions/commit/982b848ef88c989b5d27191fcee37d0c7c17b89e))
* add README.md for Architecture Decision Records documentation ([327e7b6](https://github.com/Alberto-Codes/adk-secure-sessions/commit/327e7b6a394923273628399a5b40927145628dbc))
* add README.md for project documentation ([62ee634](https://github.com/Alberto-Codes/adk-secure-sessions/commit/62ee634a23530b4cc94eccd31ce80282f638b478))
* add tech debt issue template for reporting maintenance tasks ([09c7ec8](https://github.com/Alberto-Codes/adk-secure-sessions/commit/09c7ec8833325cacd90116251c91e1953c3a008f))
* **ci:** add google-adk version matrix to test workflow ([#24](https://github.com/Alberto-Codes/adk-secure-sessions/issues/24)) ([40fb932](https://github.com/Alberto-Codes/adk-secure-sessions/commit/40fb932c1cd3f6564e4587a688d23b78528ba835)), closes [#8](https://github.com/Alberto-Codes/adk-secure-sessions/issues/8)
* **ci:** add PyPI publish pipeline with trusted publishing ([98c3d5b](https://github.com/Alberto-Codes/adk-secure-sessions/commit/98c3d5bcb02ada0323c73e11aae3dcd4ffc3e283))
* **exceptions:** add ConfigurationError and startup validation ([#45](https://github.com/Alberto-Codes/adk-secure-sessions/issues/45)) ([4156996](https://github.com/Alberto-Codes/adk-secure-sessions/commit/4156996ee93d5705841d4d56aff155a91a4a63dc))
* **exceptions:** implement exception hierarchy ([#4](https://github.com/Alberto-Codes/adk-secure-sessions/issues/4)) ([#18](https://github.com/Alberto-Codes/adk-secure-sessions/issues/18)) ([865745e](https://github.com/Alberto-Codes/adk-secure-sessions/commit/865745eaa457ed05afefd5895816e3386d2e74cb))
* implement FernetBackend encryption backend ([#3](https://github.com/Alberto-Codes/adk-secure-sessions/issues/3)) ([#14](https://github.com/Alberto-Codes/adk-secure-sessions/issues/14)) ([d4fc86e](https://github.com/Alberto-Codes/adk-secure-sessions/commit/d4fc86eb6d677ae095de642bbba017615ec73657))
* **packaging:** add py.typed marker, fix keywords, tighten type signatures ([2f709ee](https://github.com/Alberto-Codes/adk-secure-sessions/commit/2f709ee714797d8962515964e165ef8ee5876073))
* **protocol:** add EncryptionBackend protocol with dev tooling and docs infrastructure ([#12](https://github.com/Alberto-Codes/adk-secure-sessions/issues/12)) ([e9314df](https://github.com/Alberto-Codes/adk-secure-sessions/commit/e9314df46372ee8193f82d65f94941f8c420820a)), closes [#2](https://github.com/Alberto-Codes/adk-secure-sessions/issues/2)
* **schema:** reserve version column for optimistic concurrency ([#43](https://github.com/Alberto-Codes/adk-secure-sessions/issues/43)) ([83f44b5](https://github.com/Alberto-Codes/adk-secure-sessions/commit/83f44b5e22733cf2cb80142a45d81d4b79d067c0)), closes [#42](https://github.com/Alberto-Codes/adk-secure-sessions/issues/42)
* **serialization:** add serialization layer with self-describing envelope format ([#19](https://github.com/Alberto-Codes/adk-secure-sessions/issues/19)) ([09d73a8](https://github.com/Alberto-Codes/adk-secure-sessions/commit/09d73a8f7a1813ab190a0ac768bf629053025e89)), closes [#5](https://github.com/Alberto-Codes/adk-secure-sessions/issues/5)
* **session:** add EncryptedSessionService with field-level encryption ([#21](https://github.com/Alberto-Codes/adk-secure-sessions/issues/21)) ([c602ef2](https://github.com/Alberto-Codes/adk-secure-sessions/commit/c602ef28409179ec7b923e721b86c66fbd5afb13)), closes [#6](https://github.com/Alberto-Codes/adk-secure-sessions/issues/6)
* **session:** ensure database changes are committed after upserting session state ([272a62e](https://github.com/Alberto-Codes/adk-secure-sessions/commit/272a62e368dd7254eb113fbc3b2bd0320219e274))
* simplify exception hierarchy in ADR-005 for clarity and maintainability ([ebd1118](https://github.com/Alberto-Codes/adk-secure-sessions/commit/ebd11183cc8f0e2ef72f4913260ad7cae2f33376))
* **templates:** add new templates for agent files, checklists, plans, specs, and tasks ([d72b61c](https://github.com/Alberto-Codes/adk-secure-sessions/commit/d72b61c57d4d9945a162832322ad61fcda209f30))
* **test:** add test infrastructure foundation and BMAD workflow enhancements ([7f64668](https://github.com/Alberto-Codes/adk-secure-sessions/commit/7f64668925c20980b0673b67d6ee7c2fc6e1064a))
* update constitution with core principles, security constraints, and development workflow ([354f1b8](https://github.com/Alberto-Codes/adk-secure-sessions/commit/354f1b8be39f844b57fa56a8875ee0eb5378ed03))


### Bug Fixes

* correct titles in ADR index for clarity ([3194044](https://github.com/Alberto-Codes/adk-secure-sessions/commit/31940445fec4d4aa2787eca0a945b1f79a5f1f43))
* update architecture description from Decorator to Direct Implementation for clarity ([75cc3f3](https://github.com/Alberto-Codes/adk-secure-sessions/commit/75cc3f3ec93f4357c38d2923438c539709fab1ef))
* update README for clarity on encryption features and backend options ([25c5d44](https://github.com/Alberto-Codes/adk-secure-sessions/commit/25c5d4452cef13b696cdd5dffbf88b2ed476433a))
* update title and context in ADR-004 for clarity and accuracy ([b141c99](https://github.com/Alberto-Codes/adk-secure-sessions/commit/b141c995dcf1bfae54056630334bef15f371117c))


### Performance Improvements

* **test:** skip PBKDF2 derivation in test fixtures ([#47](https://github.com/Alberto-Codes/adk-secure-sessions/issues/47)) ([a7e3a34](https://github.com/Alberto-Codes/adk-secure-sessions/commit/a7e3a342232e4e94d234abd3e096204a926267cf)), closes [#46](https://github.com/Alberto-Codes/adk-secure-sessions/issues/46)


### Documentation

* **context:** add AI agent project context with implementation rules ([15af996](https://github.com/Alberto-Codes/adk-secure-sessions/commit/15af99673875839f329ba4425daf5718f5eca9e9))
* **context:** update project-context.md branch references to main ([7884bef](https://github.com/Alberto-Codes/adk-secure-sessions/commit/7884bef3aa1959c0426ea46fa7ce26bac5dfefac))
* **planning:** add architecture, re-validate PRD, and sync roadmap phases ([c286605](https://github.com/Alberto-Codes/adk-secure-sessions/commit/c28660514be464640f2fc8c6d927d00f25a4eeb1))
* **planning:** add epic breakdown and user stories ([79c3e4a](https://github.com/Alberto-Codes/adk-secure-sessions/commit/79c3e4a81321a51dc5dfd8dc611756309ba9e9b3))
* **planning:** add implementation readiness assessment report ([822ea72](https://github.com/Alberto-Codes/adk-secure-sessions/commit/822ea7270d334c6167b1b4a4e8c740bca29ef7eb))
* **planning:** add sprint status tracking file ([a3041c4](https://github.com/Alberto-Codes/adk-secure-sessions/commit/a3041c4b99105bdaff8b97b9f16c6b51c754084e))
* **prd:** add product requirements document for adk-secure-sessions ([2b5daab](https://github.com/Alberto-Codes/adk-secure-sessions/commit/2b5daab17c1a2dffc5fc5e89cf9e1787ad8d65cf))
* **prd:** fix validation warnings in measurability, traceability, and domain compliance ([092a95b](https://github.com/Alberto-Codes/adk-secure-sessions/commit/092a95b9c31685fc64c6f297ba3734c7c830c368))
* **project:** add BMAD exhaustive scan documentation ([129e8c3](https://github.com/Alberto-Codes/adk-secure-sessions/commit/129e8c30241ab3c91816a895e439a93f7f16d30c))
* **readme:** rewrite with compliance gateway positioning ([b2b6713](https://github.com/Alberto-Codes/adk-secure-sessions/commit/b2b671304596af99c02b5796f13c0a1fda0d1f50)), closes [#65](https://github.com/Alberto-Codes/adk-secure-sessions/issues/65)
* **security:** add SECURITY.md and Apache-2.0 LICENSE ([e7ab509](https://github.com/Alberto-Codes/adk-secure-sessions/commit/e7ab5098ab85e251ac494a4311ef74b88e59e725)), closes [#63](https://github.com/Alberto-Codes/adk-secure-sessions/issues/63)

## [0.1.1](https://github.com/Alberto-Codes/adk-secure-sessions/compare/v0.1.0...v0.1.1) (2026-02-04)


### Features

* add .gitignore file to exclude unnecessary files and directories ([8290133](https://github.com/Alberto-Codes/adk-secure-sessions/commit/82901338bcd75e99bd4953404bdd7763be30d69a))
* add .python-version file for Python version management ([9096552](https://github.com/Alberto-Codes/adk-secure-sessions/commit/9096552efe00361127e6299b2ccce01800cc217d))
* add ADR-000 for Strategy + Decorator Architecture documentation ([f37c797](https://github.com/Alberto-Codes/adk-secure-sessions/commit/f37c797ea5114e4f9e418b50da26a6d8f4abcd89))
* add ADR-001 for Protocol-Based Interfaces documentation ([2a917c8](https://github.com/Alberto-Codes/adk-secure-sessions/commit/2a917c848caa45e29ef21eb89e9731e70e39768b))
* add ADR-002 for Async-First Design documentation ([2d5d131](https://github.com/Alberto-Codes/adk-secure-sessions/commit/2d5d1317e2354f65faea7bfa730f9a3098299795))
* add ADR-003 for Field-Level Encryption by Default documentation ([a5b7ee1](https://github.com/Alberto-Codes/adk-secure-sessions/commit/a5b7ee180a8c11ae57b5e040b23b9d858f995152))
* add ADR-004 for ADK Schema Compatibility Strategy documentation ([ebb48dc](https://github.com/Alberto-Codes/adk-secure-sessions/commit/ebb48dcf6db41de1e712156d6abafacd998fb60d))
* add ADR-005 for Exception Hierarchy and error handling guidelines ([a5d0261](https://github.com/Alberto-Codes/adk-secure-sessions/commit/a5d02617855f30e743650a3d69e651ea8ff2635c))
* add bug report issue template for reporting bugs and unexpected behavior ([5a031e3](https://github.com/Alberto-Codes/adk-secure-sessions/commit/5a031e38c7549657427712a7db325680ae0dea43))
* add CONTRIBUTING.md with guidelines for project contributions ([651d998](https://github.com/Alberto-Codes/adk-secure-sessions/commit/651d9988a681384b11b24c34f7088626e0011506))
* add detailed README.md for project overview and usage instructions ([d2c098b](https://github.com/Alberto-Codes/adk-secure-sessions/commit/d2c098b0216a4d0158ec0c6ee4963db79aa24ec5))
* add docstring templates for Google-style documentation guidance ([53f5652](https://github.com/Alberto-Codes/adk-secure-sessions/commit/53f565262266f8e9d60fa7809c5ffd0878a36b8a))
* add feature request issue template for suggesting new features ([cc4b309](https://github.com/Alberto-Codes/adk-secure-sessions/commit/cc4b309ee2c7d421e4b9a48a952cc91c19fae9c6))
* add google-adk dependency for enhanced functionality ([6617d69](https://github.com/Alberto-Codes/adk-secure-sessions/commit/6617d6910db2e5f09c96cf6b950438f54475c1ed))
* add initial roadmap outlining project phases and features ([19618c0](https://github.com/Alberto-Codes/adk-secure-sessions/commit/19618c06bb9f1f2a35f9ce4d7b5fd378d0fd03a7))
* add pull request template for consistent contributions ([0edf361](https://github.com/Alberto-Codes/adk-secure-sessions/commit/0edf361e27d253686ef8240200e179aae8c09223))
* add pyproject.toml for project configuration and dependencies ([982b848](https://github.com/Alberto-Codes/adk-secure-sessions/commit/982b848ef88c989b5d27191fcee37d0c7c17b89e))
* add README.md for Architecture Decision Records documentation ([327e7b6](https://github.com/Alberto-Codes/adk-secure-sessions/commit/327e7b6a394923273628399a5b40927145628dbc))
* add README.md for project documentation ([62ee634](https://github.com/Alberto-Codes/adk-secure-sessions/commit/62ee634a23530b4cc94eccd31ce80282f638b478))
* add tech debt issue template for reporting maintenance tasks ([09c7ec8](https://github.com/Alberto-Codes/adk-secure-sessions/commit/09c7ec8833325cacd90116251c91e1953c3a008f))
* **ci:** add google-adk version matrix to test workflow ([#24](https://github.com/Alberto-Codes/adk-secure-sessions/issues/24)) ([40fb932](https://github.com/Alberto-Codes/adk-secure-sessions/commit/40fb932c1cd3f6564e4587a688d23b78528ba835)), closes [#8](https://github.com/Alberto-Codes/adk-secure-sessions/issues/8)
* **exceptions:** implement exception hierarchy ([#4](https://github.com/Alberto-Codes/adk-secure-sessions/issues/4)) ([#18](https://github.com/Alberto-Codes/adk-secure-sessions/issues/18)) ([865745e](https://github.com/Alberto-Codes/adk-secure-sessions/commit/865745eaa457ed05afefd5895816e3386d2e74cb))
* implement FernetBackend encryption backend ([#3](https://github.com/Alberto-Codes/adk-secure-sessions/issues/3)) ([#14](https://github.com/Alberto-Codes/adk-secure-sessions/issues/14)) ([d4fc86e](https://github.com/Alberto-Codes/adk-secure-sessions/commit/d4fc86eb6d677ae095de642bbba017615ec73657))
* **protocol:** add EncryptionBackend protocol with dev tooling and docs infrastructure ([#12](https://github.com/Alberto-Codes/adk-secure-sessions/issues/12)) ([e9314df](https://github.com/Alberto-Codes/adk-secure-sessions/commit/e9314df46372ee8193f82d65f94941f8c420820a)), closes [#2](https://github.com/Alberto-Codes/adk-secure-sessions/issues/2)
* **serialization:** add serialization layer with self-describing envelope format ([#19](https://github.com/Alberto-Codes/adk-secure-sessions/issues/19)) ([09d73a8](https://github.com/Alberto-Codes/adk-secure-sessions/commit/09d73a8f7a1813ab190a0ac768bf629053025e89)), closes [#5](https://github.com/Alberto-Codes/adk-secure-sessions/issues/5)
* **session:** add EncryptedSessionService with field-level encryption ([#21](https://github.com/Alberto-Codes/adk-secure-sessions/issues/21)) ([c602ef2](https://github.com/Alberto-Codes/adk-secure-sessions/commit/c602ef28409179ec7b923e721b86c66fbd5afb13)), closes [#6](https://github.com/Alberto-Codes/adk-secure-sessions/issues/6)
* **session:** ensure database changes are committed after upserting session state ([272a62e](https://github.com/Alberto-Codes/adk-secure-sessions/commit/272a62e368dd7254eb113fbc3b2bd0320219e274))
* simplify exception hierarchy in ADR-005 for clarity and maintainability ([ebd1118](https://github.com/Alberto-Codes/adk-secure-sessions/commit/ebd11183cc8f0e2ef72f4913260ad7cae2f33376))
* **templates:** add new templates for agent files, checklists, plans, specs, and tasks ([d72b61c](https://github.com/Alberto-Codes/adk-secure-sessions/commit/d72b61c57d4d9945a162832322ad61fcda209f30))
* update constitution with core principles, security constraints, and development workflow ([354f1b8](https://github.com/Alberto-Codes/adk-secure-sessions/commit/354f1b8be39f844b57fa56a8875ee0eb5378ed03))


### Bug Fixes

* correct titles in ADR index for clarity ([3194044](https://github.com/Alberto-Codes/adk-secure-sessions/commit/31940445fec4d4aa2787eca0a945b1f79a5f1f43))
* update architecture description from Decorator to Direct Implementation for clarity ([75cc3f3](https://github.com/Alberto-Codes/adk-secure-sessions/commit/75cc3f3ec93f4357c38d2923438c539709fab1ef))
* update README for clarity on encryption features and backend options ([25c5d44](https://github.com/Alberto-Codes/adk-secure-sessions/commit/25c5d4452cef13b696cdd5dffbf88b2ed476433a))
* update title and context in ADR-004 for clarity and accuracy ([b141c99](https://github.com/Alberto-Codes/adk-secure-sessions/commit/b141c995dcf1bfae54056630334bef15f371117c))

## Changelog
