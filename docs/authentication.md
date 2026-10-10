# Authentication and order scope

The addon consumes WordPress's established identity and does not parse global tokens, implement JWT, or change CORS. Authentication and ownership are checked before provider reads or checkout URL disclosure. Guest orders are rejected even for an integration user.

## Authenticated customers

On a same-store WordPress page, use the existing logged-in cookie and a current `wp_rest` nonce in `X-WP-Nonce`. WordPress core validates the nonce before dispatch; without a valid nonce cookie authentication does not authorize these routes. Only that user's orders are allowed. Knowing the order ID/key is insufficient.

A user-specific Application Password may be used by a trusted backend on behalf of that WordPress customer. It has the user's WordPress authority, not a plugin-created isolated payment scope. Prefer a dedicated minimally privileged integration account when your backend manages multiple customers.

## Trusted server integration

Use core WordPress Application Passwords over HTTPS with a dedicated account. Do not use the user's main password. WordPress itself authenticates the request; invalid credentials never establish a caller. WooCommerce consumer keys alone are not advertised as plugin-route authentication.

For an integration user to access another customer's order, both are required:

1. User capability `quixdevs_stripe_rest_payments_prepare_orders`.
2. Order metadata `_quixdevs_stripe_rest_payments_integration_user_id` exactly matching that user ID.

Administrators do not automatically bypass ownership. The addon grants no capabilities during activation. Assign/revoke them through trusted operator/backend code, never through a public endpoint:

```php
$user = get_user_by('id', 456); // Dedicated integration user, resolved by trusted configuration.
$user->add_cap('quixdevs_stripe_rest_payments_prepare_orders');
$order = wc_get_order(123); // Operator must validate this assignment.
$order->update_meta_data('_quixdevs_stripe_rest_payments_integration_user_id', '456');
$order->save();
```

Revoke by removing the capability or deleting the assignment through CRUD. One integration assignment per order is supported. The backend must still authenticate its own app users and map each order to the correct customer; never expose a generic privileged proxy accepting arbitrary order IDs from clients.

## Browser payment login

API authentication does not create a browser session. Application Passwords cannot log the user into the native payment page. The customer must sign in as the order owner in that browser. The addon does not mint login links or bypass WooCommerce order-pay authorization. This extra browser login is an explicit v1 limitation.

## Operational requirements

Keep Application Passwords on the backend, rotate/revoke them, redact Authorization and Cookies from access tracing, preserve core REST nonce enforcement, and do not enable broad credentialed CORS. Configure TLS termination so WordPress correctly sees HTTPS. No forwarded-header trust is added by this plugin. Protect plugin routes and order-pay URLs against caching and analytics capture.

Authoritative reference: [WordPress REST authentication](https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/) and [Application Passwords](https://developer.wordpress.org/advanced-administration/security/application-passwords/).
