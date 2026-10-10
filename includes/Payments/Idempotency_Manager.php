<?php
/** Binds the single preparation to its caller and immutable order context. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Payments;

use QuixDevs\StripeRestPayments\Data\Payment_Repository;
use QuixDevs\StripeRestPayments\Support\Failure;

final class Idempotency_Manager {
	public function __construct( private readonly Payment_Repository $repository ) {}

	public function remember( \WC_Order $order, int $user_id, string $key ): bool {
		$expected = array(
			'key_hash'    => hash( 'sha256', $key ),
			'user_id'     => $user_id,
			'fingerprint' => $this->repository->fingerprint( $order ),
		);
		$record   = $order->get_meta( Payment_Repository::ATTEMPT_META, true );
		if ( '' !== $record ) {
			if ( ! is_array( $record ) || $record !== $expected ) {
				// phpcs:ignore WordPress.Security.EscapeOutput.ExceptionNotEscaped -- REST domain messages are JSON encoded, never echoed.
				throw new Failure( 'idempotency_conflict', __( 'A different preparation exists or the order changed. Reconcile it before retrying.', 'quixdevs-stripe-rest-payments' ), 409 );
			}
			return true;
		}
		$this->repository->save( $order, $expected );
		return false;
	}
}
