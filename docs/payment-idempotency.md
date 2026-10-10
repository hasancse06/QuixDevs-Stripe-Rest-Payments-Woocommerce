# Preparation idempotency, concurrency and recovery

This plugin serializes **preparation**, not native checkout settlement. Preparation never issues Stripe mutations, so repeated REST requests cannot create duplicate intents/charges through this addon. Concurrent payments performed in normal checkout remain the official gateway's responsibility; the addon does not acquire, override or delete `_stripe_lock_payment` or other official locks.

The per-order mutex is a non-autoloaded WordPress option `quixdevs_stripe_rest_payments_lock_{order_id}`. A prepared INSERT IGNORE against the options table's unique option_name elects one owner atomically across PHP workers; it never updates a conflicting row. WordPress 6.9 add_option() uses ON DUPLICATE KEY UPDATE, so it is deliberately not used for mutex acquisition. A repeated four-worker test exposed that upsert race during development, and acquisition was corrected. The random owner token is required by a prepared, conditional SQL DELETE on the options table. Cache invalidation follows release. Order data itself uses WooCommerce CRUD exclusively.

Locks have no automatic expiry. Expiring a lock while an old worker is alive would admit another owner. A crashed/killed worker leaves the mutex held and later callers receive 409 payment_in_progress. Deactivation/uninstall preserve outstanding locks and preparation records. No stale-lock scheduled deletion is installed.

Under the mutex, the addon reloads and reauthorizes the order. Existing Stripe intent state is verified before issuing a new handoff. Unknown or uncertain provider state fails closed. A preparation record contains only SHA-256(key), caller user ID and SHA-256(order owner/total/currency/payment method/order key). It is saved via update_meta_data/save_meta_data, never postmeta SQL. A retry with the same record returns the current safe result. A different key/caller or changed order context returns 409. Responses and native payment URLs are not cached in the record.

The same idempotency key is scoped to one order preparation; it is not a Stripe idempotency key. Native gateway Stripe operations keep their own idempotency behavior. A key cannot be rotated through this public API, and old records are not silently pruned. Existing declined/canceled attempts require native recovery rather than automatic fresh preparation.

## Operator recovery

1. Stop or prove termination of all workers for that order; pause relevant clients.
2. Inspect the official gateway order notes, Stripe Dashboard in the correct mode, persisted intent/transaction, amount and currency. A timeout is not proof of no payment.
3. Allow official webhooks/native verification to reconcile. Do not mark the order paid using an app claim.
4. Only after reconciliation, use trusted operator code to delete the addon mutex option. Never clear the gateway's locks.
5. If a fresh preparation is explicitly appropriate, remove only `_quixdevs_stripe_rest_payments_preparation` through WC_Order CRUD and generate a new key. Do not delete `_stripe_intent_id` or payment transactions to force a retry.

No public unlock endpoint exists. GET status is independent of the preparation mutex and remains available for authorized reconciliation. The guarantee does not serialize edits made by unrelated plugins or administrators; read verification detects changed payment context and fails closed. Database transactions, persistent object cache variants, checkout/browser duplicate clicks and process crashes during real payments require merchant acceptance beyond the local mutex test.
