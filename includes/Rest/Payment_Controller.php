<?php
/** Thin HTTP boundary; all payment decisions belong to the service. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Rest;

use QuixDevs\StripeRestPayments\Authentication\Request_Authenticator;
use QuixDevs\StripeRestPayments\Dependencies;
use QuixDevs\StripeRestPayments\Payments\Payment_Service;
use QuixDevs\StripeRestPayments\Support\Failure;

final class Payment_Controller {
	public function __construct(
		private readonly Payment_Service $service,
		private readonly Request_Authenticator $authenticator,
		private readonly Request_Validator $validator,
		private readonly Response_Factory $responses,
		private readonly Dependencies $dependencies
	) {}

	public function permission( \WP_REST_Request $request ): bool|\WP_Error {
		try {
			$user_id = $this->authenticator->user_id();
			$this->validator->validate( $request, 'POST' === $request->get_method() );
			$this->service->authorized_order( (int) $request->get_url_params()['order_id'], $user_id );
			if ( array() !== $this->dependencies->issues() ) {
				// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
				throw new Failure( 'stripe_unavailable', __( 'The configured payment integration is unavailable.', 'quixdevs-stripe-rest-payments' ), 503 );
			}
			return true;
		} catch ( \Throwable $error ) {
			return $this->responses->error( $error, 0 );
		}
	}

	public function prepare( \WP_REST_Request $request ): \WP_REST_Response|\WP_Error {
		$id = (int) $request->get_url_params()['order_id'];
		try {
			$key = $this->validator->validate( $request, true );
			return $this->responses->success( $this->service->prepare( $id, $this->authenticator->user_id(), $key ) );
		} catch ( \Throwable $error ) {
			return $this->responses->error( $error, $id );
		}
	}

	public function status( \WP_REST_Request $request ): \WP_REST_Response|\WP_Error {
		$id = (int) $request->get_url_params()['order_id'];
		try {
			$this->validator->validate( $request, false );
			return $this->responses->success( $this->service->status( $id, $this->authenticator->user_id() ) );
		} catch ( \Throwable $error ) {
			return $this->responses->error( $error, $id );
		}
	}
}
