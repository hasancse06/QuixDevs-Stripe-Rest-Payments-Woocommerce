# cURL — trusted backend

Use dummy IDs and a real *test-store* user-specific Application Password stored in your shell secret manager. Do not paste credentials into history. Set STORE_USER/STORE_APP_PASSWORD privately. The identity must own order 123 or have both documented integration grants. The native payment browser still requires the owner's login.

```sh
curl --fail-with-body --user "$STORE_USER:$STORE_APP_PASSWORD" \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: demo-preparation-0001' \
  --data '{}' \
  'https://store.example/wp-json/quixdevs-stripe-rest-payments/v1/orders/123/prepare'

curl --fail-with-body --user "$STORE_USER:$STORE_APP_PASSWORD" \
  'https://store.example/wp-json/quixdevs-stripe-rest-payments/v1/orders/123/status'
```

Read the response and open checkout_url only when flow is woocommerce_order_pay. An HTTP 202 result has no fresh URL; continue the original native gateway flow. Retain the key on network retries. Never print/log the URL or Authorization in production. Only paid=true is success. See ../rest-api.md for schemas/errors/backoff.
