<?php
/** Allowlist-based redaction: arbitrary strings and payloads cannot be logged. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Support;

final class Logger {
	public function failure( string $category, int $order_id ): void {
		$allowed = array( 'provider_unavailable', 'invalid_provider_response', 'payment_context_mismatch', 'internal_error', 'invalid_payment_reference' );
		if ( ! in_array( $category, $allowed, true ) || ! function_exists( 'wc_get_logger' ) ) {
			return;
		}
		wc_get_logger()->warning(
			$category,
			array(
				'source'   => 'quixdevs-stripe-rest-payments',
				'order_id' => $order_id,
			)
		);
		update_option(
			'quixdevs_stripe_rest_payments_last_diagnostic',
			array(
				'category' => $category,
				'time'     => gmdate( 'c' ),
			),
			false
		);
	}
}
