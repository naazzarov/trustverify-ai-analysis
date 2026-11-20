import copy
import unittest
from trustverify.audit import create_receipt, parse_csv, replay_receipt
from trustverify.core import calculate, ContractError


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.csv = b'x,n\n10,1\n20,3\n,5\n'
        self.spec = {'op':'weighted_mean','column':'x','weight':'n','unit':'points'}
        self.report = calculate(parse_csv(self.csv),self.spec)

    def test_replay_preserves_pass_fail_and_abstention(self):
        for spec,report,status in [(self.spec,self.report,'pass'),
            (self.spec,dict(self.report,unit='USD'),'fail'),
            (dict(self.spec,op='regression'),self.report,'abstain')]:
            with self.subTest(status=status):
                receipt = create_receipt(self.csv,spec,report)
                self.assertEqual(replay_receipt(self.csv,receipt)['status'],status)

    def test_data_receipt_and_engine_changes_are_rejected(self):
        receipt = create_receipt(self.csv,self.spec,self.report)
        with self.assertRaises(ValueError): replay_receipt(self.csv+b'50,2\n',receipt)
        changed = copy.deepcopy(receipt); changed['report']['unit'] = 'USD'
        with self.assertRaises(ValueError): replay_receipt(self.csv,changed)
        changed = copy.deepcopy(receipt); changed['verification']['status'] = 'fail'
        with self.assertRaises(ValueError): replay_receipt(self.csv,changed)

    def test_utf8_bom_and_quoted_csv(self):
        rows = parse_csv(b'\xef\xbb\xbfx,g\r\n10,"A, B"\r\n')
        self.assertEqual(rows,[{'x':'10','g':'A, B'}])
        for body in [b'x,x\n1,2',b'x,n\n1,2,3',b'x,n\n1',b'\xff']:
            with self.assertRaises(ContractError): parse_csv(body)

    def test_causal_prose_scope_is_preserved_in_receipt(self):
        report = dict(self.report,narrative='This proves that group causes the outcome.')
        receipt = create_receipt(self.csv,self.spec,report)
        self.assertEqual(receipt['verification']['status'],'pass')
        self.assertIn('Narrative meaning',receipt['scope'])
        self.assertIn('not a digital signature',receipt['integrity'])


if __name__ == '__main__': unittest.main()
