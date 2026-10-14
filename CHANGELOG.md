# Changelog

## Draft-release automation — 2026-10-15 (unreleased)

- Added version-tag and manual triggers for the approved public-repository draft-preparation workflow.
- Reused all required CI, Plugin Check, secret scanning, runtime packaging and checksum/autoload validation.
- Limited release write permission to the final draft job using the official GitHub CLI; drafts receive the installation ZIP, checksum and professional notes.
- Added safe retry guards for existing drafts, published releases, conflicting assets, edited notes, moved tags and ambiguous API failures. Published assets are never overwritten.
- Preserved version 1.0.0, all runtime PHP, API contracts and development/acceptance evidence. No tag, commit, push or release was created during local preparation.

## Distribution preparation — 2026-10-15 (unreleased)

- Reused the packager with an explicit 27-file runtime allowlist, ignored `dist/` output, SHA-256 sidecar, per-file manifest and Composer-free autoload verification.
- Added packaging regression tests and a manual, existing-tag release verification workflow with private-repository artifact uploads only; no release publication path.
- Reused CI for PHP syntax, PHPUnit, WooCommerce integration, PHPCS, PHPStan, installed-ZIP smoke checks and runtime-enabled Plugin Check.
- Added installation/download guidance and release distribution documentation; repository API guides, examples and images are retained.
- Corrected one space in the main plugin header comment; version and payment behavior remain unchanged.

## 1.0.0 — development build, 2026-10-10

- Introduced QuixDevs authenticated existing-order preparation and status routes.
- Delegated payment collection, confirmation and settlement to native WooCommerce Stripe checkout.
- Added explicit customer/server authorization, idempotency, persistent locks, safe diagnostics and provider verification.
- Added real WooCommerce datastore and REST integration tests, development tooling and package validation.

No public release has been published. See docs/publication-readiness.md.
