# QuixDevs Stripe REST Payments

REST API Payment Integration for WooCommerce Stripe.

**Development-only build, target 1.0.0.** Real merchant payment/browser/webhook acceptance and ownership confirmation remain publication gates. Do not deploy this as a verified production release.

This addon lets authorized external applications prepare an existing customer order, open the store's native WooCommerce Stripe payment page, and inspect server-verified payment status. It adds no gateway, credentials or webhook and never settles orders itself. Embedded Payment Element, native SDK confirmation, guest orders, subscriptions and split Stripe gateways are unsupported.

Requires PHP 8.2+, WordPress 6.9+, WooCommerce 10.9+, HTTPS and official WooCommerce Stripe Gateway **exactly 11.0.1**, enabled/configured with cards enabled. Executed fixture environment: PHP 8.4.13 / WordPress 6.9 / WooCommerce 10.9.0 / Stripe 11.0.1, provider HTTP mocked.

Upload this directory/ZIP through WordPress Plugins and activate on staging. No Composer installation is required. Open WooCommerce → Stripe REST Payments and resolve diagnostics. Configure all Stripe credentials in the official gateway.

- POST `/wp-json/quixdevs-stripe-rest-payments/v1/orders/{order_id}/prepare`
- GET `/wp-json/quixdevs-stripe-rest-payments/v1/orders/{order_id}/status`

POST requires a stable Idempotency-Key and an empty body or empty JSON object. Use a WordPress cookie/REST nonce or backend-only Application Password. Only an order owner or an explicitly assigned capable integration user is authorized. The customer signs in separately in the payment browser. Never embed administrator credentials in a mobile application, log payment URLs, or cache payment routes.

[REST contract](docs/rest-api.md) · [Authentication](docs/authentication.md) · [Lifecycle](docs/payment-flow.md) · [Retries/recovery](docs/payment-idempotency.md) · [Errors](docs/error-codes.md) · [Security](docs/security.md) · [Ionic Angular](docs/examples/ionic-angular.md) · [Postman](docs/postman/README.md).

Display success only when the status response says `paid: true`. Timeouts are uncertain; do not start another payment. Preparation locks survive crashes and need explicit operator reconciliation before clearing.

MIT for the new implementation, Copyright © 2026 QuixDevs. Developed and maintained by Md Abu Hasan (M A Hasan), [hasan.online](https://hasan.online/). Independent addon with no official Stripe/WooCommerce endorsement.
