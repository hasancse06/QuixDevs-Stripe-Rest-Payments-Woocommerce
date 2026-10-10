<?php
/** Registers the plugin once, after WooCommerce and Stripe have initialized. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments;

final class Bootstrap {
	private static bool $registered = false;

	public static function register( string $file ): void {
		if ( self::$registered ) {
			return;
		}
		self::$registered = true;
		add_action(
			'before_woocommerce_init',
			static function () use ( $file ): void {
				if ( class_exists( '\\Automattic\\WooCommerce\\Utilities\\FeaturesUtil' ) ) {
					\Automattic\WooCommerce\Utilities\FeaturesUtil::declare_compatibility( 'custom_order_tables', $file, true );
				}
			}
		);
		add_action( 'init', static fn() => ( new Plugin() )->register(), 30 );
		register_activation_hook( $file, array( self::class, 'activate' ) );
		register_deactivation_hook( $file, array( self::class, 'deactivate' ) );
	}

	public static function activate(): void {
		// No credentials, roles, order mutations, schedules, or rewrites are created.
		update_option( 'quixdevs_stripe_rest_payments_version', '1.0.0', false );
	}

	public static function deactivate(): void {
		// Persistent preparation records survive deactivation to preserve retry safety.
		delete_option( 'quixdevs_stripe_rest_payments_version' );
	}
}
