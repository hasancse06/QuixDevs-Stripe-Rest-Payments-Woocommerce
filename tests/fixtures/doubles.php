<?php
/** Intentionally minimal standalone doubles; not evidence of WooCommerce acceptance. */
function __($text, $domain = '') { return $text; }
function get_site_url() { return 'https://example.test'; }
function esc_url($url) { return $url; }
function wp_json_encode($data) { return json_encode($data); }
function user_can($id, $cap) { return !empty($GLOBALS['test_caps'][$id][$cap]); }
function get_current_user_id() { return $GLOBALS['test_user'] ?? 0; }
function is_ssl() { return $GLOBALS['test_ssl'] ?? true; }
function wc_get_order($id) { return isset($GLOBALS['test_orders'][$id]) ? clone $GLOBALS['test_orders'][$id] : false; }
function wp_generate_uuid4() { return bin2hex(random_bytes(16)); }
function add_option($name, $value, $deprecated = '', $autoload = null) {
    if (isset($GLOBALS['test_options'][$name])) { return false; }
    $GLOBALS['test_options'][$name] = $value; return true;
}
function wp_cache_delete($name, $group) { return true; }
class TestWpdb {
    public $options = 'wp_options';
    public function prepare($query, ...$args) { return json_encode([$query,$args]); }
    public function query($query) {
        [$sql, [$name, $token]] = json_decode($query, true);
        if (str_starts_with($sql,'INSERT IGNORE')) {if(isset($GLOBALS['test_options'][$name])) {return 0;} $GLOBALS['test_options'][$name]=$token;return 1;}
        if (($GLOBALS['test_options'][$name] ?? null) === $token) { unset($GLOBALS['test_options'][$name]); return 1; }
        return 0;
    }
}
$GLOBALS['wpdb'] = new TestWpdb();
class WC_Order {
    public int $id = 1;
    public int $owner = 10;
    public string $total = '10.00';
    public string $currency = 'USD';
    public string $method = 'stripe';
    public string $status = 'pending';
    public string $transaction = '';
    public array $meta = [];
    public function get_id() { return $this->id; }
    public function get_order_number() { return (string)$this->id; }
    public function get_type() { return 'shop_order'; }
    public function get_customer_id() { return $this->owner; }
    public function get_total() { return $this->total; }
    public function get_currency() { return $this->currency; }
    public function get_payment_method() { return $this->method; }
    public function get_order_key() { return 'wc_order_dummy'; }
    public function get_transaction_id() { return $this->transaction; }
    public function get_status() { return $this->status; }
    public function is_paid() { return in_array($this->status, ['processing', 'completed'], true); }
    public function has_status($statuses) { return in_array($this->status, (array)$statuses, true); }
    public function needs_payment() { return in_array($this->status, ['pending', 'failed'], true) && (float)$this->total > 0; }
    public function get_meta($key, $single = true) { return $this->meta[$key] ?? ''; }
    public function update_meta_data($key, $value) { $this->meta[$key] = $value; }
    public function save_meta_data() { $GLOBALS['test_orders'][$this->id] = clone $this; }
}
class WP_REST_Request {
    private array $headers = [];
    public function __construct(public string $method = 'POST', public string $body = '', public array $query = [], public array $form = [], public array $files = [], public mixed $id = '1') {}
    public function get_route() { return '/fixture'; }
    public function get_url_params() { return ['order_id' => $this->id]; }
    public function get_body() { return $this->body; }
    public function get_query_params() { return $this->query; }
    public function get_body_params() { return $this->form; }
    public function get_file_params() { return $this->files; }
    public function get_header($key) { return $this->headers[$key] ?? null; }
    public function set_header($key, $value) { $this->headers[$key] = $value; }
    public function is_json_content_type() { return ($this->headers['content-type'] ?? '') === 'application/json'; }
}

function wc_get_logger() { return new class { public function warning($message,$context) { $GLOBALS['test_logs'][]=[$message,$context]; } }; }
function update_option($key,$value,$autoload=null) { $GLOBALS['test_options'][$key]=$value; return true; }
