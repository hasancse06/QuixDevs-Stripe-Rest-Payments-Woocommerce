<?php
/** Atomic database-backed preparation mutex; never expires during a worker. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Payments;

use QuixDevs\StripeRestPayments\Support\Failure;

final class Payment_Lock {
	public const PREFIX = 'quixdevs_stripe_rest_payments_lock_';

	public function acquire( int $order_id ): string {
		global $wpdb;
		$token = wp_generate_uuid4();
		$name  = self::PREFIX . $order_id;
		// add_option() uses an upsert in WordPress 6.9 and can replace a concurrent owner.
		// phpcs:ignore WordPress.DB.DirectDatabaseQuery.DirectQuery -- INSERT IGNORE elects one owner without any update on a unique-key conflict.
		$result = $wpdb->query( $wpdb->prepare( "INSERT IGNORE INTO {$wpdb->options} (option_name, option_value, autoload) VALUES (%s, %s, 'off')", $name, $token ) );
		if ( false === $result ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'lock_unavailable', __( 'Preparation locking is temporarily unavailable.', 'quixdevs-stripe-rest-payments' ), 503 );
		}
		if ( 1 !== $result ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'payment_in_progress', __( 'Preparation is locked. Retry later; contact the store if the lock persists.', 'quixdevs-stripe-rest-payments' ), 409 );
		}
		wp_cache_delete( $name, 'options' );
		wp_cache_delete( 'notoptions', 'options' );
		return $token;
	}

	public function release( int $order_id, string $token ): void {
		global $wpdb;
		$name = self::PREFIX . $order_id;
		// Compare-and-delete prevents a former worker from releasing another worker's lock.
		// phpcs:ignore WordPress.DB.DirectDatabaseQuery.DirectQuery -- Atomic compare-and-delete on options; delete_option has no ownership condition.
		$wpdb->query( $wpdb->prepare( "DELETE FROM {$wpdb->options} WHERE option_name = %s AND option_value = %s", $name, $token ) );
		wp_cache_delete( $name, 'options' );
	}
}
