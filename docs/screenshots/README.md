# Genuine screenshot provenance

Screenshots are captured from the actual addon running in disposable local WordPress 6.9 with WooCommerce 10.9.0 and official Stripe 11.0.1. The fixture uses dummy credentials and blocks outbound provider HTTP. They demonstrate UI/diagnostics, not a connected merchant account or accepted payment.

The capture harness grants a test administrator session only in the loopback temporary server. It is outside the repository/package. Any dependency-disabled screenshot uses a request-local disabled gateway fixture, not a fabricated interface. No customer orders or credentials are shown.

Files: 01-stripe-rest-settings.png, 02-dependency-status.png, 03-api-endpoints.png, 04-payment-diagnostics.png. Supplemental screenshots may show the same real native screen at a different scroll position. See [the implementation report](../implementation-report.md) for completed capture status.

Capture completed through native Google Chrome on the local test server. Raw captures are retained in the separate working project and excluded from this clean GitHub folder. The numbered screenshots are crops that remove browser chrome/unused whitespace or highlight rows; no labels, warnings, statuses or interface elements are fabricated or retouched. Stripe's own unreachable/Apple Pay warnings are expected because the fixture blocks outbound requests. The last diagnostic reflects an earlier negative test; it does not show a merchant payment.
