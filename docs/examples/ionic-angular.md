# Ionic Angular / Capacitor — native store payment handoff

This version supports a browser handoff. It does not return a client_secret and cannot drive Stripe Payment Element or a native Stripe SDK directly. Payment details and issuer authentication stay in the official WooCommerce Stripe page; no fabricated Capacitor Stripe plugin is used.

## Application contract

1. Your already-existing app login authenticates the user to your backend. That backend verifies ownership and resolves the specific WooCommerce order.
2. The backend stores a stable preparation key and calls the plugin POST prepare using backend-only WordPress credentials and the documented order scope.
3. It returns the safe plugin result only to that authorized app user, with no-store headers. Do not implement a privileged arbitrary-order proxy.
4. Open checkout_url using official Capacitor Browser. The customer signs in as the order owner in that browser; app authentication and WordPress Application Passwords do not create this browser session.
5. The native WooCommerce page runs the official Stripe client integration, including PaymentMethod/PaymentIntent authentication. The user can close the browser and return to the app manually.
6. Check verified status through the authenticated backend. Display success only when paid=true; closing the browser is not proof of success.

Your application's backend routes are intentionally not named here: they belong to your app and are not provided by this plugin. The TypeScript interface below must be implemented using your existing authenticated backend API. Do not point it at a fabricated QuixDevs login endpoint.

## Capacitor Browser example

The [official Capacitor Browser v8 docs](https://capacitorjs.com/docs/apis/browser) document Browser.open and browserFinished. Install @capacitor/browser matching your application's Capacitor major and run npx cap sync. No native iOS/Android build was executed here; validate your exact app versions before shipping.

```ts
import { Browser } from '@capacitor/browser';

export interface PaymentStatus {
  order_id: number;
  order_status: string;
  payment_state: string;
  payment_verified: boolean;
  paid: boolean;
}
export interface PreparedPayment extends PaymentStatus {
  flow: 'woocommerce_order_pay' | 'gateway_pending';
  checkout_url: string | null;
  reused: boolean;
}
// Implement with your existing authenticated backend; keep WP credentials there.
export interface AuthorizedOrderPayments {
  prepareOwnedOrder(orderId: number): Promise<PreparedPayment>;
  statusOwnedOrder(orderId: number): Promise<PaymentStatus>;
}

export async function openOrderPayment(
  backend: AuthorizedOrderPayments,
  orderId: number,
  onStatus: (status: PaymentStatus) => void
): Promise<() => Promise<void>> {
  const prepared = await backend.prepareOwnedOrder(orderId);
  if (prepared.flow === 'gateway_pending') {
    onStatus(await backend.statusOwnedOrder(orderId));
    return async () => {};
  }
  if (!prepared.checkout_url) throw new Error('Missing payment page');
  const url = new URL(prepared.checkout_url);
  if (url.protocol !== 'https:' || url.origin !== 'https://store.example') {
    throw new Error('Unexpected payment origin');
  }
  // Configure the real trusted store origin in your app; do not log url.href.
  const listener = await Browser.addListener('browserFinished', () => {
    void backend.statusOwnedOrder(orderId).then(onStatus).catch(() => {
      // Present a retry-status action; do not initiate a fresh payment.
    });
  });
  try {
    await Browser.open({ url: url.href });
  } catch (error) {
    await listener.remove();
    throw error;
  }
  return () => listener.remove(); // Call on page/component teardown.
}
```

Angular HttpClient is suitable inside your backend adapter's existing app-authentication layer; [its requests return Observables](https://angular.dev/guide/http/making-requests). Convert/subscribe according to your application's existing conventions and validate response shape at runtime. No app login implementation is supplied or assumed.

Provide an explicit “Check payment status” control on app resume and web/PWA, because browserFinished is a native event and a return from navigation is unreliable. Use bounded polling/backoff and cancel on component teardown. Configure verified app links separately if desired; this plugin does not accept arbitrary return URLs or implement deep-link login/payment callbacks.

HTTP 202 means continue original payment authentication or wait. 409 means reconcile the specific conflict. 422 means use native retry/store help. 503 means verification is uncertain: retain the key, check status later and never create another payment merely because of a timeout.

Acceptance requirements: device browser login, issuer challenge/redirect, app backgrounding, user cancellation, offline return, failed network after payment, delayed webhook, status backoff and duplicate tapping. These flows are documented, not claimed as device-tested. Never embed WordPress admin credentials, unrestricted application passwords, Stripe secret keys or card fields in Ionic/Angular source.
