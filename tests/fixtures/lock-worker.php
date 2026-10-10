<?php
/** Separate PHP process used by the persistent concurrency integration test. */
require dirname(__DIR__).'/bootstrap.php';
$barrier=$argv[1]; $worker=$argv[2]; $order_id=(int)$argv[3];
file_put_contents($barrier.'.ready.'.$worker,'ready');
$deadline=microtime(true)+20;
while(!is_file($barrier)) {if(microtime(true)>$deadline) {exit(2);} usleep(10000);}
$lock=new QuixDevs\StripeRestPayments\Payments\Payment_Lock();
try {
    $token=$lock->acquire($order_id);
    file_put_contents($barrier.'.attempt.'.$worker,'acquired');
    // Keep ownership until every contender has tried, irrespective of scheduling delays.
    try {
        while(count(glob($barrier.'.attempt.*'))!==4) {if(microtime(true)>$deadline) {exit(3);} usleep(10000);}
        echo 'won';
    } finally {$lock->release($order_id,$token);}
} catch(QuixDevs\StripeRestPayments\Support\Failure $e) {
    file_put_contents($barrier.'.attempt.'.$worker,'rejected');
    echo $e->error_code;
}
