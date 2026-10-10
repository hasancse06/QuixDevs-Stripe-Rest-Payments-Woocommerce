<?php
use PHPUnit\Framework\TestCase;
use QuixDevs\StripeRestPayments\Payments\Payment_Lock;
final class ConcurrencyTest extends TestCase {
    public function test_four_independent_workers_have_one_lock_owner(): void {
        if(!getenv('QUIXDEVS_WP_ROOT')) {self::markTestSkipped('Disposable WordPress required.');}
        $barrier=sys_get_temp_dir().'/quixdevs-barrier-'.bin2hex(random_bytes(8));$id=987654322;
        delete_option(Payment_Lock::PREFIX.$id);
        $workers=[];
        try {
            for($i=0;$i<4;$i++) {
                $process=proc_open([PHP_BINARY,dirname(__DIR__).'/fixtures/lock-worker.php',$barrier,(string)$i,(string)$id],[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes);
                self::assertIsResource($process); fclose($pipes[0]); $workers[]=[$process,$pipes];
            }
            $deadline=microtime(true)+20;
            while(count(glob($barrier.'.ready.*'))!==4) {if(microtime(true)>$deadline) {self::fail('Workers did not reach barrier.');} usleep(10000);}
            touch($barrier);$results=[];
            foreach($workers as [$process,$pipes]) {$results[]=stream_get_contents($pipes[1]);$errors=stream_get_contents($pipes[2]);fclose($pipes[1]);fclose($pipes[2]);self::assertSame(0,proc_close($process),$errors);}
            self::assertSame(1,count(array_filter($results,fn($v)=>$v==='won')),json_encode($results));
            self::assertSame(3,count(array_filter($results,fn($v)=>$v==='payment_in_progress')),json_encode($results));
        } finally {
            foreach(glob($barrier.'*') as $path) {unlink($path);}
            delete_option(Payment_Lock::PREFIX.$id);
        }
    }
}
