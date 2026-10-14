# Diagnose hidden or duplicate v1.0.0 releases

Repository: [hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce](https://github.com/hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce). The existing `v1.0.0` tag remains at `d93820ce3c64dd70fe63f851df328bcfe8830463`.

## Obtain the authoritative inventory

After the maintainer reviews and deploys the correction to `master`, open **Actions → Prepare Draft Release → Run workflow**. Select **master**, enter **v1.0.0**, and select **diagnostics_only**. Use a fresh dispatch; rerunning an older run executes its older workflow commit. This task does not commit or push the correction.

The existing identity, quality and package gates still run. The final job uses its existing `contents: write` permission and supplies `${{ github.token }}` through `GH_TOKEN`; no additional secret or PAT is configured. The diagnostic step performs authentication checking and GET requests only. With diagnostics selected, the create/upload step is skipped. Nothing deletes or publishes releases, or creates/moves tags.

Open the run summary's **Release inventory diagnostics** section. It reports:

- `unique_release_count`: distinct matching numeric release IDs, each confirmed through GET by ID.
- `draft_count` and `published_count`: separate counts from the verified records.
- `tag_commit`: the existing remote tag’s safely resolved commit, checked again after inventory verification.
- `matching_occurrences`: matching rows across all list pages.
- `repeated_occurrences`: rows repeating a previously counted ID.
- `pages_scanned` and the inventory classification.
- For each record: release ID, name, exact tag, draft/prerelease status, actual GitHub HTML URL, created timestamp and attached asset names.
- A clickable review link for each valid same-repository GitHub HTML URL.

Only selected metadata is printed. Release bodies, authors, authorization headers, CLI authentication output and raw server errors are omitted. Known authentication values and recognizable GitHub tokens are redacted from metadata; JSON escaping prevents names containing control characters from becoming workflow commands. Credentials/query strings and external URLs are not included in review links. No editor URL is invented from a numeric ID.

Before listing releases, the helper confirms repository identity and reads the existing tag reference, safely peeling annotated tags. It checks that the tag still resolves to the same commit after inventory verification. These are GET requests and never create or move a tag. The helper queries:

```text
GET /repos/hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce/releases?per_page=100&page=1
```

It reads subsequent numbered pages until a page contains fewer than 100 rows. Each distinct matching candidate is confirmed with:

```text
GET /repos/hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce/releases/{id}
```

It fails closed on API errors, invalid IDs, incomplete pagination, disappearing records or a changed tag during verification. The published-release-by-tag lookup is not used by diagnostic mode. Normal release preparation retains its published-release refusal and package/source/notes/tag/checksum safeguards.

For a trusted authenticated local environment, the same read-only command is:

```sh
python3 tools/create-draft-release.py --diagnose \
  --repo hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce --tag v1.0.0
```

No expected commit, clean checkout, local build or package modification is required to list metadata. Local GitHub authentication must already be available; no credentials should be pasted into logs or chat. Authorization is evaluated through the authenticated repository/tag/releases API responses. The helper does not require repository `permissions.push` or a normal user collaborator role for an Actions installation token. Real HTTP failures still stop diagnostics with a safe method, endpoint, status and category.

## Why the Releases page can look empty

Public visitors can see published releases; draft listings require authenticated push access. An empty public Releases page or unauthenticated API list does not establish that no draft exists. Sign in as a repository maintainer to review the reported HTML URLs. [GitHub release visibility](https://docs.github.com/en/rest/releases/releases#list-releases).

The October 15 local public probe returned **zero public release records**, including zero visible `v1.0.0` records. Local GitHub CLI authentication and `GH_TOKEN`/`GITHUB_TOKEN` were unavailable. Consequently, the live draft count, IDs, review URLs and exact historical conflict remain **unconfirmed** until the authenticated workflow report is collected. No test fixture IDs are presented as real releases.

## Duplicate detection and resolution

The previous loop appended every row whose `tag_name` matched `v1.0.0`, then rejected `len(matches) > 1`. It never checked whether rows referred to the same numeric ID. A repeated ID on one page or across pages could therefore be misclassified as multiple releases. The regression tests reproduce that defect.

The corrected lookup deduplicates numeric IDs, then reads each once by ID. Distinct IDs remain distinct even when names, timestamps or asset names match. This corrects row-count false positives while preserving the stop on real conflicts. The diagnostic report uses the same inventory function as normal draft lookup.

An earlier helper created drafts and then tried to verify them through the published-release-by-tag endpoint. If that GET returned 404 after creation, retrying the older helper could create another draft. That is a possible origin of separate records, not a confirmed explanation for this repository's present conflict. Confirm distinct IDs and created timestamps before assigning that cause. [GitHub by-tag release semantics](https://docs.github.com/en/rest/releases/releases#get-a-release-by-tag-name).

| Authenticated result | Safe next step |
| --- | --- |
| Zero unique records | No matching release was visible to this authenticated caller. Check its draft visibility and tag identity before normal preparation. |
| One unique ID, multiple occurrences | The duplicate error was a row-count false positive. The corrected helper reuses this record if its draft/source/notes/assets satisfy all existing checks. |
| One published record | Keep it unchanged; normal preparation refuses to edit it. |
| Multiple distinct draft IDs | Open every reported URL as a maintainer. Compare source commit, notes, timestamps and asset bytes before choosing the intended draft. Keep all records during review. |
| Published and draft records share the tag | Stop; leave published records unchanged and review unpublished drafts separately. |
| Inventory verification/API error | Diagnose the safe method/endpoint/status/category. Do not assume an empty inventory or create a fallback release. |

For real duplicate drafts, first retain a copy of the notes and any assets you need. Verify the intended ZIP against the checksum below and the source commit. Once the maintainer has explicitly decided which unpublished draft to retain, redundant **draft release records** may be removed manually through GitHub's release editor. Leave the Git tag intact and do not select tag-cleanup options. This diagnostic contains no deletion command and does not choose a record automatically. If there is uncertainty about a record's contents or publication status, keep it and continue review.

After the authenticated inventory contains a single matching draft, a fresh normal workflow run can resume missing assets. Existing source, edited notes or asset mismatches still stop preparation; nothing uses `--clobber` or publishes the draft.

## Preserved artifact and local verification

The runtime ZIP remains **27 files, 24,919 bytes**, with SHA-256:

```text
3d0acdb3dc749dccbff41bb91f0a48a805a81277749edc87ba85d5fbd3c57735
```

This correction changes the helper, release workflow, draft regression tests and this diagnostic guide. The already-modified `docs/release-distribution.md` was present before this task and remains byte-for-byte unchanged by it. Payment PHP, plugin version, package allowlist/verifier, existing tag, checksum sidecar and prior checks remain intact.

Local validation: **55 distribution tests** (40 draft-release/diagnostic tests and 15 packaging tests), actionlint on CI/release workflows, source and repository/documentation checks, ZIP/source/checksum/CRC/PHP syntax/autoload verification, and diff whitespace checks. Added coverage includes repeated IDs within/across pages, distinct-ID refusal without mutations, read-only empty/single/multiple reports, draft/published metadata, changed/disappearing records, auth/visibility failures, safe metadata/summary output, token redaction, CLI diagnostics without a commit argument and workflow mutation gating. No live authenticated Actions diagnostic or payment acceptance test is claimed.

## Installation-token authentication correction

The previous diagnostic incorrectly treated this collaborator-permission condition as a mandatory installation-token authorization check:

```python
permissions = repository.get('permissions', {})
if isinstance(permissions, dict) and permissions.get('push') is False:
    raise ReleaseError('Authenticated caller lacks push access; draft inventory visibility cannot be verified.')
```

This produced the reported error before the releases API was queried, even with the workflow's confirmed Contents write permission and `GH_TOKEN`. The guard has been removed. Private CLI authentication checking remains; repository identity, the existing remote tag and the fully paginated releases API are verified using their real responses. Every distinct matching ID is re-read, and the tag commit is checked again before reporting results. False or absent collaborator flags cannot block a successful installation-token inventory. API denials and malformed or incomplete responses remain failures; no write probe is used to test permissions.

Local validation for this correction: **59 distribution tests** (44 draft/diagnostic and 15 packaging tests), actionlint for both workflows, source/repository checks and ZIP/source/checksum/CRC/PHP syntax/autoload verification. New regressions cover installation tokens with false/absent collaborator flags, zero/one/multiple drafts, real HTTP response parsing for repository/tag/inventory/ID denials, pagination with repeated IDs, annotated tags and a tag changing during diagnostics. The workflow configuration, normal draft creation/published-release protections, runtime/version, existing Git tag, ZIP and checksum sidecar remain unchanged. No authenticated remote run, commit, push, deletion or publication was performed by this correction.
