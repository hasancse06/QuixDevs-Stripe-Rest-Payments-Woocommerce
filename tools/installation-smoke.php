<?php
/** WP-CLI-only package smoke check; never included in the installation ZIP. */
if ( ! defined( 'WP_CLI' ) || ! WP_CLI || DB_NAME !== 'quixdevs_test' || ! str_contains( DB_HOST, 'quixdevs' ) || getenv( 'QUIXDEVS_DISPOSABLE_TESTS' ) !== '1' ) {
    throw new RuntimeException( 'Only an explicitly disposable WordPress fixture is allowed.' );
}
$_SERVER['HTTPS'] = 'on';
$assert = static function ( bool $condition, string $message ): void {
    if ( ! $condition ) { throw new RuntimeException( $message ); }
};
$plugin = WP_PLUGIN_DIR . '/quixdevs-stripe-rest-payments';
$assert( is_dir( $plugin ) && ! is_link( $plugin ), 'Install an extracted ZIP, not a source symlink.' );
$assert( ! is_dir( $plugin . '/vendor' ) && ! is_dir( $plugin . '/tests' ) && ! is_dir( $plugin . '/docs' ), 'Development files leaked into runtime.' );
$reflection = new ReflectionClass( \QuixDevs\StripeRestPayments\Bootstrap::class );
$assert( realpath( $reflection->getFileName() ) === realpath( $plugin . '/includes/Bootstrap.php' ), 'Class loaded outside installed package.' );
$deps = new \QuixDevs\StripeRestPayments\Dependencies();
$routes = array_filter( array_keys( rest_get_server()->get_routes() ), static fn( $route ) => str_starts_with( $route, '/quixdevs-stripe-rest-payments/v1/orders/' ) );
if ( getenv( 'QUIXDEVS_EXPECT_MISSING_DEPENDENCY' ) === '1' ) {
    $assert( count( $routes ) === 0 && $deps->issues() !== array(), 'Missing dependency must disable routes safely.' );
    WP_CLI::success( 'Missing dependency: no payment routes, actionable diagnostics, no fatal.' );
    return;
}
$assert( $deps->issues() === array() && count( $routes ) === 2, 'Installed package readiness/routes failed.' );
$admin = get_user_by( 'login', 'quixdevs_test_admin' );
$assert( $admin instanceof WP_User, 'Disposable administrator not found.' );
wp_set_current_user( $admin->ID );
ob_start();
( new \QuixDevs\StripeRestPayments\Admin\Settings_Page( $deps ) )->render();
$html = ob_get_clean();
$assert( str_contains( $html, 'QuixDevs Stripe REST Payments' ) && str_contains( $html, 'development build' ) && str_contains( $html, 'API endpoints' ), 'Admin diagnostics did not render.' );
$user = wp_insert_user( array( 'user_login' => 'distribution_' . wp_generate_password( 12, false ), 'user_pass' => wp_generate_password(), 'role' => 'customer' ) );
$assert( is_int( $user ), 'Could not create disposable customer.' );
$order = null;
try {
    $order = wc_create_order( array( 'customer_id' => $user, 'status' => 'pending' ) );
    $order->set_payment_method( 'stripe' );
    $order->set_currency( 'USD' );
    $order->set_total( '10.00' );
    $order->save();
    $request = new WP_REST_Request( 'POST', '/quixdevs-stripe-rest-payments/v1/orders/' . $order->get_id() . '/prepare' );
    $request->set_header( 'Idempotency-Key', '0000000000000001' );
    $request->set_header( 'Content-Type', 'application/json' );
    $request->set_body( '{}' );
    wp_set_current_user( 0 );
    $assert( rest_do_request( $request )->get_status() === 401, 'Anonymous access was accepted.' );
    wp_set_current_user( $user );
    $response = rest_do_request( $request );
    $assert( $response->get_status() === 200 && $response->get_data()['flow'] === 'woocommerce_order_pay', 'Owned-order handoff failed.' );
    $assert( rest_do_request( $request )->get_data()['reused'] === true, 'Idempotency retry failed.' );
    $status = rest_do_request( new WP_REST_Request( 'GET', '/quixdevs-stripe-rest-payments/v1/orders/' . $order->get_id() . '/status' ) );
    $assert( $status->get_status() === 200 && $status->get_data()['paid'] === false, 'Unpaid status projection failed.' );
    $assert( wc_get_order( $order->get_id() )->get_status() === 'pending', 'Smoke check changed settlement status.' );
} finally {
    if ( $order instanceof WC_Order ) { $order->delete( true ); }
    require_once ABSPATH . 'wp-admin/includes/user.php';
    wp_delete_user( $user );
    wp_set_current_user( 0 );
}
WP_CLI::success( 'ZIP activation, package autoloading, two routes, admin diagnostics, anonymous denial, owned handoff, idempotent retry and unpaid status passed. No provider payment calls.' );
