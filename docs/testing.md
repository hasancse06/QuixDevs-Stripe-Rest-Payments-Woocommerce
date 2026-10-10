# Reproducible testing

Install development tools with `composer install`. Unit suite: `composer test`. Quality: `composer lint`, `composer analyse`; if a sandbox forbids PHPStan's local parallel-worker socket, run `vendor/bin/phpstan analyse --debug --no-progress` for serial analysis. No baseline or global error suppression is used. Stubs describe exact inspected gateway interfaces; dynamic constants avoid treating a stub's fake version as runtime truth.

## Disposable integration environment

Use a fresh database named `quixdevs_test` and a host/socket whose name contains `quixdevs`. Never use an existing store database. Set `QUIXDEVS_WP_ROOT` to an empty temporary path containing quixdevs, `QUIXDEVS_DB_HOST`, `QUIXDEVS_DB_USER`, `QUIXDEVS_DB_PASSWORD`, and `QUIXDEVS_DISPOSABLE_TESTS=1`. With WP-CLI installed, run `bash tools/provision-test-site.sh`, then `composer test:integration` with those environment variables retained.

The setup downloads WordPress 6.9, WooCommerce 10.9.0, Stripe 11.0.1 and Plugin Check, creates an explicitly disposable installation, and configures unmistakably dummy test credentials. Its mu-plugin blocks all external WordPress HTTP calls. Individual tests override selected reads with fixture responses. Bootstrap refuses unrecognized DB names/hosts. Integration tests create and delete dummy users/orders and switch the disposable store's order storage mode; they are destructive to their fixture, not safe on an existing site.

Local execution used an independent temporary MariaDB 10.4.28 instance with --skip-networking and a private Unix socket. The pre-existing machine database was never connected. PHPUnit uses real WordPress/WooCommerce objects and persistence, not WP's core test factories. Standalone tests use explicit minimal doubles. Four independent PHP subprocesses contend for one database option mutex through a barrier. An external persistent object cache was not installed.

Tests cover native handoff persistence/retries, both datastores, read-only settlement verification, provider projection, auth/ownership/server scope, malformed fields, route methods/permissions, no-store headers, core Application Passwords, forged cookie nonce, duplicate registration, disabled dependencies, changed amount, transaction mismatch, timeout and all seven Stripe states. See [the implementation report](implementation-report.md) for exact executed counts and limitations.

CI plans quality checks on PHP 8.2/8.3/8.4 and MySQL 8 integration on PHP 8.4. A workflow file is not a passing CI run; no remote CI was executed in this task. The historical plugin has no tests and is never loaded.

For merchant acceptance, use authorized Stripe test-mode credentials and official native checkout. Record versions, webhook delivery and real transaction references privately; never commit secrets. Production keys and live charges are prohibited.


## Recorded local results

The unchanged runtime was verified on PHP 8.4.13, WordPress 6.9, WooCommerce 10.9.0, Stripe 11.0.1 and a disposable MariaDB 10.4.28 database: 51 unit tests / 93 assertions; 18 database/REST integration tests / 81 assertions; five additional four-worker concurrency runs; PHPCS with no errors or warnings; PHPStan level 5 with no errors; PHP syntax; Plugin Check on the extracted runtime ZIP; ZIP installation without Composer; and deactivation/uninstall retention. These are local results, not a GitHub Actions run or merchant payment test.

GitHub preparation preserves the runtime, tests and dependency lockfile. Raw local verification output and uncropped captures stay in the separate working project; they are excluded from source uploads. The clean folder has additional checks for relative documentation/image links, image dimensions, archive contents and source exclusions. Run `python3 tools/check-repository.py` after documentation or branding edits.
