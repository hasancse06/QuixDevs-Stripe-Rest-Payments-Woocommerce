<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use PHPUnit\Framework\Attributes\DataProvider;
use QuixDevs\StripeRestPayments\Authentication\{Order_Authorizer,Request_Authenticator};
use QuixDevs\StripeRestPayments\Data\Payment_Repository;
use QuixDevs\StripeRestPayments\Payments\{Status_Verifier,Payment_State,Idempotency_Manager,Payment_Lock,Payment_Service};
use QuixDevs\StripeRestPayments\Rest\Request_Validator;
use QuixDevs\StripeRestPayments\Support\Failure;
use QuixDevs\StripeRestPayments\Tests\FakeAdapter;
require_once dirname(__DIR__) . '/fixtures/FakeAdapter.php';
final class PaymentTest extends TestCase {
    private WC_Order $order;
    private FakeAdapter $adapter;
    protected function setUp(): void {
        $GLOBALS['test_options'] = $GLOBALS['test_caps'] = [];
        $GLOBALS['test_user'] = 10; $GLOBALS['test_ssl'] = true;
        $this->order = new WC_Order();
        $this->order->meta['_stripe_intent_id'] = 'pi_dummy';
        $this->adapter = new FakeAdapter();
        $this->adapter->response = ['id'=>'pi_dummy','object'=>'payment_intent','status'=>'requires_action','amount'=>1000,'amount_received'=>0,'currency'=>'usd','livemode'=>false,'metadata'=>['order_id'=>'1','order_key'=>'wc_order_dummy','site_url'=>'https://example.test'],'latest_charge'=>null];
        $GLOBALS['test_orders'] = [1=>clone $this->order];
    }
    private function service(): Payment_Service {
        $repo = new Payment_Repository();
        return new Payment_Service($repo,new Order_Authorizer(),$this->adapter,new Status_Verifier($this->adapter),new Idempotency_Manager($repo),new Payment_Lock());
    }
    public static function states(): array {
        return array_map(fn($v)=>[$v], ['requires_payment_method','requires_confirmation','requires_action','processing','requires_capture','succeeded','canceled']);
    }
    #[DataProvider('states')]
    public function test_maps_provider_states_without_fulfilling_order(string $state): void {
        $this->adapter->response['status'] = $state;
        if ($state === 'succeeded') { $this->adapter->response['latest_charge']='ch_dummy'; $this->adapter->response['amount_received']=1000; }
        $result = (new Status_Verifier($this->adapter))->verify($this->order);
        self::assertSame($state,$result->state->value);
        self::assertTrue($result->verified); self::assertFalse($result->paid);
        self::assertSame('pending',$this->order->status);
    }
    public static function invalid_provider_fields(): array {
        return [ ['id','pi_other'],['object','setup_intent'],['amount',999],['amount','1000'],['currency','eur'],['livemode',true],['metadata',['order_id'=>'2']],['metadata',[]],['status','invented'],['status',[]],['latest_charge',[]] ];
    }
    #[DataProvider('invalid_provider_fields')]
    public function test_rejects_invalid_provider_context(string $field,mixed $value): void {
        $this->adapter->response['status']='succeeded'; $this->adapter->response['amount_received']=1000; $this->adapter->response['latest_charge']='ch_dummy';
        $this->adapter->response[$field]=$value;
        $this->expectException(Failure::class); (new Status_Verifier($this->adapter))->verify($this->order);
    }
    public function test_success_needs_matching_transaction_and_paid_order(): void {
        $this->adapter->response['status']='succeeded'; $this->adapter->response['latest_charge']='ch_dummy'; $this->adapter->response['amount_received']=1000;
        $this->order->status='processing'; $this->order->transaction='ch_dummy';
        self::assertTrue((new Status_Verifier($this->adapter))->verify($this->order)->paid);
        self::assertSame('processing',$this->order->status);
    }
    public function test_transaction_mismatch_is_rejected(): void {
        $this->order->transaction='ch_other';
        $this->expectException(Failure::class); (new Status_Verifier($this->adapter))->verify($this->order);
    }
    public function test_no_reference_never_claims_verification(): void {
        $this->order->meta=[]; $result=(new Status_Verifier($this->adapter))->verify($this->order);
        self::assertFalse($result->verified); self::assertSame(Payment_State::NOT_STARTED,$result->state); self::assertSame(0,$this->adapter->reads);
    }
    public function test_paid_order_without_intent_is_ambiguous(): void {
        $this->order->meta=[]; $this->order->status='completed';
        $this->expectException(Failure::class); (new Status_Verifier($this->adapter))->verify($this->order);
    }
    public function test_other_customer_is_denied_before_provider_read(): void {
        try { $this->service()->status(1,20); self::fail('Access granted'); }
        catch(Failure $e) { self::assertSame('order_access_denied',$e->error_code); self::assertSame(0,$this->adapter->reads); }
    }
    public function test_scoped_server_requires_both_grants(): void {
        $auth=new Order_Authorizer(); $this->order->meta[Order_Authorizer::SCOPE_META]='20';
        try { $auth->check($this->order,20); self::fail('Missing capability accepted'); } catch(Failure $e) { self::assertSame(403,$e->http_status); }
        $GLOBALS['test_caps'][20][Order_Authorizer::CAPABILITY]=true;
        $auth->check($this->order,20); self::assertTrue(true);
    }
    public function test_guest_order_is_denied_even_to_scoped_integration(): void {
        $this->order->owner=0; $this->expectException(Failure::class); (new Order_Authorizer())->check($this->order,10);
    }
    public function test_authentication_and_https_are_required(): void {
        $GLOBALS['test_user']=0;
        try {(new Request_Authenticator())->user_id(); self::fail('Anonymous accepted');} catch(Failure $e) {self::assertSame(401,$e->http_status);}
        $GLOBALS['test_user']=10; $GLOBALS['test_ssl']=false;
        $this->expectException(Failure::class); (new Request_Authenticator())->user_id();
    }
    public function test_repeated_preparation_reuses_record_without_provider_creation(): void {
        $GLOBALS['test_orders'][1]->meta=[];
        $first=$this->service()->prepare(1,10,'dummy-idempotency-0001');
        $second=$this->service()->prepare(1,10,'dummy-idempotency-0001');
        self::assertFalse($first['reused']); self::assertTrue($second['reused']); self::assertSame($first['checkout_url'],$second['checkout_url']); self::assertSame(0,$this->adapter->reads);
        self::assertStringNotContainsString('dummy-idempotency-0001',json_encode($GLOBALS['test_orders'][1]->meta));
    }
    public function test_conflicting_key_and_changed_total_are_rejected(): void {
        $GLOBALS['test_orders'][1]->meta=[];
        $this->service()->prepare(1,10,'dummy-idempotency-0001');
        try {$this->service()->prepare(1,10,'dummy-idempotency-0002'); self::fail('Conflict accepted');} catch(Failure $e) {self::assertSame('idempotency_conflict',$e->error_code);}
        $GLOBALS['test_orders'][1]->total='20.00';
        $this->expectException(Failure::class); $this->service()->prepare(1,10,'dummy-idempotency-0001');
    }
    public function test_existing_action_does_not_issue_new_checkout_link(): void {
        $result=$this->service()->prepare(1,10,'dummy-idempotency-0001');
        self::assertSame('gateway_pending',$result['flow']); self::assertNull($result['checkout_url']); self::assertSame(1,$this->adapter->reads);
    }
    public function test_timeout_fails_closed_and_releases_mutex(): void {
        $this->adapter->failure=new Failure('provider_unavailable','Safe timeout',503);
        try {$this->service()->prepare(1,10,'dummy-idempotency-0001'); self::fail('Timeout accepted');} catch(Failure $e) {self::assertSame(503,$e->http_status);}
        self::assertSame([],$GLOBALS['test_options']);
        self::assertSame('',$GLOBALS['test_orders'][1]->get_meta(Payment_Repository::ATTEMPT_META));
    }
    public static function ineligible(): array {return [['completed'],['processing'],['cancelled'],['refunded'],['on-hold']];}
    #[DataProvider('ineligible')]
    public function test_ineligible_orders_cannot_be_prepared(string $state): void {
        $GLOBALS['test_orders'][1]->status=$state; $this->expectException(Failure::class); $this->service()->prepare(1,10,'dummy-idempotency-0001');
    }
    public function test_wrong_gateway_is_denied(): void {
        $GLOBALS['test_orders'][1]->method='cod'; $this->expectException(Failure::class); $this->service()->prepare(1,10,'dummy-idempotency-0001');
    }
    public function test_persistent_lock_rejects_second_owner_and_wrong_release(): void {
        $lock=new Payment_Lock(); $token=$lock->acquire(1); $lock->release(1,'wrong-token');
        try {$lock->acquire(1); self::fail('Concurrent owner accepted');} catch(Failure $e) {self::assertSame('payment_in_progress',$e->error_code);}
        $lock->release(1,$token); self::assertNotEmpty($lock->acquire(1));
    }
    public static function malformed_requests(): array {
        return [['array-body'],['raw-card'],['query'],['form'],['large'],['missing-key'],['key-array'],['wrong-id'],['status-body']];
    }
    #[DataProvider('malformed_requests')]
    public function test_rejects_unexpected_request_shapes(string $kind): void {
        $r=new WP_REST_Request(); $r->set_header('idempotency-key','dummy-idempotency-0001'); $r->set_header('content-type','application/json');
        match($kind) {
            'array-body'=>$r->body='[]', 'raw-card'=>$r->body='{"card_number":"dummy"}', 'query'=>$r->query=['total'=>'1'], 'form'=>$r->form=['currency'=>'usd'], 'large'=>$r->body=str_repeat(' ',2049), 'missing-key'=>$r->set_header('idempotency-key',''), 'key-array'=>$r->set_header('idempotency-key','a,b'), 'wrong-id'=>$r->id=[], 'status-body'=>$r->body='{}'
        };
        $this->expectException(Failure::class); (new Request_Validator())->validate($r,$kind!=='status-body');
    }
    public function test_valid_empty_request_and_id_schema(): void {
        $r=new WP_REST_Request(); $r->set_header('idempotency-key','dummy-idempotency-0001');
        self::assertSame('dummy-idempotency-0001',(new Request_Validator())->validate($r,true));
        self::assertFalse((new Request_Validator())->order_id('1e3')); self::assertFalse((new Request_Validator())->order_id(1.5));
    }
    public function test_logging_accepts_only_fixed_categories_and_order_ids(): void {
        $GLOBALS['test_logs']=[];
        $logger=new \QuixDevs\StripeRestPayments\Support\Logger();
        $logger->failure('client_secret=must-not-log',1);
        self::assertSame([],$GLOBALS['test_logs']);
        $logger->failure('provider_unavailable',1);
        self::assertSame([['provider_unavailable',['source'=>'quixdevs-stripe-rest-payments','order_id'=>1]]],$GLOBALS['test_logs']);
        self::assertArrayNotHasKey('order_id',$GLOBALS['test_options']['quixdevs_stripe_rest_payments_last_diagnostic']);
    }
    public function test_wordpress_routing_query_and_empty_json_whitespace(): void {
        $r=new WP_REST_Request(body:'{ }',query:['rest_route'=>'/fixture']);
        $r->set_header('content-type','application/json');$r->set_header('idempotency-key','dummy-idempotency-0001');
        self::assertSame('dummy-idempotency-0001',(new Request_Validator())->validate($r,true));
        $r->query=['rest_route'=>'/wrong-route'];$this->expectException(Failure::class);(new Request_Validator())->validate($r,true);
    }
}
