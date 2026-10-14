# Lightweight distribution and release preparation

Prepared 2026-10-15 for **QuixDevs Stripe REST Payments 1.0.0**. This is packaging and release engineering work. The payment implementation, request/response contract, authentication, authorization, idempotency, Stripe adapter, order CRUD and HPOS behavior are unchanged. All runtime classes are byte-identical to the starting source. One extra space before `Author` in the main plugin header comment was removed to pass PHPCS; no version change occurred.

**Status remains development-only.** Merchant payment acceptance and publisher-rights/publication requirements in [publication readiness](publication-readiness.md) remain open. The workflow has read-only repository permissions and creates no tags or GitHub Releases.

## Files changed

- `tools/package.py`: reused packager, explicit allowlist, lightweight `dist/` output, checksum and detailed manifest.
- `tools/runtime-files.json`, `tools/verify-package.py`, `tools/prepare-release.py`: new runtime, autoload, archive and existing-tag guards.
- `tools/install-gitleaks.py`, `.gitleaks.toml`: pinned official secret scanner and narrow fixture exception.
- `tools/installation-smoke.php`, `tools/verify-plugin-check.py`, `tests/Packaging/test_package.py`: installed-package and packaging verification.
- `.github/workflows/release.yml`, `.github/workflows/ci.yml`: manual/private-only artifact process and reused automated checks.
- `tools/check-repository.py`, `tools/check-source.py`, `tools/provision-test-site.sh`: `dist/` checks and reproducible Plugin Check fixture version.
- `README.md`, `CHANGELOG.md`, `docs/github-publishing-checklist.md`, this guide: download/install and distribution instructions.
- `quixdevs-stripe-rest-payments.php`: one header-comment whitespace correction only.

The existing `.gitignore` already ignores `dist/`; no change was necessary. API guides, examples, Postman, screenshots, runtime classes, dependency lockfile and dated test/readiness evidence are retained.

## Build commands

Run from the `quixdevs-stripe-rest-payments-github` repository root:

```sh
python3 tools/check-source.py
python3 -m unittest discover -s tests/Packaging -v
python3 tools/package.py
python3 tools/verify-package.py
python3 tools/check-repository.py
```

Python 3.9+ and PHP 8.2+ suffice for local package building and verification. Composer is used for development checks only. Build output is ignored by Git:

```text
dist/
  quixdevs-stripe-rest-payments.zip
  quixdevs-stripe-rest-payments.zip.sha256
  package-manifest.json
```

`tools/package.py` is the existing packager, now using the explicit [runtime allowlist](../tools/runtime-files.json). It prints the filename, bytes, file count, SHA-256 and unchanged development-only status. ZIP entries have fixed timestamps/modes and order, so repeated builds with the same input bytes and compression implementation produce the same checksum. The manifest records each source-file hash, no bundled third-party runtime dependencies, and the required externally installed WooCommerce/Stripe versions.

`tools/verify-package.py` checks every entry against the source and allowlist, rejects extra/duplicate/wrong-root files, verifies CRC, sidecar and manifest, parses every PHP file, and loads all 22 runtime classes/interfaces/enums from the extracted ZIP without Composer. New production dependencies, missing/symlinked files, unreviewed runtime classes and version drift fail closed.

## Current artifact

| Property | Value |
| --- | --- |
| Filename | `quixdevs-stripe-rest-payments.zip` |
| Location | `dist/quixdevs-stripe-rest-payments.zip` |
| Status/version | Development-only / 1.0.0 |
| Size | **24,919 bytes** (24.33 KiB) |
| File count | **27**: 25 PHP runtime files, `readme.txt`, `LICENSE` |
| SHA-256 | `3d0acdb3dc749dccbff41bb91f0a48a805a81277749edc87ba85d5fbd3c57735` |
| Root | `quixdevs-stripe-rest-payments/` |
| Customer Composer requirement | None |

Verify the checksum from the output directory:

```sh
cd dist
sha256sum --check quixdevs-stripe-rest-payments.zip.sha256
```

On macOS use `shasum -a 256 -c quixdevs-stripe-rest-payments.zip.sha256`. Archive size/checksum describe this exact runtime snapshot; regenerate and record them after any approved runtime change. The dated October 10 implementation/testing/readiness reports and old ignored `build/` artifact remain historical evidence and are not rewritten as new test results.

## Source repository and installation ZIP

The GitHub source keeps the full project:

