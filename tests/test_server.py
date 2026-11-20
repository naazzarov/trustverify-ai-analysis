import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from trustverify.audit import replay_receipt
from trustverify.benchmark import generate
from trustverify.server import make_handler


class LocalDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name);generate(cls.root)
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(cls.root))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.tmp.cleanup()
    def post(self,route,payload,origin=None):
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        request=urllib.request.Request(self.base+route,data=json.dumps(payload).encode(),headers=headers)
        with urllib.request.urlopen(request) as response:return json.load(response)
    def test_custom_csv_recompute_receipt_and_replay(self):
        payload={'csv':'amount,weight\n10,1\n20,3\n','spec':{
            'op':'weighted_mean','column':'amount','weight':'weight','unit':'points'}}
        preview=self.post('/api/preview',payload)
        self.assertEqual(len(preview['rows']),2)
        report=self.post('/api/repair',payload)
        self.assertEqual(report['metrics']['value'],17.5)
        receipt=self.post('/api/receipt',dict(payload,report=report))
        self.assertEqual(replay_receipt(payload['csv'].encode(),receipt)['status'],'pass')
    def test_foreign_origin_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.post('/api/verify',{'id':'sum-02','report':{}},'https://unrelated.example')
        self.assertEqual(caught.exception.code,403)
        caught.exception.close()
    def test_oversized_and_malformed_inputs_rejected(self):
        for payload,code in [({'csv':'x'*100001},413),({'csv':'x,x\n1,2','spec':{}},400),([],400)]:
            with self.subTest(code=code):
                with self.assertRaises(urllib.error.HTTPError) as caught:self.post('/api/verify',payload)
                self.assertEqual(caught.exception.code,code)
                caught.exception.close()
    def test_controlled_fault_and_clean_recompute(self):
        example=self.post('/api/example',{'id':'ratio-02','fault':'numeric'})
        self.assertEqual(self.post('/api/verify',{'id':'ratio-02','report':example['report']})['status'],'fail')
        fixed=self.post('/api/repair',{'id':'ratio-02'})
        self.assertEqual(self.post('/api/verify',{'id':'ratio-02','report':fixed})['status'],'pass')


if __name__=='__main__':unittest.main()
