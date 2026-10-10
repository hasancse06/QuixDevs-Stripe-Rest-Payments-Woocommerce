<?php
/** Tests use either small doubles or an explicitly provisioned disposable WordPress. */
declare(strict_types=1);
require_once dirname(__DIR__) . '/vendor/autoload.php';
$root = getenv('QUIXDEVS_WP_ROOT');
if ($root) {
    if (getenv('QUIXDEVS_DISPOSABLE_TESTS') !== '1') {
        throw new RuntimeException('Explicit disposable test environment acknowledgement required.');
    }
    $_SERVER['HTTPS'] = 'on';
    $_SERVER['HTTP_HOST'] = 'quixdevs.test';
    $_SERVER['REMOTE_ADDR'] = '127.0.0.1';
    require rtrim($root, '/') . '/wp-load.php';
    if (DB_NAME !== 'quixdevs_test' || !str_contains(DB_HOST, 'quixdevs')) {
        throw new RuntimeException('Refusing to run destructive tests against an unrecognized database.');
    }
} else {
    require __DIR__ . '/fixtures/doubles.php';
}
