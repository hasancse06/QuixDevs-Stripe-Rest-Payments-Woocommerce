<?php
/** Order persistence exclusively through WooCommerce CRUD. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Data;

use QuixDevs\StripeRestPayments\Support\Failure;

final class Payment_Repository {
	public const ATTEMPT_META = '_quixdevs_stripe_rest_payments_preparation';

	public function order( int $id ): \WC_Order {
		$order = wc_get_order( $id );
		if ( ! $order instanceof \WC_Order ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'order_not_found', __( 'Order not found.', 'quixdevs-stripe-rest-payments' ), 404 );
		}
		return $order;
	}

	public function fingerprint( \WC_Order $order ): string {
		return hash( 'sha256', (string) wp_json_encode( array( $order->get_customer_id(), $order->get_total(), $order->get_currency(), $order->get_payment_method(), $order->get_order_key() ) ) );
	}

	/**
	 * Persist a credential-free preparation record.
	 *
	 * @param array<string, mixed> $record Preparation record without credentials.
	 */
	public function save( \WC_Order $order, array $record ): void {
		$order->update_meta_data( self::ATTEMPT_META, $record );
		$order->save_meta_data();
	}
}
