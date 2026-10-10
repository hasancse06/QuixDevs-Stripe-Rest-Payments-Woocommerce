<?php
/** Reuses native checkout, merchant headers and currency conversion. No charges. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Stripe;

use QuixDevs\StripeRestPayments\Support\Failure;

final class WooCommerce_Stripe_Adapter implements Stripe_Adapter_Interface {
	public function checkout_url( \WC_Order $order ): string {
		$url = $order->get_checkout_payment_url();
		if ( 'https' !== wp_parse_url( $url, PHP_URL_SCHEME ) || wp_parse_url( home_url(), PHP_URL_HOST ) !== wp_parse_url( $url, PHP_URL_HOST ) || ( wp_parse_url( home_url(), PHP_URL_PORT ) ?? 443 ) !== ( wp_parse_url( $url, PHP_URL_PORT ) ?? 443 ) ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'checkout_unavailable', __( 'A secure same-store payment page is required.', 'quixdevs-stripe-rest-payments' ), 503 );
		}
		return $url;
	}

	public function intent( string $id ): array {
		if ( ! ( new Gateway_Compatibility() )->supported() ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'stripe_unavailable', __( 'The Stripe integration is unavailable.', 'quixdevs-stripe-rest-payments' ), 503 );
		}
		if ( ! preg_match( '/^pi_[A-Za-z0-9]{1,128}$/D', $id ) ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'invalid_payment_reference', __( 'The stored payment reference is invalid.', 'quixdevs-stripe-rest-payments' ), 409 );
		}
		// retrieve() logs full Stripe responses in 11.0.1. Reuse its headers instead.
		$response = wp_remote_get(
			'https://api.stripe.com/v1/payment_intents/' . $id,
			array(
				'headers'             => \WC_Stripe_API::get_headers(),
				'timeout'             => 15,
				'redirection'         => 0,
				'limit_response_size' => 65536,
			)
		);
		if ( is_wp_error( $response ) || 200 !== wp_remote_retrieve_response_code( $response ) ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'provider_unavailable', __( 'Payment verification is temporarily unavailable. Do not start another payment.', 'quixdevs-stripe-rest-payments' ), 503 );
		}
		$data = json_decode( wp_remote_retrieve_body( $response ), true );
		if ( ! is_array( $data ) || isset( $data['error'] ) ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'invalid_provider_response', __( 'Payment verification returned an invalid response.', 'quixdevs-stripe-rest-payments' ), 502 );
		}
		return array_intersect_key( $data, array_flip( array( 'id', 'object', 'status', 'amount', 'amount_received', 'currency', 'livemode', 'metadata', 'latest_charge' ) ) );
	}

	public function amount( \WC_Order $order ): int {
		return (int) \WC_Stripe_Helper::get_stripe_amount( $order->get_total(), $order->get_currency() );
	}

	public function test_mode(): bool {
		return \WC_Stripe_Mode::is_test();
	}
}
