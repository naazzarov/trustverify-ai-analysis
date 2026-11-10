import copy
import json
import tempfile
import unittest
from pathlib import Path
from trustverify.benchmark import generate, gold_correct, load_tasks, mutate, oracle, FAULTS
from trustverify.core import calculate, ContractError, load_rows, repair, verify
from trustverify.live import paired_bootstrap

ROWS = [{"x":"10", "n":"1", "g":"A"}, {"x":"20", "n":"3", "g":"B"},
        {"x":"", "n":"5", "g":"A"}, {"x":"30", "n":"", "g":"A"}]


class ArithmeticTests(unittest.TestCase):
    def test_hand_calculations(self):
        expectations = {"sum":60, "mean":20, "weighted_mean":17.5, "ratio":750, "pct_change":200}
        for op,value in expectations.items():
            spec = {"op":op,"column":"x","weight":"n","denominator":"n","unit":"%"}
            with self.subTest(op=op): self.assertAlmostEqual(calculate(ROWS,spec)["metrics"]["value"],value)
    def test_group_sum_and_complete_case(self):
        spec = {"op":"group_sum","column":"x","group":"g","unit":"points"}
        self.assertEqual(calculate(ROWS,spec)["metrics"], {"A":40.0,"B":20.0})
        spec.update(op="weighted_mean",weight="n")
        self.assertEqual(calculate(ROWS,spec)["rows_used"],2)
    def test_abstention(self):
        for rows,spec in [([], {"op":"sum","column":"x","unit":"x"}),
            (ROWS,{"op":"causal_effect","column":"x","unit":"x"}),
            ([{"x":"1","n":"0"}],{"op":"ratio","column":"x","denominator":"n","unit":"%"}),
            (ROWS,{"op":"sum","column":"missing","unit":"x"})]:
            with self.subTest(spec=spec): self.assertEqual(verify(rows,spec,{})["status"],"abstain")
    def test_nonfinite_and_negative_weights(self):
        spec={"op":"weighted_mean","column":"x","weight":"n","unit":"x"}
        for row in [{"x":"NaN","n":"1"},{"x":"1","n":"-1"},{"x":True,"n":"1"}]:
            with self.assertRaises(ContractError): calculate([row],spec)
    def test_malformed_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"bad.csv"
            for text in ["x,x\n1,2\n","x,n\n1\n","x,n\n1,2,3\n"]:
                p.write_text(text)
                with self.assertRaises(ContractError): load_rows(p)


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.spec={"op":"sum","column":"x","unit":"points"}
        self.report=calculate(ROWS,self.spec)
    def test_clean_and_all_supported_faults(self):
        self.assertEqual(verify(ROWS,self.spec,self.report)["status"],"pass")
        for fault in FAULTS:
            status=verify(ROWS,self.spec,mutate(self.report,fault))["status"]
            self.assertEqual(status,"pass" if fault=="causal_claim" else "fail",fault)
    def test_ablation(self):
        wrong=mutate(self.report,"unit")
        self.assertEqual(verify(ROWS,self.spec,wrong,"numeric")["status"],"pass")
        self.assertEqual(verify(ROWS,self.spec,wrong,"full")["status"],"fail")
    def test_invalid_reports(self):
        for report in [None,[],{"metrics":[]},{}]: self.assertEqual(verify(ROWS,self.spec,report)["status"],"fail")
    def test_bool_infinite_and_tolerance(self):
        for value in [True,float("inf"),float("nan"),"60"]:
            bad=copy.deepcopy(self.report); bad["metrics"]["value"]=value
            self.assertEqual(verify(ROWS,self.spec,bad)["status"],"fail")
        self.report["metrics"]["value"]+=1e-7
        self.assertEqual(verify(ROWS,self.spec,self.report)["status"],"pass")
    def test_chart_duplicates_wrong_lengths_and_unhashable_labels(self):
        for chart in [{"labels":["value","value"],"values":[60,60]},
                      {"labels":["value"],"values":[]},{"labels":[{}],"values":[60]}]:
            bad=copy.deepcopy(self.report);bad["chart"]=chart
            self.assertEqual(verify(ROWS,self.spec,bad)["status"],"fail")
    def test_no_input_mutation_and_repair_disclosure(self):
        bad=mutate(self.report,"numeric"); snapshot=copy.deepcopy(bad)
        fixed=repair(ROWS,self.spec,bad)
        self.assertEqual(bad,snapshot)
        self.assertTrue(gold_correct(fixed,self.report))
        self.assertIn("No causal conclusion",fixed["narrative"])
    def test_wrong_approved_intent_is_a_blind_spot(self):
        wrong={"op":"mean","column":"x","unit":"points"}
        self.assertEqual(verify(ROWS,wrong,calculate(ROWS,wrong))["status"],"pass")
        self.assertNotEqual(calculate(ROWS,wrong)["metrics"],self.report["metrics"])


class BenchmarkTests(unittest.TestCase):
    def test_all_generated_tasks_agree_with_independent_oracle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);tasks,gold=generate(root)
            self.assertEqual(len(tasks),60)
            self.assertEqual(sum(t["split"]=="test" for t in tasks),48)
            self.assertEqual(len({t["data_sha256"] for t in tasks}),60)
            for task in tasks:
                rows=load_rows(root/task["data"])
                self.assertTrue(gold_correct(calculate(rows,task["spec"]),gold[task["id"]]),task["id"])
    def test_sql_oracle_hand_result(self):
        spec={"op":"weighted_mean","column":"x","weight":"n","unit":"points"}
        self.assertEqual(oracle(ROWS,spec)["metrics"]["value"],17.5)
    def test_bootstrap_preserves_pairing(self):
        self.assertEqual(paired_bootstrap([True]*4,[True]*4,100),[0,0])
        self.assertEqual(paired_bootstrap([False]*4,[True]*4,100),[1,1])


if __name__ == "__main__": unittest.main()
