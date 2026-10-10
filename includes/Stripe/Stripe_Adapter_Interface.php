<?php
/** Narrow boundary: hosted checkout handoff and read-only provider verification. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Stripe;

interface Stripe_Adapter_Interface {
	public function checkout_url( \WC_Order $order ): string;

	/**
	 * Retrieve only fields needed for verification.
	 *
	 * @return array<string, mixed> Only verification fields, never client secrets.
	 */
	public function intent( string $id ): array;

	public function amount( \WC_Order $order ): int;

	public function test_mode(): bool;
}