```text
.github/workflows/ci.yml, release.yml
includes/                       # payment runtime classes and autoloader
quixdevs-stripe-rest-payments.php # WordPress bootstrap and metadata
uninstall.php, readme.txt, LICENSE
README.md, CHANGELOG.md, SECURITY.md, CONTRIBUTING.md
composer.json, composer.lock    # locked development dependencies
phpunit.xml.dist, phpcs.xml.dist, phpstan.neon.dist
tests/                          # existing unit/REST/DB tests + packaging tests
tools/                          # build, verification and fixture tools
docs/                           # all API/auth/recovery/security/client guides
wordpress-org-assets/           # separate presentation handoff
```

The installation ZIP contains only:

```text
quixdevs-stripe-rest-payments/
  quixdevs-stripe-rest-payments.php
  uninstall.php
  readme.txt
  LICENSE
  includes/
    Autoload.php, Bootstrap.php, Dependencies.php, Plugin.php
    Admin/, Authentication/, Data/, Payments/, Rest/, Stripe/, Support/
```

There are no runtime JS/CSS assets, translation catalogs or Composer libraries required by this version. WordPress, WooCommerce and the official Stripe gateway supply their own dependencies and translations. `readme.txt` retains the installation, authentication, endpoint, external-service, security, compatibility and development-only disclosures.

Excluded from the ZIP: tests, `.github`, tools/configuration/Composer manifests and development packages, repository Markdown guides and examples, Postman, screenshots, branding, directory assets, logs, local configuration, archives, caches, credentials and original EventPro source. This exclusion does not delete any GitHub documentation. The `.gitignore` already excludes `dist/` and `build/`.

**Code → Download ZIP** is a full development-source archive. The lightweight installation ZIP is a separately generated asset. Its canonical filename has no version suffix so a future approved stable release can support the permanent latest-download URL.

## Verification performed for this distribution

Fresh isolated environment: PHP 8.4.13, WordPress 6.9, WooCommerce 10.9.0, official Stripe 11.0.1, MariaDB 10.4.28 with networking disabled and a dedicated private temporary socket. Plugin Check 2.1.0 was downloaded from the official directory. Dummy test credentials and the existing network-blocking mu-plugin prevent provider calls; selected integration reads use fixtures. No real payment was attempted.

| Check | Current observed result |
| --- | --- |
| Existing unit suite | 51 tests / 93 assertions passed |
| Existing real WP/WooCommerce REST/storage suite | 18 tests / 81 assertions passed, legacy and HPOS, four-worker lock contention |
| Packaging regressions | 15 tests passed: completeness, deterministic build, missing/symlinked/new files, source drift, root, dependency/version/tag guards, private-only workflow, and fail-closed Plugin Check result handling |
| Runtime PHP syntax | All 25 PHP files passed |
| PHPCS | Passed after correcting the pre-existing single-space header formatting issue |
| PHPStan | Level 5, no errors, serial analysis |
| ZIP/autoloader/checksum | 27-file allowlist, CRC, source/manifest bytes and SHA-256 passed; 22 runtime types loaded without Composer |
| WordPress installation | WP-CLI ZIP installation passed; authenticated native admin multipart ZIP upload, installation and nonce-protected activation also passed over loopback; no source symlink/vendor directory |
| Installed-package API/diagnostics | Two payment routes; anonymous denial; owner preparation; idempotent retry; unpaid status; native admin diagnostics passed |
| Missing WooCommerce / missing Stripe | Separate cold requests: no payment routes, actionable diagnostics, no fatal |
| WordPress Plugin Check | Absolute installed-package path with runtime bootstrap: 0 errors, 0 warnings |
| Secret scanning | Official checksum-pinned Gitleaks 8.30.1: maintained source and extracted runtime pass; heuristic source checks pass |
| Documentation | Relative links and all four visible README screenshots verified; existing API guides/examples retained |
| GitHub workflow syntax | Official checksum-verified actionlint used on CI/release workflows |

The Gitleaks configuration excludes installed dependencies/generated output and allows only the exact existing `dummy-idempotency-0001` request header fixture in `tests/Unit/PaymentTest.php` with both path and value matching. Idempotency fixture values are not authentication credentials. No general test-directory or scanner-rule suppression is added. Full Git history is not covered by the maintained-tree/runtime scan.

