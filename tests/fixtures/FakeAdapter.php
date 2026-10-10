<?php
namespace QuixDevs\StripeRestPayments\Tests;
use QuixDevs\StripeRestPayments\Stripe\Stripe_Adapter_Interface;
final class FakeAdapter implements Stripe_Adapter_Interface {
    public array $response = [];
    public int $reads = 0;
    public ?\Throwable $failure = null;
    public function intent(string $id): array { ++$this->reads; if ($this->failure) { throw $this->failure; } return $this->response; }
    public function amount(\WC_Order $order): int { return (int)round((float)$order->get_total() * 100); }
    public function test_mode(): bool { return true; }
    public function checkout_url(\WC_Order $order): string { return 'https://example.test/checkout/order-pay/' . $order->get_id(); }
}
