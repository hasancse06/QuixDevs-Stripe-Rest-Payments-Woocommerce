=== QuixDevs Stripe REST Payments ===
Tags: woocommerce, stripe, rest-api, payments, mobile
Requires at least: 6.9
Tested up to: 6.9
Requires PHP: 8.2
Requires Plugins: woocommerce, woocommerce-gateway-stripe
Stable tag: 1.0.0
License: MIT
License URI: https://opensource.org/license/mit/

Secure REST API payment integration for WooCommerce stores using the official Stripe Payment Gateway.

== Description ==

REST API Payment Integration for WooCommerce Stripe, published under QuixDevs.

This development build extends the official WooCommerce Stripe Payment Gateway with authorized native order-pay preparation and read-only payment verification. It adds no checkout gateway and stores no merchant credentials. Stripe PaymentMethods, PaymentIntents, authentication and webhooks remain managed by the official gateway.

Requires WooCommerce 10.9 or newer and WooCommerce Stripe Gateway exactly 11.0.1, enabled/configured with cards enabled. PHP 8.2 and WordPress 6.9 are minimum guards; executed integration tests used PHP 8.4.13, WordPress 6.9, WooCommerce 10.9.0 and Stripe 11.0.1 with mocked provider HTTP. Real merchant payment acceptance is outstanding. Not a production-approved release.

== Installation ==

1. Install and configure required official plugins on a staging HTTPS store.
2. Upload and activate QuixDevs Stripe REST Payments.
3. Open WooCommerce → Stripe REST Payments and resolve diagnostics.
4. Integrate the authenticated endpoints using the included README and developer guides in the source repository.

== Configuration ==

Configure Stripe only in WooCommerce payment settings. Use WordPress cookie authentication with a REST nonce, or Application Passwords on a trusted server. Separate integration users need the dedicated capability and explicit per-order assignment described in the source documentation. Never embed merchant keys or shared administrator credentials in mobile applications.

== API documentation ==

POST /wp-json/quixdevs-stripe-rest-payments/v1/orders/{order_id}/prepare
GET /wp-json/quixdevs-stripe-rest-payments/v1/orders/{order_id}/status

POST requires Idempotency-Key (16–128 letters/digits/underscore/hyphen) and an empty body or {}. Existing non-guest customer orders must belong to the caller or be explicitly assigned to a capable integration user. Orders must be assigned to stripe. The response provides a native order-pay URL for a new payment, or pending state for an existing intent. GET verifies Stripe state and WooCommerce settlement without modifying orders.

== External services ==

The addon contacts https://api.stripe.com/v1/payment_intents/{stored_intent_id} to verify a payment for an authorized order. It sends the official gateway's existing merchant authentication headers and stored intent ID. Preparation also verifies existing intents when present. It does not create a new Stripe account, submit card data or alter webhook configuration. Stripe processes payments through the required official extension.

Stripe terms: https://stripe.com/legal/ssa
Stripe privacy: https://stripe.com/privacy

== Security requirements ==

HTTPS is mandatory. Do not cache payment routes, record payment URLs in analytics, or log authentication headers. Guest API access is unsupported. The payment browser requires the owner's native store login. Payment page return URLs do not prove payment. Display success only when status.paid is true. Rate-limit authenticated payment verification at the infrastructure boundary.

== Frequently Asked Questions ==

= Is this another Stripe gateway? =
No. The official WooCommerce Stripe Payment Gateway is required.

= Can I submit raw cards or confirm a PaymentIntent directly? =
No. This version uses the store's native payment page. Embedded Payment Element and native SDK flows are unsupported.

= Why are my API routes missing? =
Resolve the dependency, HTTPS, version and merchant-configuration diagnostics.

= Does the addon mark orders completed? =
No. WooCommerce and the official gateway control payment and fulfillment status.

= Does it support HPOS? =
The addon uses WooCommerce CRUD and has passed legacy and HPOS database tests in the documented environment. Real payment acceptance remains outstanding.

== Screenshots ==

1. QuixDevs native WooCommerce diagnostics, captured from a disposable local WordPress installation.
2. Dependency warning with the gateway disabled in the disposable fixture.
3. Versioned preparation and status API endpoint details.
4. Test-mode configuration and safe diagnostic details.

== Changelog ==

= 1.0.0 =
Development implementation of authenticated order-pay preparation, verification, persistent preparation locking and admin diagnostics. Publication gates remain open.

== License ==

New implementation: MIT, Copyright 2026 QuixDevs. Source ownership confirmation is required before publication. Original EventPro source is excluded from the package.
