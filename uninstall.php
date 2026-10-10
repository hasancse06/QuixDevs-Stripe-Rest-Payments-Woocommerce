<?php
/** Retains financial preparation records and mutexes for explicit reconciliation. */
defined( 'WP_UNINSTALL_PLUGIN' ) || exit;

delete_option( 'quixdevs_stripe_rest_payments_version' );
delete_option( 'quixdevs_stripe_rest_payments_last_diagnostic' );
// Never delete Stripe data, WooCommerce orders, or outstanding processing locks.
