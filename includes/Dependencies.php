<?php
/** Runtime readiness checks, without copying merchant credentials. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments;

use QuixDevs\StripeRestPayments\Stripe\Gateway_Compatibility;

final class Dependencies {
	/**
	 * Collect actionable dependency problems.
	 *
	 * @return list<string>
	 */
	public function issues(): array {
		global $wp_version;
		$issues = array();
		if ( version_compare( PHP_VERSION, '8.2', '<' ) || version_compare( (string) $wp_version, '6.9', '<' ) ) {
			$issues[] = __( 'PHP 8.2 and WordPress 6.9 or newer are required.', 'quixdevs-stripe-rest-payments' );
		}
		if ( ! defined( 'WC_VERSION' ) || version_compare( WC_VERSION, '10.9', '<' ) || ! function_exists( 'WC' ) ) {
			$issues[] = __( 'WooCommerce 10.9 or newer must be active.', 'quixdevs-stripe-rest-payments' );
			return $issues;
		}
		if ( ! ( new Gateway_Compatibility() )->supported() ) {
			$issues[] = __( 'The inspected WooCommerce Stripe Gateway version 11.0.1 is required. Other versions are disabled pending contract verification.', 'quixdevs-stripe-rest-payments' );
			return $issues;
		}
		$gateway = $this->gateway();
		if ( ! $gateway instanceof \WC_Stripe_UPE_Payment_Gateway ) {
			$issues[] = __( 'The official Stripe UPE card gateway must be initialized.', 'quixdevs-stripe-rest-payments' );
			return $issues;
		}
		if ( 'yes' !== $gateway->enabled ) {
			$issues[] = __( 'Enable the official Stripe gateway in WooCommerce payment settings.', 'quixdevs-stripe-rest-payments' );
		}
		$prefix = \WC_Stripe_Mode::is_test() ? 'test_' : '';
		if ( ! $gateway->get_option( $prefix . 'publishable_key' ) || ! $gateway->get_option( $prefix . 'secret_key' ) ) {
			$issues[] = __( 'Configure merchant credentials for the active mode in the official Stripe gateway.', 'quixdevs-stripe-rest-payments' );
		}
		if ( ! isset( $gateway->payment_methods['card'] ) || ! $gateway->payment_methods['card']->is_enabled() ) {
			$issues[] = __( 'Enable the card payment method in the official Stripe gateway.', 'quixdevs-stripe-rest-payments' );
		}
		if ( 'https' !== wp_parse_url( home_url(), PHP_URL_SCHEME ) || 'https' !== wp_parse_url( wc_get_checkout_url(), PHP_URL_SCHEME ) ) {
			$issues[] = __( 'The store and checkout URLs must use HTTPS.', 'quixdevs-stripe-rest-payments' );
		}
		return $issues;
	}

	public function gateway(): ?\WC_Payment_Gateway {
		if ( ! function_exists( 'WC' ) || ! WC()->payment_gateways() ) {
			return null;
		}
		$gateways = WC()->payment_gateways()->payment_gateways();
		return $gateways['stripe'] ?? null;
	}
}
