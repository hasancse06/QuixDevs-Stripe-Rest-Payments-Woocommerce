# Publication readiness — development-only

Assessed 2026-10-10. Target release version 1.0.0. Source existence and mocked provider tests do not establish production acceptance.

| Status | Item | Evidence / next action |
| --- | --- | --- |
| Implemented | Authenticated native order-pay preparation and read-only status | Two versioned routes, strict authorization/validation |
| Implemented | Idempotency and fail-closed persistent mutex | Insert-only SQL and owner-conditional release; no expiry |
| Implemented | Admin diagnostics, safe errors/logging, packaging and documentation | Runtime source, client examples and Postman |
| Verified | Unit tests | 51 tests / 93 assertions |
| Verified | Real WordPress/WooCommerce REST and datastore tests | 18 tests / 81 assertions; both legacy and HPOS |
| Verified | Process concurrency | Deterministic four-worker test plus five additional passes after fixing WP add_option upsert race |
| Verified | PHPCS / PHPStan / PHP syntax | No final errors; PHPCS has no warnings; PHPStan level 5 |
| Verified | Plugin Check | Extracted production package reports no errors |
| Verified | ZIP install/activation without Composer | Disposable WordPress with official plugins active |
| Verified | Dependency failures and lifecycle retention | No routes/fatals when dependencies missing; retention fixture tested |
| Verified | Original source preservation | Original SHA-256 hashes unchanged |
| Verified | Branding and screenshots | Exact export dimensions and genuine local admin captures |
| Not verified | PHP 8.2/8.3 and other WP/Woo versions | Minimum guards and planned CI are not executed combinations |
| Not verified | Remote GitHub Actions | Workflow prepared; no remote run/publication authorized |
| Not verified | Native devices and app return behavior | Capacitor v8 API docs checked; no device build/test |
| Not verified | Persistent external object caches / broader security audit | Review deployment and execute acceptance tests |
| Unsupported | Guest API, embedded Payment Element/native SDK confirmation | Native payment browser with owner login only |
| Unsupported | Other Stripe versions, split gateways, subscriptions and custom order types | Exact 11.0.1 / primary stripe / shop_order guard |
| Unsupported | Automatic unlock/reset or webhook/settlement replacement | Operator reconciliation and official gateway lifecycle required |
| Release blocker | Real merchant Stripe test-mode acceptance | Authorized test credentials needed; test success, decline, 3DS, capture and timeouts |
| Release blocker | Full native checkout / webhook / duplicate-submission acceptance | Verify classic, Blocks, Store API coexistence and async recovery |
| Release blocker | Publisher ownership/license attestation | Historical license is only a label; confirm QuixDevs/EventPro rights |
| Release blocker | Public directory/release review | Confirm publisher/contributor accounts, final requirements and explicit publication authorization |

Executed environment only: PHP 8.4.13, WordPress 6.9, WooCommerce 10.9.0, official Stripe 11.0.1, temporary MariaDB 10.4.28. All provider HTTP was blocked or mocked. No production credentials, charges, live database modifications, deployments, GitHub pushes or WordPress.org submissions occurred.

The development ZIP is available under build/. Its checksum is in package-manifest.json and implementation-report.md. It includes production runtime plus relevant API guides; promotional assets and development files are excluded. See [the implementation report](implementation-report.md) and [testing guide](testing.md) for the recorded local results and exact limits. Raw verification logs remain in the separate working project.
