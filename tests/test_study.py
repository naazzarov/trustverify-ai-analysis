import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from trustverify.benchmark import gold_correct
from trustverify.core import calculate
from trustverify.public_data import reference
from trustverify.study import call, digest, fields, paired, schema_valid, validate_saved


class StudyTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{'amount':'10','weight':'1','region':'A'},
                     {'amount':'20','weight':'3','region':'B'}]
        self.spec = {'op':'weighted_mean','column':'amount','weight':'weight','unit':'points'}
        self.gold = reference(self.rows,self.spec)

    def test_descriptive_public_columns_and_hand_result(self):
        self.assertEqual(self.gold['metrics']['value'],17.5)
        self.assertTrue(gold_correct(calculate(self.rows,self.spec),self.gold))

    def test_schema_does_not_supply_correctness(self):
        wrong = copy.deepcopy(self.gold)
        wrong['metrics']['value'] = 999
        wrong['unit'] = 'unknown'
        wrong['chart']['values'] = [0,1]  # Equal lengths are not a schema constraint.
        self.assertTrue(schema_valid(wrong))
        self.assertFalse(gold_correct(wrong,self.gold))
        self.assertFalse(fields(wrong,self.gold)['numeric'])
        self.assertFalse(fields(wrong,self.gold)['chart'])

    def test_schema_rejects_extras_bool_and_long_narrative(self):
        for field,value in [('extra',1),('rows_used',True),('narrative','x'*161)]:
            report = copy.deepcopy(self.gold); report[field] = value
            self.assertFalse(schema_valid(report))
        report = copy.deepcopy(self.gold); report['metrics']['value'] = True
        self.assertFalse(schema_valid(report))

    def test_exact_paired_counts(self):
        result = paired([False]*6,[True]*6)
        self.assertEqual(result['improved'],6)
        self.assertEqual(result['regressed'],0)
        self.assertEqual(result['exact_mcnemar_two_sided_p'],.03125)
        self.assertEqual(paired([True,False],[True,False])['exact_mcnemar_two_sided_p'],1)
        self.assertEqual(paired([True,False],[False,True])['difference'],0)

    def test_resume_rejects_response_tampering_and_context_change(self):
        request = {'format':'json'}; frozen = {'model_digest':'abc','protocol':'first'}
        response = {'message':{'content':'{}'}}
        result = {'request':request,'request_sha256':digest(request),
                  'context_sha256':digest(frozen),'response':response,'response_sha256':digest(response)}
        validate_saved(result,request,frozen)
        with self.assertRaises(RuntimeError): validate_saved(result,request,dict(frozen,model_digest='new'))
        result['response']['message']['content'] = '{"changed":true}'
        with self.assertRaises(RuntimeError): validate_saved(result,request,frozen)

    def test_operational_failure_does_not_create_content_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'call.json'
            with patch('trustverify.study.post',side_effect=OSError('Unavailable')):
                with self.assertRaises(OSError): call('http://local','test',[],'json',path,{})
            self.assertFalse(path.exists())

    def test_complete_case_and_scaling_metamorphic_properties(self):
        base = calculate(self.rows,self.spec)['metrics']['value']
        scaled = [dict(r,weight=str(7*int(r['weight']))) for r in self.rows]
        self.assertEqual(calculate(scaled,self.spec)['metrics']['value'],base)
        missing = self.rows + [{'amount':'1000','weight':'','region':'A'}]
        self.assertEqual(calculate(missing,self.spec)['metrics']['value'],base)
        reversed_rows = list(reversed(self.rows))
        self.assertEqual(calculate(reversed_rows,self.spec)['metrics']['value'],base)


if __name__ == '__main__': unittest.main()
