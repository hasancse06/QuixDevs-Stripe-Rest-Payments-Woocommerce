<?php
/** Strict contract: no payment data, arbitrary amounts or nested forwarding. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Rest;

use QuixDevs\StripeRestPayments\Support\Failure;

final class Request_Validator {
	public function order_id( mixed $value ): bool {
		return ( is_int( $value ) && $value > 0 ) || ( is_string( $value ) && preg_match( '/^[1-9][0-9]{0,17}$/D', $value ) && (float) $value <= PHP_INT_MAX );
	}

	public function validate( \WP_REST_Request $request, bool $prepare ): string {
		if ( ! $this->order_id( $request->get_url_params()['order_id'] ?? null ) ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'invalid_order_id', __( 'A positive integer order ID is required.', 'quixdevs-stripe-rest-payments' ), 400 );
		}
		$body = $request->get_body() ?? '';
		if ( strlen( $body ) > 2048 ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'payload_too_large', __( 'The request body is too large.', 'quixdevs-stripe-rest-payments' ), 413 );
		}
		$query = $request->get_query_params();
		if ( isset( $query['rest_route'] ) && $request->get_route() === $query['rest_route'] ) {
			unset( $query['rest_route'] );
		}
		if ( array() !== $query || array() !== $request->get_body_params() || array() !== $request->get_file_params() ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'unexpected_fields', __( 'Query fields, form fields and file uploads are not supported.', 'quixdevs-stripe-rest-payments' ), 400 );
		}
		$decoded = '' !== $body ? json_decode( $body ) : null;
		if ( '' !== $body && ( ! $prepare || ! $request->is_json_content_type() || ! is_object( $decoded ) || array() !== get_object_vars( $decoded ) ) ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'unexpected_fields', __( 'Preparation accepts only an empty JSON object; status has no body.', 'quixdevs-stripe-rest-payments' ), 400 );
		}
		$key = $request->get_header( 'idempotency-key' ) ?? '';
		if ( $prepare && ! preg_match( '/^[A-Za-z0-9_-]{16,128}$/D', $key ) ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'invalid_idempotency_key', __( 'Idempotency-Key must contain 16–128 letters, digits, underscores or hyphens.', 'quixdevs-stripe-rest-payments' ), 400 );
		}
		return $key;
	}
}