This task verified WP-CLI ZIP installation, real admin rendering and the native WordPress admin upload endpoint with an authenticated HTTP client over loopback. The fixture temporarily used a loopback URL for that upload and restored its HTTPS store URLs before the installed-package API smoke check. No interactive browser GUI upload or real Stripe test-mode payment occurred. PHP 8.2/8.3, MySQL 8 remote jobs and actual Actions artifact upload have not been executed locally. Remote workflow execution is prepared, not claimed as passed. Earlier test evidence is preserved separately in [testing](testing.md) and [the implementation report](implementation-report.md).

## GitHub Actions instructions

The actual configured remote was verified as [hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce](https://github.com/hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce). It is **public** and had **no published releases** when inspected on 2026-10-15.

1. Review and commit/push these source changes yourself when ready. No commit, push or tag was performed by this task.
2. A maintainer must separately review/create an existing `v1.0.0` tag containing the updated tools/workflows. Version and `readme.txt` Stable tag must match. The workflow never creates a tag and requires the tag’s clean checkout to match `HEAD`.
3. Once the workflow is on the default branch, open **Actions → Verify Development Distribution → Run workflow** and enter the existing reviewed tag.
4. The identity job validates the tag. The reusable CI workflow runs PHP 8.2/8.3/8.4 syntax/unit/PHPCS/PHPStan/packaging checks plus the disposable MySQL/WooCommerce integration job, installed-ZIP smoke checks, missing dependencies and runtime-enabled Plugin Check.
5. Only after CI succeeds does the package job recheck identity, scan source, build/verify ZIP+checksum+manifest, and scan every extracted runtime file.
6. In a **private repository**, the final step uploads only those three verified files as `stripe-development-v1.0.0`, retained for 14 days. Download them from the run’s Artifacts section and recheck the SHA-256 locally.
7. In the current **public repository**, that ZIP-upload step is skipped; the run records the reason in its summary. A private copy with the same reviewed source/tag can be used for private artifact review. This task does not change repository visibility or create that copy.

Artifacts require a signed-in user with repository read access. A public repository’s Actions artifact is therefore not private to maintainers. The explicit repository-privacy guard preserves the requested private-only development distribution. [GitHub artifact access documentation](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts).

The workflow is manual-only, uses pinned official action/scanner references, and has `contents: read`. There is no draft/publish job, write-token job, tag creation command, public release action or readiness override input. It cannot silently turn the development build into a release.

## Future approved draft and publication

These instructions are a later maintainer procedure, not an action taken or enabled by this task:

1. Complete merchant Stripe test-mode success/decline/3DS/capture, native checkout/webhook/duplicate-retry and device-return acceptance; review persistent-cache/compatibility/security evidence and confirm publisher/source/brand rights. Review all [publication gates](publication-readiness.md).
2. Review the final source, rerun all checks and decide whether version 1.0.0 is still appropriate. Any future version change is separately authorized work.
3. Approve the source tag and release notes. Use GitHub **Releases → Draft a new release** and select the existing reviewed tag; save it as an **unpublished draft**.
4. Upload the verified `quixdevs-stripe-rest-payments.zip`, `.zip.sha256` and `package-manifest.json` as assets. Compare the uploaded/downloaded checksum and test installation on staging.
5. Review notes, licensing, supported versions and acceptance evidence. **Publish the approved draft manually** only after explicit maintainer approval. Never convert a pending development build into a stable release by changing a filename or workflow input.
6. For an approved stable release eligible as latest, promote the following URL in the README only after the exact asset exists:

```text
https://github.com/hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce/releases/latest/download/quixdevs-stripe-rest-payments.zip
```

Drafts and prereleases do not qualify as the latest stable release. [GitHub release API semantics](https://docs.github.com/en/rest/releases/releases#get-the-latest-release).

A future automated draft-preparation job may be added only after these gates are evidenced and reviewed. It must use a protected maintainer approval boundary, existing-tag verification, verified artifacts, draft-only creation and a refusal to overwrite published releases. This development workflow deliberately contains no release-write path.

## User installation

Once an installation asset is approved, install WooCommerce and the exact supported official Stripe gateway, download the approved lightweight ZIP from **Releases → Assets**, then use **WordPress → Plugins → Add Plugin → Upload Plugin → Install Now → Activate**. Review **WooCommerce → Stripe REST Payments** and follow the [authentication](authentication.md), [API](rest-api.md) and [security](security.md) guides. Store owners do not run Composer.

Until approval, obtain development builds privately and use isolated/staging environments only. Packaging success does not establish payment acceptance, publish authorization or production readiness.
