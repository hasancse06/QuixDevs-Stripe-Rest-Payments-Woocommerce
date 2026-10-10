<?php
/** Explicit guard around the inspected extension's internal read interfaces. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Stripe;

final class Gateway_Compatibility {
	public const VERSION = '11.0.1';

	public function supported(): bool {
		return defined( 'WC_STRIPE_VERSION' ) && self::VERSION === WC_STRIPE_VERSION
			&& is_callable( array( 'WC_Stripe_API', 'get_headers' ) )
			&& is_callable( array( 'WC_Stripe_Helper', 'get_stripe_amount' ) )
			&& is_callable( array( 'WC_Stripe_Mode', 'is_test' ) );
	}
}
