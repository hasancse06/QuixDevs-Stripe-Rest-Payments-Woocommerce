# Draft release notes — 1.0.0

QuixDevs Stripe REST Payments adds authorized REST preparation and server-side status verification for existing WooCommerce Stripe customer orders. Apps hand payment collection to the native store payment page; the official extension handles PaymentMethods, PaymentIntents, authentication and webhooks.

Includes customer/scoped-server authorization, persistent preparation locks, hashed idempotency records, safe diagnostics, HPOS/legacy integration tests, Ionic Angular browser handoff examples, Postman and a Composer-free plugin package.

Inspected extension: 11.0.1 only. Executed local environment: PHP 8.4.13, WordPress 6.9, WooCommerce 10.9.0, Stripe 11.0.1. Provider HTTP was mocked; this is not evidence of Stripe production acceptance.

**Do not publish this as a stable production release.** Merchant test-mode and checkout/webhook acceptance, ownership attestation and publication gates in publication-readiness.md must be completed. Guest API access, embedded Payment Element, native SDK payments, subscriptions and split Stripe methods are unsupported.
