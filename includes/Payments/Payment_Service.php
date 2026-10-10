<?php
/** Orchestrates authorization, preparation serialization and read-only status. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Payments;

use QuixDevs\StripeRestPayments\Authentication\Order_Authorizer;
use QuixDevs\StripeRestPayments\Data\Payment_Repository;
use QuixDevs\StripeRestPayments\Stripe\Stripe_Adapter_Interface;
use QuixDevs\StripeRestPayments\Support\Failure;

final class Payment_Service {
	public function __construct(
		private readonly Payment_Repository $repository,
		private readonly Order_Authorizer $authorizer,
		private readonly Stripe_Adapter_Interface $adapter,
		private readonly Status_Verifier $verifier,
		private readonly Idempotency_Manager $idempotency,
		private readonly Payment_Lock $lock
	) {}

	public function authorized_order( int $id, int $user_id ): \WC_Order {
		$order = $this->repository->order( $id );
		$this->authorizer->check( $order, $user_id );
		if ( 'stripe' !== $order->get_payment_method() ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'unsupported_payment_method', __( 'Only orders assigned to the official Stripe card gateway are supported.', 'quixdevs-stripe-rest-payments' ), 409 );
		}
		return $order;
	}

	/**
	 * Return the safe public representation.
	 *
	 * @return array<string, mixed>
	 * @throws Failure If preparation or verification is unsafe.
	 */
	public function prepare( int $id, int $user_id, string $key ): array {
		$this->authorized_order( $id, $user_id );
		$token = $this->lock->acquire( $id );
		try {
			// Re-read after obtaining the persistent mutex, then authorize again.
			$order = $this->authorized_order( $id, $user_id );
			if ( $order->is_paid() ) {
				// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
				throw new Failure( 'payment_already_completed', __( 'This order is already paid.', 'quixdevs-stripe-rest-payments' ), 409 );
			}
			if ( ! $order->has_status( array( 'pending', 'failed' ) ) || ! $order->needs_payment() || (float) $order->get_total() <= 0 ) {
				// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
				throw new Failure( 'order_not_payable', __( 'This order cannot be paid.', 'quixdevs-stripe-rest-payments' ), 409 );
			}
			$result = $this->verifier->verify( $order );
			if ( in_array( $result->state, array( Payment_State::CANCELED, Payment_State::REQUIRES_PAYMENT_METHOD ), true ) ) {
				// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
				throw new Failure( 'payment_failed', __( 'The existing attempt requires reconciliation or a retry through native checkout.', 'quixdevs-stripe-rest-payments' ), 422 );
			}
			$reused  = $this->idempotency->remember( $order, $user_id, $key );
			$pending = Payment_State::NOT_STARTED !== $result->state;
			return $result->data( $order ) + array(
				'flow'         => $pending ? 'gateway_pending' : 'woocommerce_order_pay',
				'checkout_url' => $pending ? null : $this->adapter->checkout_url( $order ),
				'reused'       => $reused || $pending,
			);
		} finally {
			$this->lock->release( $id, $token );
		}
	}

	/**
	 * Return the safe public representation.
	 *
	 * @return array<string, mixed>
	 * @throws Failure If preparation or verification is unsafe.
	 */
	public function status( int $id, int $user_id ): array {
		$order       = $this->authorized_order( $id, $user_id );
		$fingerprint = $this->repository->fingerprint( $order );
		$result      = $this->verifier->verify( $order );
		$fresh       = $this->authorized_order( $id, $user_id );
		if ( $fingerprint !== $this->repository->fingerprint( $fresh ) || $order->get_meta( '_stripe_intent_id', true ) !== $fresh->get_meta( '_stripe_intent_id', true ) || $order->get_status() !== $fresh->get_status() || $order->get_transaction_id() !== $fresh->get_transaction_id() ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'order_changed', __( 'The order changed during verification. Retry the status request.', 'quixdevs-stripe-rest-payments' ), 409 );
		}
		return $result->data( $fresh );
	}
}
