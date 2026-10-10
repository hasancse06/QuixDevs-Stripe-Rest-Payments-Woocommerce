# Same-store browser JavaScript

Use this inside an existing authenticated WordPress page. The theme/plugin rendering the page must provide the site's REST root and a current wp_rest nonce using WordPress's script-data APIs. The example does not invent login endpoints or cross-origin cookie support. In external apps, use your existing backend instead.

```js
async function prepareOrder(orderId, stableKey, restNonce) {
  if (!Number.isSafeInteger(orderId) || orderId < 1) throw new Error('Invalid order');
  const response = await fetch(
    `/wp-json/quixdevs-stripe-rest-payments/v1/orders/${orderId}/prepare`,
    {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: {
        'Content-Type': 'application/json',
        'X-WP-Nonce': restNonce,
        'Idempotency-Key': stableKey
      },
      body: '{}'
    }
  );
  const result = await response.json();
  if (!response.ok) throw new Error(result.code || 'payment_request_failed');
  if (result.flow === 'woocommerce_order_pay' && typeof result.checkout_url === 'string') {
    const url = new URL(result.checkout_url);
    if (url.protocol !== 'https:' || url.origin !== location.origin) throw new Error('Unsafe payment URL');
    location.assign(url.href);
  }
  return result; // gateway_pending means continue original payment, then query status.
}

async function readPaymentStatus(orderId, restNonce) {
  const response = await fetch(
    `/wp-json/quixdevs-stripe-rest-payments/v1/orders/${orderId}/status`,
    {credentials: 'same-origin', cache: 'no-store', headers: {'X-WP-Nonce': restNonce}}
  );
  const result = await response.json();
  if (!response.ok) throw new Error(result.code || 'verification_unavailable');
  return result.paid === true;
}
```

Create stableKey once with crypto.randomUUID() and retain it in your authenticated application's order context across retries. Do not regenerate it after timeouts. For WordPress installations in a subdirectory, use the server-supplied rest_url rather than hardcoding /wp-json. Never treat a browser return/redirect or a resolved promise as proof of payment.
