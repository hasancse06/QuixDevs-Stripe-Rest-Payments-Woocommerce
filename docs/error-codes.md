# Error codes

Plugin errors use WP_Error's REST schema: code/string, message/string, data.status/integer. Messages are translated safe descriptions; raw exceptions and provider bodies are withheld.

| Code | HTTP | Meaning / response |
| --- | --- | --- |
| https_required | 403 | WordPress did not see TLS; correct proxy/store configuration |
| authentication_required | 401 | Establish a valid core WordPress identity |
| invalid_order_id | 400 | Invalid positive route identifier |
| payload_too_large | 413 | Body exceeds 2048 bytes |
| unexpected_fields | 400 | Body/query/form/files outside the empty contract |
| invalid_idempotency_key | 400 | Missing/malformed required POST header |
| order_not_found | 404 | No order with that ID |
| order_access_denied | 403 | Wrong customer, missing server grants, guest or unsupported order type |
| unsupported_payment_method | 409 | Order is not assigned to primary stripe gateway |
| payment_already_completed | 409 | Already-paid order cannot be prepared |
| order_not_payable | 409 | Unsupported status, nonpositive total or not needing payment |
| lock_unavailable | 503 | Persistent mutex insertion failed; no preparation occurs |
| payment_in_progress | 409 | Preparation mutex is held; retry/reconcile |
| idempotency_conflict | 409 | Key/caller/context differs from persisted preparation |
| invalid_payment_reference | 409 | Missing/invalid/ambiguous stored intent/transaction |
| payment_context_mismatch | 409 | Provider identity, order metadata, mode, amount, currency or transaction mismatch |
| order_changed | 409 | Order/intent/transaction changed during status verification |
| payment_failed | 422 | Existing intent canceled or requires a new payment method; native recovery |
| stripe_unavailable | 503 | Dependency or inspected integration contract unavailable |
| checkout_unavailable | 503 | Native payment URL is not secure/same-store |
| provider_unavailable | 503 | Provider timeout/non-200/error; do not start another payment |
| invalid_provider_response | 502 | Malformed/unknown provider state/shape |
| internal_error | 503 | Unexpected server failure, safely redacted |

Existing requires_action/processing/requires_confirmation/requires_capture/succeeded-but-unpaid preparations return HTTP 202 with safe state, not an error. GET status returns HTTP 200 for known verified states. There is no plugin 429/rate limiter; infrastructure may produce 429 with its own retry policy.

WordPress additionally emits rest_no_route (404), rest_invalid_param/rest_invalid_json (400), rest_cookie_invalid_nonce (403), and core authentication errors. Malformed route IDs may fail route matching before the plugin validator runs. Dependency failure at initialization means routes are not registered, so requests return the core missing-route response; configuration changes after initialization yield stripe_unavailable.
