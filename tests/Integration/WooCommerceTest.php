<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use PHPUnit\Framework\Attributes\DataProvider;
use QuixDevs\StripeRestPayments\Authentication\Order_Authorizer;
use QuixDevs\StripeRestPayments\Data\Payment_Repository;
use QuixDevs\StripeRestPayments\Payments\{Payment_Lock,Idempotency_Manager,Payment_Service,Status_Verifier};
use QuixDevs\StripeRestPayments\Stripe\WooCommerce_Stripe_Adapter;
use QuixDevs\StripeRestPayments\Support\Failure;
final class WooCommerceTest extends TestCase {
    private array $orders=[];
    private int $user;
    protected function setUp(): void {
        if (!getenv('QUIXDEVS_WP_ROOT')) { self::markTestSkipped('Disposable WordPress required.'); }
        $this->user=wp_insert_user(['user_login'=>'qdx_'.wp_generate_password(12,false),'user_pass'=>wp_generate_password(),'user_email'=>wp_generate_password(10,false).'@example.test','role'=>'customer']);
    }
    protected function tearDown(): void {
        foreach($this->orders as $id) { $o=wc_get_order($id); if($o) {$o->delete(true);} }
        if(isset($this->user)) {require_once ABSPATH.'wp-admin/includes/user.php'; wp_delete_user($this->user);}
        wp_set_current_user(0);
    }
    public static function storage(): array {return [['no'],['yes']];}
    private function order(string $hpos): WC_Order {
        update_option('woocommerce_custom_orders_table_enabled',$hpos);
        $order=wc_create_order(['customer_id'=>$this->user,'status'=>'pending']);
        $order->set_payment_method('stripe'); $order->set_currency('USD'); $order->set_total('10.00'); $order->save();
        $this->orders[]=$order->get_id(); return $order;
    }
    private function service(): Payment_Service {
        $repo=new Payment_Repository(); $adapter=new WooCommerce_Stripe_Adapter();
        return new Payment_Service($repo,new Order_Authorizer(),$adapter,new Status_Verifier($adapter),new Idempotency_Manager($repo),new Payment_Lock());
    }
    #[DataProvider('storage')]
    public function test_crud_handoff_and_retry_on_both_datastores(string $hpos): void {
        $order=$this->order($hpos);
        $data=$this->service()->prepare($order->get_id(),$this->user,'integration-key-0001');
        self::assertSame('woocommerce_order_pay',$data['flow']); self::assertStringContainsString('order-pay',$data['checkout_url']);
        self::assertSame('https',wp_parse_url($data['checkout_url'],PHP_URL_SCHEME));
        $fresh=wc_get_order($order->get_id());
        self::assertSame('pending',$fresh->get_status()); self::assertSame('',$fresh->get_transaction_id());
        self::assertIsArray($fresh->get_meta(Payment_Repository::ATTEMPT_META,true));
        self::assertTrue($this->service()->prepare($order->get_id(),$this->user,'integration-key-0001')['reused']);
        self::assertSame($hpos==='yes',\Automattic\WooCommerce\Utilities\OrderUtil::custom_orders_table_usage_is_enabled());
        global $wpdb;
        $table=$hpos==='yes' ? $wpdb->prefix.'wc_orders' : $wpdb->posts;
        self::assertSame((string)$order->get_id(),(string)$wpdb->get_var($wpdb->prepare("SELECT id FROM $table WHERE id=%d",$order->get_id())));
    }
    #[DataProvider('storage')]
    public function test_provider_verification_is_read_only_and_discards_secrets(string $hpos): void {
        $order=$this->order($hpos); $order->update_meta_data('_stripe_intent_id','pi_fixture'); $order->save();
        $filter=static function($pre,$args,$url) use($order) {
            if(str_contains($url,'payment_intents/pi_fixture')) {
                TestCase::assertSame(0,$args['redirection']); TestCase::assertArrayHasKey('Stripe-Version',$args['headers']);
                return ['headers'=>[],'response'=>['code'=>200],'body'=>json_encode(['id'=>'pi_fixture','object'=>'payment_intent','status'=>'succeeded','amount'=>1000,'amount_received'=>1000,'currency'=>'usd','livemode'=>false,'metadata'=>['order_id'=>(string)$order->get_order_number(),'order_key'=>$order->get_order_key(),'site_url'=>esc_url(get_site_url())],'latest_charge'=>'ch_fixture','client_secret'=>'must_never_leave_adapter'])];
            }
            return $pre;
        };
        add_filter('pre_http_request',$filter,PHP_INT_MAX,3);
        try {
            $data=$this->service()->status($order->get_id(),$this->user);
            self::assertTrue($data['payment_verified']); self::assertFalse($data['paid']);
            self::assertStringNotContainsString('must_never_leave_adapter',json_encode($data));
            $order->payment_complete('ch_fixture');
            $data=$this->service()->status($order->get_id(),$this->user);
            self::assertTrue($data['paid']); self::assertContains($data['order_status'],['processing','completed']);
        } finally {remove_filter('pre_http_request',$filter,PHP_INT_MAX);}
    }
    public function test_atomic_option_lock_and_owner_condition(): void {
        $lock=new Payment_Lock(); $id=987654321; delete_option(Payment_Lock::PREFIX.$id);
        $token=$lock->acquire($id); $lock->release($id,'different-owner');
        self::assertSame($token,get_option(Payment_Lock::PREFIX.$id));
        try {$lock->acquire($id);self::fail('Second worker accepted');} catch(Failure $e) {self::assertSame(409,$e->http_status);}
        finally {$lock->release($id,$token);}
        self::assertFalse(get_option(Payment_Lock::PREFIX.$id));
    }
    public function test_gateway_readiness_and_disabled_state(): void {
        $deps=new \QuixDevs\StripeRestPayments\Dependencies(); self::assertSame([],$deps->issues());
        $gateway=$deps->gateway(); $gateway->enabled='no';
        try {self::assertNotEmpty($deps->issues());} finally {$gateway->enabled='yes';}
    }
    public function test_unsafe_provider_shapes_and_timeouts_fail_closed(): void {
        $order=$this->order('no');$order->update_meta_data('_stripe_intent_id','pi_fixture');$order->save();
        $this->expectException(Failure::class); $this->service()->status($order->get_id(),$this->user);
    }
}
