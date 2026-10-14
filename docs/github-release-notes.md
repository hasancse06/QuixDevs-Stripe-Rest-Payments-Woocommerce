# QuixDevs Stripe REST Payments v1.0.0

REST API payment preparation and verification for WooCommerce stores using the official Stripe Payment Gateway.

**Development build for staging review.** Maintainer approval covers preparing an unpublished GitHub draft; it does not establish real Stripe payment acceptance or production compatibility. Merchant acceptance and publisher-rights review remain documented release gates.

## What this version provides

- Authenticated payment preparation for existing customer orders assigned to the primary `stripe` gateway.
- Native WooCommerce order-pay browser handoff; the customer signs in as the order owner.
- Read-only payment status verification against Stripe and the persisted WooCommerce order context.
- Order ownership authorization, or explicitly scoped and assigned backend integration users.
- Hashed idempotency records and persistent per-order locks protecting duplicate preparation.
- WooCommerce CRUD with recorded legacy-storage and HPOS integration coverage.
- Safe error responses, no-store headers, native diagnostics, client examples and a Postman collection.

The official WooCommerce Stripe extension collects cards, creates/confirms PaymentIntents, handles issuer authentication and webhooks, and updates payment status. This addon performs no Stripe mutation or custom settlement operation. Applications display success only when the verified status response reports `paid: true`.

## Requirements

PHP **8.2+**, WordPress **6.9+**, WooCommerce **10.9+**, HTTPS and the official WooCommerce Stripe Payment Gateway **exactly 11.0.1**, enabled and configured with cards enabled. The exact Stripe pin protects inspected internal interfaces; other Stripe versions are disabled pending contract verification.

Declared minimums are guards, not separately verified environments. Local checks used PHP 8.4.13, WordPress 6.9, WooCommerce 10.9.0, Stripe 11.0.1 and an isolated MariaDB 10.4.28 fixture.

## Installation for staging review

1. Install/activate WooCommerce and the required official Stripe gateway; configure authorized test-mode merchant settings.
2. Download **`quixdevs-stripe-rest-payments.zip`** from this release's Assets. GitHub's automatic source ZIP includes development files and is not the installation asset.
3. Open **WordPress Admin → Plugins → Add Plugin → Upload Plugin**, choose the ZIP, install and activate.
4. Review **WooCommerce → Stripe REST Payments** and resolve diagnostics before integration.
5. Follow the authentication/API guides and complete merchant acceptance before considering production use.

The lightweight ZIP has the correct plugin root and its own production autoloader. No Composer installation is required on the store. The accompanying `.zip.sha256` verifies the exact downloaded package.

## Known limitations

- No guest API access, embedded Stripe Payment Element or native mobile SDK confirmation.
- No subscription renewals, custom order types, split Stripe gateways or extension versions other than 11.0.1.
- Browser owner login is separate from app/backend authentication; no session bridge or deep-link handler is included.
- Preparation returns a native payment URL; it never creates an intent or charges a card. Existing/uncertain attempts need reconciliation instead of a fresh URL.
- Persistent preparation locks do not expire automatically. Crashed-worker recovery requires operator reconciliation.
- Provider `succeeded` alone is not proof of a reconciled WooCommerce paid order. The official gateway owns settlement and fulfillment status.

## Verification and remaining acceptance

Recorded checks include 51 unit tests / 93 assertions, 18 real WordPress/WooCommerce integration tests / 81 assertions, legacy and HPOS storage, process lock contention, packaging/draft safety regressions, PHP syntax, PHPCS, PHPStan level 5, runtime-enabled Plugin Check, and native ZIP upload/install/activation. Release helper tests mock GitHub CLI/API operations; they are not evidence of a live release upload.

Stripe HTTP was mocked or blocked. Real merchant success/decline/3DS/capture, full browser checkout/webhook recovery and duplicate attempts, mobile return behavior, broader hosting/version/cache compatibility, and publisher/source/brand rights require final review. No production keys or real charges were used.

The workflow creates an **unpublished prerelease draft** and never publishes it. Review these limitations and the documented evidence before choosing whether to publish a development prerelease or an approved stable release. A draft or prerelease does not activate GitHub's latest stable download URL.

## Documentation and maintainer

[README and installation](https://github.com/hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce/blob/v1.0.0/README.md) · [REST API](https://github.com/hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce/blob/v1.0.0/docs/rest-api.md) · [Authentication](https://github.com/hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce/blob/v1.0.0/docs/authentication.md) · [Publication readiness](https://github.com/hasancse06/QuixDevs-Stripe-Rest-Payments-Woocommerce/blob/v1.0.0/docs/publication-readiness.md)

Developed and maintained by **Md Abu Hasan (M A Hasan)** under **QuixDevs**. New implementation: MIT, Copyright © 2026 QuixDevs, subject to the documented ownership/licensing record. Independent addon; no official Stripe or WooCommerce endorsement is implied.
