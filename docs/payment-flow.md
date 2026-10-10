# Payment lifecycle

```mermaid
sequenceDiagram
    participant App
    participant API as QuixDevs API
    participant Browser as Native WooCommerce order-pay
    participant Stripe
    App->>API: Authenticated prepare(order, Idempotency-Key)
    API->>API: Authorize, lock, inspect order/intent, persist preparation
    API-->>App: Native checkout URL or verified pending state
    App->>Browser: Open URL; owner signs in
    Browser->>Stripe: Official gateway collects PaymentMethod and confirms PaymentIntent
    Stripe-->>Browser: Authenticate if needed
    Stripe->>API: Official Stripe webhook updates WooCommerce (not an addon webhook)
    App->>API: Authenticated status
    API->>Stripe: GET stored PaymentIntent
    API-->>App: Verified state and reconciled paid boolean
```

The diagram's webhook recipient is the store running the official extension, not a QuixDevs REST endpoint. The addon registers no webhook and has no finalization endpoint.

| State | Client behavior |
| --- | --- |
| not_started | Open returned native payment URL; verification is false |
| requires_payment_method | Existing method failed or absent; use native store recovery/operator help |
| requires_confirmation | Continue the original native gateway flow |
| requires_action | Finish authentication in the payment browser |
| processing | Wait and refresh status with backoff |
| requires_capture | Merchant capture is pending; never treat as paid |
| succeeded | Display success only when paid is also true |
| canceled | No fresh payment is created automatically; reconcile before retry |

A Stripe success can precede WooCommerce's webhook update. Verification then returns succeeded/paid=false. The application waits; it never sends a success flag to the addon. Refunded/cancelled orders can retain a succeeded intent but are not reported as paid if WooCommerce no longer considers them paid. The status endpoint is not a refund ledger or fulfillment tracker.

The gateway validates and updates its own settlement lifecycle. QuixDevs independently checks intent/order context before reporting status and does not repair a mismatch by changing the order. No processing → completed override exists. Manual capture, issuer challenges and asynchronous settlement are handled by official checkout; actual merchant acceptance is outstanding.
