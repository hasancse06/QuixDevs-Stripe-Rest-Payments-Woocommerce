<?php
/**
 * Plugin Name: QuixDevs Stripe REST Payments
 * Description: Secure REST API payment integration for WooCommerce stores using the official Stripe Payment Gateway.
 * Version: 1.0.0
  * Author: QuixDevs
 * Author URI: https://quixdevs.com/
 * Requires at least: 6.9
 * Requires PHP: 8.2
 * Requires Plugins: woocommerce, woocommerce-gateway-stripe
 * Text Domain: quixdevs-stripe-rest-payments
 * License: MIT
 * License URI: https://opensource.org/license/mit/
 *
 * @package QuixDevsStripeRestPayments
 */

defined( 'ABSPATH' ) || exit;

require_once __DIR__ . '/includes/Autoload.php';

\QuixDevs\StripeRestPayments\Bootstrap::register( __FILE__ );
