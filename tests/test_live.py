"""Exercise the whole pilot orchestrator without a service or invented live evidence."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from trustverify.benchmark import generate
from trustverify.live import call, decode, run


class LiveOrchestrationTests(unittest.TestCase):
    def test_custom_output_directory_and_equal_call_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);generate(root);(root/'docs').mkdir();(root/'docs/protocol.md').write_text('Test protocol')
            requests=[]
            def fake_call(base,model,messages,path):
                requests.append((messages,path))
                return {'response':{'message':{'content':'{}'},'eval_count':2,'prompt_eval_count':10},'wall_seconds':.001}
            with (patch('trustverify.live.post',return_value={}),
                  patch('trustverify.live.urllib.request.urlopen',return_value=io.StringIO('{"models":[]}')),
                  patch('trustverify.live.call',side_effect=fake_call),contextlib.redirect_stdout(io.StringIO())):
                result=run(root,output=root/'nested/results')
            self.assertEqual(len(requests),72)
            self.assertEqual(sum(len(messages)==2 for messages,_ in requests),24)
            self.assertEqual(sum(len(messages)==4 for messages,_ in requests),48)
            self.assertTrue(all(path.is_relative_to(root/'nested/results') for _,path in requests))
            self.assertEqual(result['deterministic_recompute']['correct'],24)
            self.assertTrue((root/'nested/results/live_pilot.json').exists())
    def test_invalid_constants_and_arrays(self):
        self.assertIsNone(decode('{"x":NaN}'))
        self.assertEqual(decode('[]'),[])  # valid JSON, invalid report; scorer handles this distinction
    def test_operational_failure_is_not_saved_as_model_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'call.json'
            with patch('trustverify.live.post',side_effect=OSError('Service unavailable')):
                with self.assertRaises(OSError):call('http://local','test',[],path)
            self.assertFalse(path.exists())


if __name__=='__main__':unittest.main()
