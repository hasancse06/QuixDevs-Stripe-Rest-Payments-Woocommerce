# Lightweight distribution and release preparation

Prepared 2026-10-15 for **QuixDevs Stripe REST Payments 1.0.0**. This is packaging and release engineering work. The payment implementation, request/response contract, authentication, authorization, idempotency, Stripe adapter, order CRUD and HPOS behavior are unchanged. All runtime classes are byte-identical to the starting source. One extra space before `Author` in the main plugin header comment was removed to pass PHPCS; no version change occurred.

**Package status remains development-only.** Merchant payment acceptance and publisher-rights/publication requirements in [publication readiness](publication-readiness.md) remain documented. The maintainer has now approved preparing an unpublished GitHub draft in the public repository. Tests/builds use read-only tokens; only the final draft job has `contents: write`. The workflow creates no tags and never publishes a release.

## Files changed

- `tools/package.py`: reused packager, explicit allowlist, lightweight `dist/` output, checksum and detailed manifest.
- `tools/runtime-files.json`, `tools/verify-package.py`, `tools/prepare-release.py`: new runtime, autoload, archive and existing-tag guards.
- `tools/install-gitleaks.py`, `.gitleaks.toml`: pinned official secret scanner and narrow fixture exception.
- `tools/installation-smoke.php`, `tools/verify-plugin-check.py`, `tests/Packaging/test_package.py`: installed-package and packaging verification.
- `.github/workflows/release.yml`, `.github/workflows/ci.yml`: tag/manual draft preparation with preserved automated checks and write permission scoped to the draft job.
- `tools/check-repository.py`, `tools/check-source.py`, `tools/provision-test-site.sh`: `dist/` checks and reproducible Plugin Check fixture version.
- `README.md`, `CHANGELOG.md`, `docs/github-publishing-checklist.md`, this guide: download/install, draft notes and distribution instructions.
- `quixdevs-stripe-rest-payments.php`: historical header-comment whitespace correction only; untouched during draft-workflow finalization.
- `tools/create-draft-release.py`, `tests/Packaging/test_draft_release.py`, `tests/Packaging/test_package.py`, `docs/github-release-notes.md`: draft-only CLI/asset safety, regression coverage and accurate release notes.

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
| Packaging regressions | 15 tests passed: completeness, deterministic build, missing/symlinked/new files, source drift, root, dependency/version/tag guards, scoped draft-workflow permissions, and fail-closed Plugin Check result handling |
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

## Files changed for draft-workflow finalization

- `.github/workflows/release.yml`
- `tools/create-draft-release.py` (new)
- `tests/Packaging/test_draft_release.py` (new)
- `tests/Packaging/test_package.py`
- `README.md`
- `CHANGELOG.md`
- `docs/github-release-notes.md`
- `docs/github-publishing-checklist.md`
- `docs/release-distribution.md`

The runtime PHP, version 1.0.0, production allowlist, packager and existing CI are unchanged. Earlier distribution work is described separately above.

## Draft-workflow finalization verification

For the newly authorized draft process, local verification passed: **51 unit tests / 93 assertions**, **18 WordPress/WooCommerce integration tests / 81 assertions**, and **33 distribution tests** (15 existing packaging guards plus 18 draft-release regressions). PHPCS, PHPStan level 5, all runtime PHP syntax, runtime-enabled Plugin Check (0 errors / 0 warnings), actionlint for both workflows, source/extracted-package Gitleaks and documentation checks passed.

The added tests mock the GitHub CLI/API and cover draft creation flags/assets/notes, idempotent retries, missing/different assets, published-release refusal, edited notes, moved/annotated/cyclic tags, API errors, publication during upload, and artifact checksum/notes tampering and a dirty source checkout. They do not claim a live GitHub Actions run or actual draft creation. Runtime classes, bootstrap/version metadata, the allowlist, existing PHP tests, existing CI and dated implementation/testing/readiness records remain unchanged; the ZIP retains the checksum above. The obsolete private-only workflow regression was replaced with checks that write permission exists only in the unpublished-draft job and that required CI/publication safeguards remain intact.

## Approved GitHub draft-release workflow

