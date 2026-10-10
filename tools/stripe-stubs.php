<?php
// Analysis-only declarations checked against the downloaded 11.0.1 source.
class WC_Stripe_API {
	/** @return array<string, string> */
	public static function get_headers(): array {}
}
class WC_Stripe_Helper {
	public static function get_stripe_amount( $total, $currency = '' ): int|float {}
}
class WC_Stripe_Mode {
	public static function is_test(): bool {}
}
class WC_Stripe_UPE_Payment_Method {
	public function is_enabled(): bool {}
}
class WC_Stripe_UPE_Payment_Gateway extends WC_Payment_Gateway {
	/** @var array<string, WC_Stripe_UPE_Payment_Method> */
	public $payment_methods;
}
