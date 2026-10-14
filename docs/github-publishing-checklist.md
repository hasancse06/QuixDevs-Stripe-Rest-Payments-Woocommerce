# GitHub upload and release checklist

## Upload the prepared source

This repository folder is `quixdevs-stripe-rest-payments-github`. The verified remote is `hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce`; the plugin slug stays `quixdevs-stripe-rest-payments`.

1. Run `python3 tools/check-source.py` and `python3 tools/check-repository.py` from the repository root.
2. Review `git status --short --ignored` and the intended upload files with `git ls-files --others --exclude-standard`. Keep source, tests, Composer manifests/lockfile, `.github`, documentation, editable artwork and numbered screenshots.
3. The GitHub source repository already exists. Upload the **contents** of this folder at its root, or add its remote and push after reviewing a commit. Include `.gitignore`, `.gitattributes` and `.github` when using a file picker; hidden files may need to be shown.
4. Apply the description/topics in [the listing guide](github-listing.md). Set `docs/branding/github-social-preview.png` as the repository social preview. The README already embeds the banner and all four screenshots with relative paths.
5. Run the prepared GitHub Actions workflow and inspect its results. Local checks do not establish remote CI success.

The `.gitignore` excludes installed dependencies, caches, local credentials/settings, database dumps, logs, archives, build output and raw capture/verification files. It intentionally retains `composer.lock`, test sources, `*.dist` templates, SVG/PNG branding and screenshots. `.gitignore` does not remove already tracked files: review the tracked file list before every push. No remote or commit is created automatically by the preparation tools.

## Build an installable development package

Run `python3 tools/package.py`. It creates `dist/quixdevs-stripe-rest-payments.zip`, `dist/quixdevs-stripe-rest-payments.zip.sha256` and `dist/package-manifest.json`. Review the manifest and extracted contents. The ZIP has the correct plugin root, an internal autoloader and only allowlisted runtime files, readme and license. GitHub source archives are not the curated installation asset.

Before preparing a draft release, rerun unit/integration tests, PHPCS, PHPStan and extracted-package Plugin Check on the final runtime. Install and activate on disposable WordPress. Describe it as development-only. The approved [draft-release workflow](../.github/workflows/release.yml) supports `v*` tag pushes and manual dispatch in the public repository. Required checks precede unpublished draft creation; no automatic publication is permitted. Existing published releases, conflicting draft assets and edited notes are refused. Follow [release distribution](release-distribution.md) for the existing-tag procedure, retry policy and manual publication steps.

## Stable payment release gates

- Confirm source and branding rights and resolve the historical license evidence in [licensing](licensing.md).
- Complete authorized merchant Stripe test-mode success, decline, 3DS, timeout recovery, webhook delay, duplicate attempts and configured capture tests.
- Verify classic checkout, Blocks, Store API coexistence, browser owner login, device builds and return-to-app behavior.
- Exercise the supported HPOS/legacy and PHP/WP/Woo matrix, including relevant persistent caches.
- Verify the strict Stripe version guard against source/contract changes before changing it.
- Review deployment authentication, cache exclusions, redaction, rate limits and operator lock recovery.
- Confirm publisher accounts and final directory/release requirements. Review the [acceptance matrix](publication-readiness.md).

This folder is prepared for GitHub source upload. Production payment acceptance and a stable release remain separate gates. No remote push, public release or WordPress.org submission was performed during preparation.
