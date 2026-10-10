# REST API v1

Base URL: `https://store.example/wp-json/quixdevs-stripe-rest-payments/v1`.

All requests require HTTPS and an established WordPress identity. See authentication.md. Every route has a permission callback. Routes are absent until dependencies are ready; configuration changes are also rechecked in each permission callback. Preparation never charges; payment happens on the native store page. No guest API access.

## POST /orders/{order_id}/prepare

Purpose: authorize and persist a native payment handoff, or identify an already-existing Stripe attempt. `order_id` is a positive integer route field, at most 18 decimal digits. The caller must own a non-guest ordinary order or hold both explicit integration grants. The order must be assigned to `stripe`, require payment, have positive total, and be pending or failed. Paid/cancelled/refunded/on-hold orders cannot be prepared.

Headers:

- Core authentication: `Authorization: Basic <backend-only-application-credential>` or same-store cookies plus `X-WP-Nonce`.
- `Idempotency-Key`: required, 16–128 ASCII letters/digits/underscore/hyphen; generate once per order preparation and retain it across retries.
- `Content-Type: application/json` when sending `{}`.

Body: empty or an empty JSON object `{}` (JSON whitespace accepted). Maximum 2048 bytes. No optional body fields. Application query parameters, form data, uploaded files, arrays, payment identifiers, amount, currency, return URLs and card fields are rejected. Fields are not forwarded to Stripe.

Example:

```http
POST /wp-json/quixdevs-stripe-rest-payments/v1/orders/123/prepare
Content-Type: application/json
Idempotency-Key: demo-preparation-0001
X-WP-Nonce: <current-user-rest-nonce>

{}
```

New handoff, HTTP 200:

```json
{"order_id":123,"order_status":"pending","payment_state":"not_started","payment_verified":false,"paid":false,"flow":"woocommerce_order_pay","checkout_url":"https://store.example/checkout/order-pay/123/?pay_for_order=true&key=wc_order_DUMMY","reused":false}
```

Existing verified attempt, HTTP 202:

```json
{"order_id":123,"order_status":"pending","payment_state":"requires_action","payment_verified":true,"paid":false,"flow":"gateway_pending","checkout_url":null,"reused":true}
```

`checkout_url` is confidential order-payment context. Open it in the system browser, where the owner must authenticate independently. The addon does not restrict which methods native checkout displays; choose Stripe. If the customer switches to a different gateway, this API rejects later verification of that order.

Side effects: creates an atomic non-autoloaded options mutex for the request and a hashed preparation record in order metadata. It may GET an existing Stripe intent. It does not create/confirm/cancel intents or update WooCommerce payment/fulfillment status. The mutex is released in finally; a killed worker leaves a lock for operator review.

Same key/caller/unchanged order repeats the handoff with `reused: true`, after rechecking current payment state. Different key, caller or changed order context returns 409. Existing requires_payment_method/canceled states return 422; native store retry and operator reconciliation are outside this preparation endpoint. An uncertain provider state returns 503 and no fresh link.

## GET /orders/{order_id}/status

Purpose: read current Stripe verification and WooCommerce settlement for an authorized order. Same authentication/order scope as preparation. No body, query fields or optional fields. No Idempotency-Key required. Terminal orders can be inspected if still assigned to Stripe.

Example:

```http
GET /wp-json/quixdevs-stripe-rest-payments/v1/orders/123/status
X-WP-Nonce: <current-user-rest-nonce>
```

HTTP 200:

```json
{"order_id":123,"order_status":"processing","payment_state":"succeeded","payment_verified":true,"paid":true}
```

No intent yields `not_started`, `payment_verified: false`, `paid: false`, unless paid/transaction data without an intent makes the order ambiguous (409). `payment_verified` means provider state matches the order; it does not mean successful payment. `paid` requires succeeded, exact received amount, a valid latest charge, a matching persisted transaction, and WooCommerce's paid state. Display success only when `paid` is true.

The route is read-only apart from safe error diagnostics. It never initiates recovery payments or updates order status. Stripe errors/timeouts return 503, malformed responses 502, context mismatches or concurrent order changes 409. Poll with backoff (e.g. 3s → 5s → 10s, stop after two minutes and offer a later status refresh). Never poll indefinitely or treat an outage as failure to charge.

## Shared response and error rules

`order_id` is integer, `order_status` and `payment_state` are strings, `payment_verified`/`paid`/`reused` are booleans, `flow` is one of the two strings above, `checkout_url` is string|null. Flow/url/reused appear only on prepare responses. No client_secret, API key, customer email, order key as an independent field, or raw provider response is returned.

Plugin responses/errors carry `Cache-Control: no-store, private, max-age=0`, `Pragma: no-cache` and `Vary: Authorization, Cookie, X-WP-Nonce`. Disable CDN caching explicitly too.

```json
{"code":"order_access_denied","message":"You cannot access payments for this order.","data":{"status":403}}
```

Core may additionally emit its own route/JSON/schema/auth errors. See error-codes.md. No plugin rate-limit endpoint or 429 emitter is implemented; configure infrastructure limiting for these authenticated operations.

WordPress plain-permalink routing (`index.php?rest_route=/quixdevs-stripe-rest-payments/v1/...`) is supported. Only the exact core rest_route value matching the dispatched route is allowed; other query fields are rejected. Use the admin-displayed route URLs when pretty permalinks are unavailable.
