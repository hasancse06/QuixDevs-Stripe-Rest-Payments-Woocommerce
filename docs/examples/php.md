# PHP backend example

This illustrates the actual WordPress REST contract, not an app login implementation. Your backend must first authenticate its app user, resolve an order it owns, and validate any integration-user assignment. Never accept an arbitrary order ID and forward privileged credentials. Secrets below come from backend environment configuration.

```php
<?php
function storeRequest(string $method, int $authorizedOrderId, string $key = ''): array {
    if ($authorizedOrderId < 1 || !in_array($method, ['POST', 'GET'], true)) {
        throw new InvalidArgumentException('Invalid request');
    }
    $base = 'https://store.example/wp-json/quixdevs-stripe-rest-payments/v1/orders/';
    $path = $method === 'POST' ? '/prepare' : '/status';
    $ch = curl_init($base . $authorizedOrderId . $path);
    $headers = ['Accept: application/json'];
    if ($method === 'POST') {
        if (!preg_match('/^[A-Za-z0-9_-]{16,128}$/D', $key)) {
            throw new InvalidArgumentException('Retain a valid idempotency key');
        }
        $headers[] = 'Content-Type: application/json';
        $headers[] = 'Idempotency-Key: ' . $key;
        curl_setopt($ch, CURLOPT_POSTFIELDS, '{}');
    }
    curl_setopt_array($ch, [
        CURLOPT_CUSTOMREQUEST => $method,
        CURLOPT_USERPWD => getenv('STORE_USER') . ':' . getenv('STORE_APP_PASSWORD'),
        CURLOPT_HTTPAUTH => CURLAUTH_BASIC,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_TIMEOUT => 25,
    ]);
    $raw = curl_exec($ch);
    $http = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    curl_close($ch);
    if ($raw === false) {
        throw new RuntimeException('Uncertain network result; retry the same preparation key or check status');
    }
    $data = json_decode($raw, true, 32, JSON_THROW_ON_ERROR);
    if (!in_array($http, [200, 202], true) || !is_array($data)) {
        throw new RuntimeException('Store rejected payment request');
    }
    return $data; // Send only to the already-authorized app user; set Cache-Control: no-store.
}
```

Persist the per-order preparation key server-side. Never log the returned URL or credentials. Expose no general-purpose WordPress proxy. Poll GET at a bounded rate and display paid status only when paid is true. No Stripe secret or client secret is needed by this backend example.
