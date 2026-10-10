<?php
use PHPUnit\Framework\TestCase;
use PHPUnit\Framework\Attributes\{RunInSeparateProcess,PreserveGlobalState};
use QuixDevs\StripeRestPayments\Stripe\Gateway_Compatibility;
final class CompatibilityTest extends TestCase {
    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function test_unknown_extension_version_is_disabled(): void {
        define('WC_STRIPE_VERSION','11.0.2');
        self::assertFalse((new Gateway_Compatibility())->supported());
    }
    #[RunInSeparateProcess]
    #[PreserveGlobalState(false)]
    public function test_missing_extension_is_disabled(): void {
        self::assertFalse((new Gateway_Compatibility())->supported());
    }
}
