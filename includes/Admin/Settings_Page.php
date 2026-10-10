<?php
/** Native, read-only diagnostics under WooCommerce administration. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Admin;

use QuixDevs\StripeRestPayments\Dependencies;
use QuixDevs\StripeRestPayments\Rest\Routes;

final class Settings_Page {
	public function __construct( private readonly Dependencies $dependencies ) {}

	public function register(): void {
		add_submenu_page( 'woocommerce', __( 'Stripe REST Payments', 'quixdevs-stripe-rest-payments' ), __( 'Stripe REST Payments', 'quixdevs-stripe-rest-payments' ), 'manage_woocommerce', 'quixdevs-stripe-rest-payments', array( $this, 'render' ) );
	}

	public function notice(): void {
		if ( ! current_user_can( 'manage_options' ) && ! current_user_can( 'manage_woocommerce' ) ) {
			return;
		}
		$issues = $this->dependencies->issues();
		if ( array() !== $issues ) {
			echo '<div class="notice notice-warning"><p><strong>QuixDevs Stripe REST Payments:</strong> ' . esc_html( implode( ' ', $issues ) ) . '</p></div>';
		}
	}

	public function render(): void {
		if ( ! current_user_can( 'manage_woocommerce' ) ) {
			wp_die( esc_html__( 'You cannot access payment diagnostics.', 'quixdevs-stripe-rest-payments' ) );
		}
		$issues = $this->dependencies->issues();
		$rows   = array(
			__( 'Plugin status', 'quixdevs-stripe-rest-payments' ) => array() === $issues ? __( 'Available — development build; merchant acceptance required', 'quixdevs-stripe-rest-payments' ) : implode( ' ', $issues ),
			'WooCommerce'                                 => defined( 'WC_VERSION' ) ? WC_VERSION : __( 'Missing', 'quixdevs-stripe-rest-payments' ),
			__( 'Stripe extension', 'quixdevs-stripe-rest-payments' ) => defined( 'WC_STRIPE_VERSION' ) ? WC_STRIPE_VERSION : __( 'Missing', 'quixdevs-stripe-rest-payments' ),
			__( 'Mode', 'quixdevs-stripe-rest-payments' ) => is_callable( array( 'WC_Stripe_Mode', 'is_test' ) ) ? ( \WC_Stripe_Mode::is_test() ? 'Test' : 'Live' ) : __( 'Unknown', 'quixdevs-stripe-rest-payments' ),
			__( 'API endpoints', 'quixdevs-stripe-rest-payments' ) => array() === $issues ? rest_url( Routes::NAMESPACE . '/orders/{order_id}/prepare' ) . ' (POST), ' . rest_url( Routes::NAMESPACE . '/orders/{order_id}/status' ) . ' (GET)' : __( 'Not registered until dependencies are ready.', 'quixdevs-stripe-rest-payments' ),
		);
		$last   = get_option( 'quixdevs_stripe_rest_payments_last_diagnostic', array() );
		$rows[ __( 'Last safe diagnostic', 'quixdevs-stripe-rest-payments' ) ] = is_array( $last ) && isset( $last['category'], $last['time'] ) ? $last['category'] . ' — ' . $last['time'] : __( 'No diagnostic recorded.', 'quixdevs-stripe-rest-payments' );
		echo '<div class="wrap"><h1>QuixDevs Stripe REST Payments</h1><p>' . esc_html__( 'Connect Apps. Process Payments. Powered by Stripe.', 'quixdevs-stripe-rest-payments' ) . '</p><table class="widefat striped"><tbody>';
		foreach ( $rows as $label => $value ) {
			echo '<tr><th scope="row">' . esc_html( $label ) . '</th><td>' . esc_html( (string) $value ) . '</td></tr>';
		}
		echo '</tbody></table><h2>' . esc_html__( 'Authentication and payment flow', 'quixdevs-stripe-rest-payments' ) . '</h2><p>' . esc_html__( 'Use customer cookies with a REST nonce, or WordPress Application Passwords from a trusted server. Integration users need an explicit per-order assignment and capability. Customers sign in again in the payment browser. Guest API access is unsupported. Configure Stripe only in WooCommerce payment settings.', 'quixdevs-stripe-rest-payments' ) . '</p><p><a href="https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/">' . esc_html__( 'WordPress authentication documentation', 'quixdevs-stripe-rest-payments' ) . '</a> · <a href="https://developer.woocommerce.com/docs/apis/store-api/resources-endpoints/checkout-order/">' . esc_html__( 'WooCommerce order checkout documentation', 'quixdevs-stripe-rest-payments' ) . '</a></p></div>';
	}
}
