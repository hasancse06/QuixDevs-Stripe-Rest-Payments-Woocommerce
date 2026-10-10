<?php
/** Safe domain error, independent of REST response rendering. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Support;

final class Failure extends \RuntimeException {
	public function __construct( public readonly string $error_code, string $message, public readonly int $http_status ) {
		parent::__construct( $message );
	}
}
