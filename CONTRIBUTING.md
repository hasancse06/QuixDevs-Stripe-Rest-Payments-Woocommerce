# Contributing

Use PHP 8.2+ and Composer for development. Run `composer install`, `composer test`, `composer lint`, and `composer analyse`. The custom production autoloader removes any customer Composer requirement.

Real integration tests require an explicitly disposable WordPress/MySQL installation; follow docs/testing.md. Never point tests at a merchant site. All test provider traffic is mocked. Run `composer package` and check the production allowlist before proposing changes.

Keep controllers thin, validate authorization before provider access, use WooCommerce CRUD for order data, preserve preparation locks, and do not introduce another gateway, credential store or webhook. Changes to Stripe internal interfaces must pin and inspect the extension and include failure/recovery tests.

Coding conventions use WordPress formatting, snake_case methods and PSR-4 namespaced files. PHPCS intentionally permits PSR-4 filenames and concise typed documentation. Narrow inline exceptions document domain-message escaping false positives: domain exceptions become JSON via WordPress, never direct HTML. The two direct options-table queries provide atomic insert-only lock acquisition and ownership-conditional release; comments explain why add_option/delete_option cannot replace them. PHPStan uses versioned WordPress/WooCommerce stubs, exact Stripe interface stubs and dynamic version constants; no error baseline is used.

Open a focused issue/patch without credentials or personal data. Publication requires completion of docs/github-publishing-checklist.md.
