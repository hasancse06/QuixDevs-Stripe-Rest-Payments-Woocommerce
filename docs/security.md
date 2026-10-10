# Security review and deployment controls

Implemented: authenticated permission callbacks, strict customer ownership, explicit per-order server scope plus dedicated capability, guest rejection, HTTPS requirements, secure same-store URL check, fixed provider GET endpoint without redirects, small strict request contract, atomic preparation serialization, safe error conversion, minimal provider field projection, and no-store success/error responses.

No merchant key settings, card endpoints, raw request forwarding, client-secret output, global WooCommerce function overrides, POST simulation, custom JWT, payment settlement mutations, new checkout gateway or duplicate webhook exist.

Provider verification matches stored intent ID/object, official amount conversion, order currency, mode, gateway order number/key/site metadata, received amount, latest charge and stored transaction. Order context is rechecked after a status read. Unknown provider state, changed context and timeouts fail closed. This does not repair tampered administrator data or replace the official gateway's webhook verification.

Logging accepts only fixed error categories and integer order ID. Arbitrary errors, headers, provider bodies, client secrets, payment URLs and customer details are never sent to the addon logger. The last diagnostic contains only category and UTC time. Routine successes/authentication failures are not logged to avoid noise or enumeration data retention. The adapter avoids the extension's full-response retrieval logger.

Before deployment: require TLS end-to-end or correctly configured trusted TLS termination; exclude routes and order-pay pages from CDN/browser caches and URL analytics; redact Cookie/Authorization/X-WP-Nonce and payment URLs in proxies, APM and error monitoring; disable debug plugins that capture Stripe response bodies; rate-limit per identity and at the edge; protect and rotate backend credentials; authorize app-to-order mapping on the backend; never put admin credentials in JavaScript; review other payment plugins and filtered metadata.

The order-pay URL contains an order key and is confidential. It is disclosed only after authorization and must not be shared, logged, placed in analytics or treated as a login link. Native WooCommerce still authorizes the payment browser. No broad CORS headers are installed.

Release risks: no real Stripe test-mode authentication/capture/webhook exercise, no full classic/Blocks browser regression, no persistent external object-cache test, and no independent penetration assessment. These remain documented acceptance gates. Never test with production keys or charge a live card.
