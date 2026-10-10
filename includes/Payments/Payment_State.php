<?php
/** Stripe lifecycle states; WooCommerce fulfillment remains independent. */
declare(strict_types=1);

namespace QuixDevs\StripeRestPayments\Payments;

enum Payment_State: string {
	case NOT_STARTED             = 'not_started';
	case REQUIRES_PAYMENT_METHOD = 'requires_payment_method';
	case REQUIRES_CONFIRMATION   = 'requires_confirmation';
	case REQUIRES_ACTION         = 'requires_action';
	case PROCESSING              = 'processing';
	case REQUIRES_CAPTURE        = 'requires_capture';
	case SUCCEEDED               = 'succeeded';
	case CANCELED                = 'canceled';
}
