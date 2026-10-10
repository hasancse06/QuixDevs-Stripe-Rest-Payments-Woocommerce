<?php
/** Uses WordPress core authentication; does not interpret credentials itself. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Authentication;

use QuixDevs\StripeRestPayments\Support\Failure;

final class Request_Authenticator {
	public function user_id(): int {
		if ( ! is_ssl() ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'https_required', __( 'HTTPS is required.', 'quixdevs-stripe-rest-payments' ), 403 );
		}
		$id = get_current_user_id();
		if ( $id < 1 ) {
			// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
			throw new Failure( 'authentication_required', __( 'Authenticate with WordPress before accessing payments.', 'quixdevs-stripe-rest-payments' ), 401 );
		}
		return $id;
	}
}
