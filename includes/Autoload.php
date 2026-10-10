<?php
/** Production autoloader; Composer is only required for development. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments;

defined( 'ABSPATH' ) || exit;

spl_autoload_register(
	static function ( string $class_name ): void {
		$prefix = __NAMESPACE__ . '\\';
		if ( str_starts_with( $class_name, $prefix ) ) {
			$relative = substr( $class_name, strlen( $prefix ) );
			if ( preg_match( '/^[A-Za-z_][A-Za-z0-9_\\\\]*$/D', $relative ) ) {
				$file = __DIR__ . '/' . str_replace( '\\', '/', $relative ) . '.php';
				if ( is_file( $file ) ) {
					require_once $file;
				}
			}
		}
	}
);
