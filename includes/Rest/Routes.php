<?php
/** Two authenticated existing-order endpoints; no duplicate payment gateway. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Rest;

final class Routes {
	public const NAMESPACE = 'quixdevs-stripe-rest-payments/v1';

	public function __construct( private readonly Payment_Controller $controller, private readonly Request_Validator $validator ) {}

	public function register(): void {
		foreach ( array(
			'prepare' => 'POST',
			'status'  => 'GET',
		) as $action => $method ) {
			register_rest_route(
				self::NAMESPACE,
				'/orders/(?P<order_id>[1-9][0-9]{0,17})/' . $action,
				array(
					'methods'             => $method,
					'callback'            => array( $this->controller, $action ),
					'permission_callback' => array( $this->controller, 'permission' ),
					'args'                => array(
						'order_id' => array(
							'required'          => true,
							'type'              => 'integer',
							'minimum'           => 1,
							'validate_callback' => array( $this->validator, 'order_id' ),
						),
					),
				)
			);
		}
	}
}
