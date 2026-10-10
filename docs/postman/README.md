# Postman collection

Import quixdevs-stripe-rest-payments.postman_collection.json. It contains only implemented prepare/status requests.

Set base_url to your HTTPS staging store (including a WordPress subdirectory if needed), order_id to an owned test order, authentication to the complete Authorization value generated privately from a WordPress user and Application Password (e.g. Basic followed by encoded credentials), and idempotency_key to a stable 16–128 character key. The authentication variable is blank in source; mark it sensitive and never export populated values.

Run prepare, open checkout_url in a separate browser as the customer, then run status. Do not log or export payment URLs. A passing collection schema test does not imply a completed payment; only paid=true is the success condition. The bundled tests accept documented errors to support negative testing; inspect the HTTP status/code for the intended scenario. See ../rest-api.md for authorization and recovery.
