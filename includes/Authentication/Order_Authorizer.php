<?php
/** Ownership and explicitly assigned server integration scope. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Authentication;

use QuixDevs\StripeRestPayments\Support\Failure;

final class Order_Authorizer {
	public const CAPABILITY = 'quixdevs_stripe_rest_payments_prepare_orders';
	public const SCOPE_META = '_quixdevs_stripe_rest_payments_integration_user_id';

	public function check( \WC_Order $order, int $user_id ): void {
		if ( 'shop_order' !== $order->get_type() || $order->get_customer_id() < 1 ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'order_access_denied', __( 'This order is outside the supported payment scope.', 'quixdevs-stripe-rest-payments' ), 403 );
		}
		if ( $order->get_customer_id() === $user_id ) {
			return;
		}
		if ( user_can( $user_id, self::CAPABILITY ) && (string) $user_id === (string) $order->get_meta( self::SCOPE_META, true ) ) {
			return;
		}
		// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
		throw new Failure( 'order_access_denied', __( 'You cannot access payments for this order.', 'quixdevs-stripe-rest-payments' ), 403 );
	}
}
