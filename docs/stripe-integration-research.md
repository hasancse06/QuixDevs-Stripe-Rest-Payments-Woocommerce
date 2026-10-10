# Stripe integration research and architecture decision

Research performed 2026-10-10. No merchant installation of WooCommerce/Stripe was present in the supplied repository. The official 11.0.1 distribution was downloaded, inspected, then installed in a disposable WordPress environment. This is an inspected/test fixture version, not a claim about the user's live store.

The [official release](https://github.com/woocommerce/woocommerce-gateway-stripe/releases/tag/11.0.1) is dated October 5, 2026. Its main file declares WordPress minimum 6.9 and WooCommerce header minimum 10.9 (the internal current minimum constant still says 10.8); this addon deliberately requires 10.9. Its API version constant is `2026-03-25.dahlia`. We inherit that header and do not select a competing Stripe API version.

## Store API investigation

WooCommerce has a public [existing-order checkout endpoint](https://developer.woocommerce.com/docs/apis/store-api/resources-endpoints/checkout-order/), POST `/wc/store/v1/checkout/{ORDER_ID}`, with order verification and checkout context requirements. Cart checkout is a [separate flow](https://developer.woocommerce.com/docs/apis/store-api/resources-endpoints/checkout/). Neither is replaced by this addon.

The checkout-order documentation still illustrates legacy `stripe_source` data. That example is insufficient evidence for a current headless UPE contract. Inspected Stripe blocks support uses `woocommerce_rest_checkout_process_payment_with_context`, enriches payment results with intent details and an official verification URL, and coordinates with its own client scripts. No documented independent existing-order prepare/confirm interface for arbitrary external clients was established. Therefore v1 uses WooCommerce's supported browser order-pay surface. Direct Store API payment orchestration is not implemented or advertised.

## Interfaces used

| Interface | Role | Stability / guard |
| --- | --- | --- |
| WordPress register_rest_route, permission_callback, WP_Error, WP_REST_Response, core auth | HTTP/auth boundary | Public APIs; WordPress 6.9 minimum |
| WC_Order CRUD and get_checkout_payment_url | Existing-order native handoff | Public WooCommerce interface; minimum 10.9 |
| WC_Payment_Gateway enabled/get_option and initialized gateway registry | Readiness | Public gateway surface |
| WC_Stripe_UPE_Payment_Gateway.payment_methods and card.is_enabled | Verify official card configuration | Extension internal; exact 11.0.1 guard |
| WC_Stripe_API::get_headers | Existing merchant auth and Stripe API version | Extension internal; exact 11.0.1 guard |
| WC_Stripe_Helper::get_stripe_amount | Match gateway currency conversion | Extension internal; exact 11.0.1 guard |
| WC_Stripe_Mode::is_test | Match current provider mode | Extension internal; exact 11.0.1 guard |
| `_stripe_intent_id`, order intent metadata and transaction conventions | Associate and verify existing payment | Extension internals; exact 11.0.1 guard |
| WordPress HTTP GET of Stripe PaymentIntent | Read-only verification | Fixed Stripe endpoint, no user-controlled URL or redirects |

Inspected source: [main plugin](https://github.com/woocommerce/woocommerce-gateway-stripe/blob/11.0.1/woocommerce-gateway-stripe.php), [API helper](https://github.com/woocommerce/woocommerce-gateway-stripe/blob/11.0.1/includes/class-wc-stripe-api.php), [Blocks integration](https://github.com/woocommerce/woocommerce-gateway-stripe/blob/11.0.1/includes/class-wc-stripe-blocks-support.php), [UPE gateway](https://github.com/woocommerce/woocommerce-gateway-stripe/blob/11.0.1/includes/payment-methods/class-wc-stripe-upe-payment-gateway.php), [order helper](https://github.com/woocommerce/woocommerce-gateway-stripe/blob/11.0.1/includes/class-wc-stripe-order-helper.php), and [abstract gateway metadata](https://github.com/woocommerce/woocommerce-gateway-stripe/blob/11.0.1/includes/abstracts/abstract-wc-stripe-payment-gateway.php).

`WC_Stripe_API::retrieve()` logs entire provider responses in this version. The addon avoids that method and makes only a read-only GET using the extension's headers. Responses are projected immediately to verification fields. Other plugins/HTTP debuggers can still observe transport data; deployment logging controls remain necessary.

## Stripe model

[PaymentIntents](https://docs.stripe.com/payments/payment-intents) track a payment across authentication and settlement. [PaymentMethods](https://docs.stripe.com/api/payment_methods) represent collected payment details. The official gateway's checkout collects/creates these; QuixDevs does not accept raw cards, create Sources or independently confirm intents. The [intent object](https://docs.stripe.com/api/payment_intents/object) supplies the verified state and amount fields.

The addon validates the persisted intent ID, object, amount, currency, livemode, order number, order key, site URL and settlement reference. The gateway's `metadata.order_id` is the WooCommerce order number, which may differ from the database ID. Customized/removed metadata or currency conversion plugins can fail this strict verification and require a new inspected adapter.

## Compatibility limits

Exact Stripe 11.0.1; primary `stripe` card gateway and ordinary customer-owned shop_order only. Other Stripe versions, subscriptions/renewals, split gateways, guest API payments, custom intent metadata and native/embedded client confirmation are unsupported. Native checkout/webhook acceptance with actual test credentials is still required. The addon has no webhook and never settles orders.

HPOS is declared after real CRUD and verification tests passed both storage modes; see [WooCommerce's guidance](https://developer.woocommerce.com/docs/features/orders/high-performance-order-storage/recipe-book/). No Blocks compatibility declaration is made because payment-browser acceptance was not performed. Tests preserve the gateway registry and do not install a second gateway or Blocks registration.
