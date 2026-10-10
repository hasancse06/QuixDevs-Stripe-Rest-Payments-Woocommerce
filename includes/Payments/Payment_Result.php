<?php
/** Immutable, deliberately small client-facing payment result. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Payments;

final class Payment_Result {
	public function __construct( public readonly Payment_State $state, public readonly bool $verified, public readonly bool $paid ) {}

	/**
	 * Return the safe public representation.
	 *
	 * @return array<string, mixed>
	 */
	public function data( \WC_Order $order ): array {
		return array(
			'order_id'         => $order->get_id(),
			'order_status'     => $order->get_status(),
			'payment_state'    => $this->state->value,
			'payment_verified' => $this->verified,
			'paid'             => $this->paid,
		);
	}
}
