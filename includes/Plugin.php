<?php
/** Composition root with explicit, small dependencies. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments;

use QuixDevs\StripeRestPayments\Admin\Settings_Page;
use QuixDevs\StripeRestPayments\Authentication\Order_Authorizer;
use QuixDevs\StripeRestPayments\Authentication\Request_Authenticator;
use QuixDevs\StripeRestPayments\Data\Payment_Repository;
use QuixDevs\StripeRestPayments\Payments\Idempotency_Manager;
use QuixDevs\StripeRestPayments\Payments\Payment_Lock;
use QuixDevs\StripeRestPayments\Payments\Payment_Service;
use QuixDevs\StripeRestPayments\Payments\Status_Verifier;
use QuixDevs\StripeRestPayments\Rest\Payment_Controller;
use QuixDevs\StripeRestPayments\Rest\Request_Validator;
use QuixDevs\StripeRestPayments\Rest\Response_Factory;
use QuixDevs\StripeRestPayments\Rest\Routes;
use QuixDevs\StripeRestPayments\Stripe\WooCommerce_Stripe_Adapter;
use QuixDevs\StripeRestPayments\Support\Logger;

final class Plugin {
	private static bool $registered = false;

	public function register(): void {
		if ( self::$registered ) {
			return;
		}
		self::$registered = true;
		$dependencies     = new Dependencies();
		$admin            = new Settings_Page( $dependencies );
		add_action( 'admin_menu', array( $admin, 'register' ) );
		add_action( 'admin_notices', array( $admin, 'notice' ) );
		$responses = new Response_Factory( new Logger() );
		add_filter( 'rest_post_dispatch', array( $responses, 'no_cache' ), 10, 3 );
		add_action( 'rest_api_init', fn() => $this->register_routes( $dependencies, $responses ) );
	}

	private function register_routes( Dependencies $dependencies, Response_Factory $responses ): void {
		if ( array() !== $dependencies->issues() ) {
			return;
		}
		$repository = new Payment_Repository();
		$adapter    = new WooCommerce_Stripe_Adapter();
		$service    = new Payment_Service( $repository, new Order_Authorizer(), $adapter, new Status_Verifier( $adapter ), new Idempotency_Manager( $repository ), new Payment_Lock() );
		$validator  = new Request_Validator();
		$controller = new Payment_Controller( $service, new Request_Authenticator(), $validator, $responses, $dependencies );
		$routes     = new Routes( $controller, $validator );
		$routes->register();
	}
}
