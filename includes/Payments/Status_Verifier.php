<?php
/** Validates provider identity and totals; never settles or mutates an order. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Payments;

use QuixDevs\StripeRestPayments\Stripe\Stripe_Adapter_Interface;
use QuixDevs\StripeRestPayments\Support\Failure;

final class Status_Verifier {
	public function __construct( private readonly Stripe_Adapter_Interface $adapter ) {}

	public function verify( \WC_Order $order ): Payment_Result {
		$id          = $order->get_meta( '_stripe_intent_id', true );
		$transaction = $order->get_transaction_id();
		if ( '' === $id ) {
			if ( $order->is_paid() || '' !== $transaction ) {
				// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
				throw new Failure( 'invalid_payment_reference', __( 'The order requires payment reconciliation.', 'quixdevs-stripe-rest-payments' ), 409 );
			}
			return new Payment_Result( Payment_State::NOT_STARTED, false, false );
		}
		if ( ! is_string( $id ) ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'invalid_payment_reference', __( 'The stored payment reference is invalid.', 'quixdevs-stripe-rest-payments' ), 409 );
		}
		$data  = $this->adapter->intent( $id );
		$state = isset( $data['status'] ) && is_string( $data['status'] ) ? Payment_State::tryFrom( $data['status'] ) : null;
		if ( null === $state || Payment_State::NOT_STARTED === $state || ! isset( $data['amount'], $data['livemode'] ) || ! is_int( $data['amount'] ) || ! is_bool( $data['livemode'] ) ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'invalid_provider_response', __( 'Payment verification returned an invalid response.', 'quixdevs-stripe-rest-payments' ), 502 );
		}
		if ( ( $data['id'] ?? null ) !== $id || 'payment_intent' !== ( $data['object'] ?? null )
			|| $this->adapter->amount( $order ) !== $data['amount'] || strtolower( $order->get_currency() ) !== ( $data['currency'] ?? null )
			|| $this->adapter->test_mode() === $data['livemode'] || ! is_array( $data['metadata'] ?? null )
			|| ( $data['metadata']['order_id'] ?? null ) !== (string) $order->get_order_number()
			|| ( $data['metadata']['order_key'] ?? null ) !== $order->get_order_key()
			|| ( $data['metadata']['site_url'] ?? null ) !== esc_url( get_site_url() ) ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'payment_context_mismatch', __( 'Payment details do not match this order. Contact the store.', 'quixdevs-stripe-rest-payments' ), 409 );
		}
		$charge = $data['latest_charge'] ?? null;
		if ( '' !== $transaction && $transaction !== $id && $transaction !== $charge ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'payment_context_mismatch', __( 'The transaction requires reconciliation.', 'quixdevs-stripe-rest-payments' ), 409 );
		}
		$settled = Payment_State::SUCCEEDED === $state;
		if ( $settled && ( ! is_string( $charge ) || ! preg_match( '/^ch_[A-Za-z0-9]+$/D', $charge ) || ( $data['amount_received'] ?? null ) !== $data['amount'] ) ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'payment_context_mismatch', __( 'Settlement details require reconciliation.', 'quixdevs-stripe-rest-payments' ), 409 );
		}
		return new Payment_Result( $state, true, $settled && $order->is_paid() && '' !== $transaction );
	}
}
