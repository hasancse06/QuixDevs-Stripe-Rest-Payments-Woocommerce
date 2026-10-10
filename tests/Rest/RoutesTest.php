<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use QuixDevs\StripeRestPayments\Rest\Routes;
use QuixDevs\StripeRestPayments\Authentication\Order_Authorizer;
final class RoutesTest extends TestCase {
    private int $owner;
    private int $other;
    private WC_Order $order;
    protected function setUp(): void {
        if (!getenv('QUIXDEVS_WP_ROOT')) {self::markTestSkipped('Disposable WordPress required.');}
        update_option('woocommerce_custom_orders_table_enabled','no');
        $this->owner=wp_insert_user(['user_login'=>'owner_'.wp_generate_password(10,false),'user_pass'=>wp_generate_password(),'role'=>'customer']);
        $this->other=wp_insert_user(['user_login'=>'other_'.wp_generate_password(10,false),'user_pass'=>wp_generate_password(),'role'=>'customer']);
        $this->order=wc_create_order(['customer_id'=>$this->owner,'status'=>'pending']);$this->order->set_payment_method('stripe');$this->order->set_total('10.00');$this->order->save();
        wp_set_current_user($this->owner); rest_get_server();
    }
    protected function tearDown(): void {
        if(isset($this->order)) {$this->order->delete(true); require_once ABSPATH.'wp-admin/includes/user.php';wp_delete_user($this->owner);wp_delete_user($this->other);}
        wp_set_current_user(0);
    }
    private function request(string $action='prepare',string $method='POST',string $body='{}'): WP_REST_Response {
        $r=new WP_REST_Request($method,'/'.Routes::NAMESPACE.'/orders/'.$this->order->get_id().'/'.$action);
        $r->set_header('Content-Type','application/json');$r->set_header('Idempotency-Key','rest-fixture-key-0001');$r->set_body($body);
        return rest_do_request($r);
    }
    public function test_routes_methods_and_permission_callbacks(): void {
        $routes=rest_get_server()->get_routes();
        foreach(['prepare'=>'POST','status'=>'GET'] as $action=>$method) {
            $route='/'.Routes::NAMESPACE.'/orders/(?P<order_id>[1-9][0-9]{0,17})/'.$action;
            self::assertArrayHasKey($route,$routes);self::assertTrue($routes[$route][0]['methods'][$method]);self::assertIsCallable($routes[$route][0]['permission_callback']);
        }
    }
    public function test_owner_can_prepare_and_repeat(): void {
        $first=$this->request(); self::assertSame(200,$first->get_status(),json_encode($first->get_data()));
        self::assertFalse($first->get_data()['reused']);self::assertTrue($this->request()->get_data()['reused']);
        self::assertSame(200,$this->request('status','GET','')->get_status());
    }
    public function test_anonymous_and_cross_customer_access_denied(): void {
        wp_set_current_user(0);self::assertSame(401,$this->request()->get_status());
        wp_set_current_user($this->other);self::assertSame(403,$this->request()->get_status());
    }
    public function test_capability_alone_does_not_grant_order_access(): void {
        $user=get_user_by('id',$this->other);$user->add_cap(Order_Authorizer::CAPABILITY);
        wp_set_current_user($this->other);self::assertSame(403,$this->request()->get_status());
        $this->order->update_meta_data(Order_Authorizer::SCOPE_META,(string)$this->other);$this->order->save();
        self::assertSame(200,$this->request()->get_status());
    }
    public function test_guests_raw_cards_amount_and_currency_are_rejected(): void {
        foreach(['{"amount":1}','{"currency":"eur"}','{"card_number":"dummy"}','[]'] as $body) {self::assertSame(400,$this->request('prepare','POST',$body)->get_status());}
        $this->order->set_customer_id(0);$this->order->save();self::assertSame(403,$this->request()->get_status());
    }
    public function test_error_and_success_responses_have_no_store_headers(): void {
        $request=new WP_REST_Request('POST','/'.Routes::NAMESPACE.'/orders/'.$this->order->get_id().'/prepare');
        $request->set_header('Idempotency-Key','rest-fixture-key-0001');
        $response=rest_do_request($request);self::assertSame(200,$response->get_status());
        $response=apply_filters('rest_post_dispatch',$response,rest_get_server(),$request);
        self::assertStringContainsString('no-store',$response->get_headers()['Cache-Control']);
        wp_set_current_user(0);$response=rest_do_request($request);$response=apply_filters('rest_post_dispatch',$response,rest_get_server(),$request);
        self::assertStringContainsString('no-store',$response->get_headers()['Cache-Control']);
    }
    public function test_core_application_password_authentication_and_invalid_credentials(): void {
        $user=get_user_by('id',$this->owner);
        [$password]=WP_Application_Passwords::create_new_application_password($this->owner,['name'=>'Disposable PHPUnit fixture']);
        add_filter('application_password_is_api_request','__return_true');
        try {
            $valid=wp_authenticate_application_password(null,$user->user_login,$password);self::assertInstanceOf(WP_User::class,$valid);self::assertSame($this->owner,$valid->ID);
            $invalid=wp_authenticate_application_password(null,$user->user_login,'invalid-fixture-password');self::assertInstanceOf(WP_Error::class,$invalid);
        } finally {remove_filter('application_password_is_api_request','__return_true');WP_Application_Passwords::delete_all_application_passwords($this->owner);}
    }
    public function test_forged_cookie_nonce_is_rejected_by_wordpress(): void {
        $GLOBALS['wp_rest_auth_cookie']=true;$_SERVER['HTTP_X_WP_NONCE']='forged-fixture-nonce';
        try {self::assertInstanceOf(WP_Error::class,rest_cookie_check_errors(null));}
        finally {unset($_SERVER['HTTP_X_WP_NONCE']);$GLOBALS['wp_rest_auth_cookie']=null;}
    }
    public function test_bootstrap_is_idempotent(): void {
        $before=has_action('rest_api_init');(new \QuixDevs\StripeRestPayments\Plugin())->register();
        self::assertSame($before,has_action('rest_api_init'));
    }
    public function test_plain_permalink_routing_query_is_supported(): void {
        $route='/'.Routes::NAMESPACE.'/orders/'.$this->order->get_id().'/status';
        $r=new WP_REST_Request('GET',$route);$r->set_query_params(['rest_route'=>$route]);
        self::assertSame(200,rest_do_request($r)->get_status());
        $r->set_query_params(['rest_route'=>$route,'amount'=>'1']);self::assertSame(400,rest_do_request($r)->get_status());
    }
}
