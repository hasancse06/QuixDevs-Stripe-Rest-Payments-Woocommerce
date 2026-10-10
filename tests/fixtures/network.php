<?php
/** Install only into the disposable test site's mu-plugins directory. */
add_filter('pre_http_request', static function ($pre, $args, $url) {
    return new WP_Error('quixdevs_test_network_blocked', 'Tests never call external services.');
}, PHP_INT_MAX, 3);
