<?php
/** Safe response conversion and cache prevention for the complete namespace. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Rest;

use QuixDevs\StripeRestPayments\Support\Failure;
use QuixDevs\StripeRestPayments\Support\Logger;

final class Response_Factory {
	public function __construct( private readonly Logger $logger ) {}

	/**
	 * Encode a successful payment response.
	 *
	 * @param array<string, mixed> $data Safe result.
	 */
	public function success( array $data ): \WP_REST_Response {
		$pending = isset( $data['flow'] ) && 'gateway_pending' === $data['flow'];
		return new \WP_REST_Response( $data, $pending ? 202 : 200 );
	}

	public function error( \Throwable $error, int $order_id ): \WP_Error {
		if ( $error instanceof Failure ) {
			$this->logger->failure( $error->error_code, $order_id );
			return new \WP_Error( $error->error_code, $error->getMessage(), array( 'status' => $error->http_status ) );
		}
		$this->logger->failure( 'internal_error', $order_id );
		return new \WP_Error( 'internal_error', __( 'Payment services are temporarily unavailable.', 'quixdevs-stripe-rest-payments' ), array( 'status' => 503 ) );
	}

	public function no_cache( mixed $response, \WP_REST_Server $server, \WP_REST_Request $request ): mixed {
		if ( str_starts_with( $request->get_route(), '/' . Routes::NAMESPACE . '/' ) && $response instanceof \WP_REST_Response ) {
			$response->header( 'Cache-Control', 'no-store, private, max-age=0' );
			$response->header( 'Pragma', 'no-cache' );
			$response->header( 'Vary', 'Authorization, Cookie, X-WP-Nonce' );
		}
		return $response;
	}
}