The configured remote is [hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce](https://github.com/hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce), a public repository. The maintainer explicitly approved draft preparation; the earlier private-artifact-only restriction is superseded. Public preparation does not prove merchant acceptance or turn the package's recorded development status into PASS.

1. Review and commit the release automation correction on the default branch, currently `master`. Push it only when the maintainer chooses to do so.
2. Keep the existing **v1.0.0** tag unchanged. Its source commit is `d93820ce3c64dd70fe63f851df328bcfe8830463`; plugin header and `readme.txt` Stable tag stay 1.0.0.
3. A push of a `v*` tag triggers **Prepare Draft Release**. Alternatively choose **Actions → Prepare Draft Release → Run workflow** and enter the existing reviewed tag.
4. The identity job verifies the clean tag/commit and version. The unchanged reusable CI runs PHP syntax, PHPUnit, WooCommerce integration, PHPCS, PHPStan, packaging checks, installed-ZIP smoke checks and runtime-enabled Plugin Check. The existing PHP 8.2/8.3/8.4 quality and MySQL 8 integration jobs remain required.
5. After CI succeeds, the package job rechecks identity, scans maintained source, builds and verifies the allowlisted ZIP/checksum/manifest, and scans the extracted runtime. Professional notes are generated from [the release notes source](github-release-notes.md) with this exact package size, file count and checksum.
6. Verified artifacts (ZIP, checksum, manifest and generated notes) are passed to the final draft job, including in public repositories. Actions artifacts use repository-reader access; they are no longer described as private to maintainers. [GitHub artifact access](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts).
7. Only the draft job has `contents: write`. It checks out the verified commit, revalidates the downloaded package, confirms repository and remote tag identity, resolves drafts through the authenticated release inventory, and calls official **`gh release create --draft --prerelease --verify-tag`** with the exact target commit and notes. It attaches **`quixdevs-stripe-rest-payments.zip`** and **`quixdevs-stripe-rest-payments.zip.sha256`**.
8. The result is an **unpublished prerelease draft** for explicit maintainer review. There is no automatic publish command or release-readiness override. New release drafts are prereleases because the package still records development-only acceptance status.

The workflow uses pinned official actions/scanner references and only the final job receives a write token. `--verify-tag` prevents implicit tag creation; `--draft` keeps the release unpublished. [Official GitHub CLI create options](https://cli.github.com/manual/gh_release_create).

## Existing releases and retries

The helper [create-draft-release.py](../tools/create-draft-release.py) validates local source/manifest/CRC/checksum/autoloading, exact artifact notes and remote tag identity before any release mutation. Annotated tags are peeled safely. Only HTTP 404 from the exact published-release lookup `GET /repos/{owner}/{repo}/releases/tags/v1.0.0` has a normal missing state. Creation additionally requires confirmed repository/tag identity and a complete successful authenticated release inventory with no matching draft. Every other 404 and authentication/server failure stops preparation. Drafts are re-read by numeric release ID before and after each upload.

- **Published release:** stop without changing its notes or assets.
- **Matching draft:** reuse it; identical existing assets are left untouched and only missing assets are uploaded.
- **Conflicting source, notes or assets:** stop for manual review. Maintainer note edits are never overwritten.
- **Tag moved or draft published during preparation:** stop remaining operations and require inspection.

Existing assets are compared by provider SHA-256 digest, with byte-download comparison when a digest is unavailable. Newly uploaded assets are verified again. The helper uses no `--clobber`, asset-deletion, release-edit/publish or tag-creation command. Keep the draft unpublished until the workflow finishes: GitHub provides no atomic draft-only condition on an asset upload, so state is checked before and after each operation. Existing published assets are never overwritten.

Draft creation/API handling is tested with mocked GitHub CLI responses; no actual release was created locally and remote Actions execution is not claimed as passed.

## October 15 draft lookup correction

The original helper tolerated the initial by-tag lookup's 404, but reused that endpoint **without** the missing-release exception immediately after `gh release create --draft`. The exact faulty draft-verification request was:

```text
GET /repos/hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce/releases/tags/v1.0.0
```

GitHub documents this as a **published-release** lookup. It cannot be relied on for an unpublished draft. The original test double incorrectly returned drafts from this endpoint, masking the defect. The corrected helper scans all authenticated release-list pages, resolves the matching draft ID, and verifies it with `GET /repos/{owner}/{repo}/releases/{id}`. Identical drafts are resumed; conflicting notes/source/assets and published releases still stop preparation. [GitHub release lookup and draft visibility](https://docs.github.com/en/rest/releases/releases#get-a-release-by-tag-name).

Live unauthenticated checks returned 200 for the repository and annotated tag, and 404 for the published-release lookup. Public Actions metadata confirmed that the identity, quality and package jobs succeeded and the draft step failed. The failed step's private log and current draft inventory were inaccessible without authentication, so the precise historical request cannot be independently proven from that generic error alone. The by-tag post-create failure is reproduced in tests; it is not evidence of a missing repository or tag. The supplied original error string came from the GET API helper; a failed create/upload CLI command would have emitted a different generic CLI error. This rules out that string being emitted directly by POST release creation, while the old logging still prevents definitive historical attribution among the GET calls. A newly reported failure now includes the safe method, endpoint, HTTP status and category.

| Response/request | Handling |
| --- | --- |
| GET published release by tag: 404 | Check authenticated inventory after confirming repository/tag; create only if all pages succeed and no matching draft exists |
| GET repository: 404 | Repository missing or hidden by token access; stop |
| GET tag reference/object: 404 | Tag missing or inaccessible; stop |
| GET release inventory or numeric ID: 404 | Endpoint/release missing or inaccessible; stop |
| 401 | Missing/invalid authentication; stop |
| 403 | Token permission denial or rate limit; stop |
| POST release creation: 404 | Access or workflow-file permission restriction; stop; never infer a missing release |
| 422 / server errors / malformed response / invalid endpoint | Fail closed; no fallback creation |

Only the final draft job has `permissions: contents: write`, and its CLI receives `GH_TOKEN: ${{ github.token }}`. Both were already configured correctly. Keep Actions enabled, allow the pinned actions under any organization policy, and allow this job's requested Contents write permission. Do not grant write permission to every job or add a PAT just to repair the GET lookup. A 404 alone cannot prove a permission denial because GitHub can hide inaccessible resources.

GitHub separately documents that **creating** a release targeting a commit whose workflow files differ from the default branch requires Workflows write permission; `GITHUB_TOKEN` cannot receive that permission. A correction to `release.yml` can make this relevant to the unchanged older tag. If POST creation fails for that reason, an authorized maintainer must create an **unpublished** draft for the existing tag with the generated `dist/release-notes.md` and exact target commit, then let the workflow resume asset verification/upload. No published release or tag should be edited, and no token scope is broadened by this fix. [GitHub create-release restrictions](https://docs.github.com/en/rest/releases/releases#create-a-release).

For manual recovery from the default branch, the draft job extracts the corrected helper from `${{ github.workflow_sha }}` to `$RUNNER_TEMP`. `PYTHONPATH` points at the verified tagged source's tools; all runtime/package/notes/clean-checkout validation remains tied to the tag. This prevents a rerun from executing the broken helper stored in the unchanged tag and avoids altering the checked-out source. Existing tag-push jobs use their own workflow commit; old failed runs must be replaced by a fresh default-branch manual dispatch after the maintainer deploys the correction.

Local verification for this correction passed: **45 distribution tests** (30 draft-release and 15 packaging regressions), actionlint for both workflows, source checks, repository/documentation checks, and ZIP/source/CRC/checksum/PHP syntax/autoload validation. The tests cover first-release creation, draft/published states, repository/tag/inventory/ID failures, permission/server errors, pagination, safe diagnostics, and the temp-helper/tagged-source import arrangement. All 45 protected runtime/security/licensing/packaging/test/evidence files matched their initial hashes; HEAD, the existing tag object and the 27-file / 24,919-byte ZIP checksum were unchanged. Full payment suites were not rerun because their code and fixtures were untouched. Remote creation/upload was explicitly deferred by the maintainer; nothing was pushed or published.

## Deploying the correction without changing the tag

These commands are instructions for the maintainer; this task does not execute them:

```sh
git diff --check
git diff
git add .github/workflows/release.yml tools/create-draft-release.py tests/Packaging/test_draft_release.py docs/release-distribution.md
git commit -m "fix: resolve draft releases by ID and preserve v1.0.0 tag"
git push origin master
```

Then choose **Actions → Prepare Draft Release → Run workflow**, select **master**, and enter **v1.0.0**. Leave the existing tag unchanged. Review any reported API category before retrying; do not delete a matching draft or overwrite assets. No force push, tag move or automatic publication is required.

## Reviewing and publishing the draft

1. Wait for all workflow jobs and uploads to finish. Open the draft in **GitHub Releases**, review notes and both attached assets, and verify the downloaded ZIP checksum.
2. Review staging installation, security, source/brand/license rights and all actual acceptance limitations. A development prerelease must disclose unresolved acceptance; a stable production release requires the merchant/checkout/webhook/device and compatibility evidence in [publication readiness](publication-readiness.md).
3. Leave **Set as a pre-release** checked for a development distribution. Change that classification only after the required stable-release review and evidence; do not infer production acceptance from green mocked-provider tests.
4. **Publish manually only after explicit maintainer approval** using GitHub's draft editor. The workflow never publishes, edits an existing published release or creates/moves tags.
5. A qualifying approved stable release with the exact ZIP asset makes this README link available:

```text
https://github.com/hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce/releases/latest/download/quixdevs-stripe-rest-payments.zip
```

Drafts and prereleases do not qualify as the latest stable release. [GitHub release API semantics](https://docs.github.com/en/rest/releases/releases#get-the-latest-release).

## User installation

Once an installation asset is approved, install WooCommerce and the exact supported official Stripe gateway, download the approved lightweight ZIP from **Releases → Assets**, then use **WordPress → Plugins → Add Plugin → Upload Plugin → Install Now → Activate**. Review **WooCommerce → Stripe REST Payments** and follow the [authentication](authentication.md), [API](rest-api.md) and [security](security.md) guides. Store owners do not run Composer.

Before manual publication, use verified local/private review builds. Any published development prerelease must retain its acceptance limitations and staging-only guidance. Packaging success does not establish payment acceptance, publish authorization or production readiness.
