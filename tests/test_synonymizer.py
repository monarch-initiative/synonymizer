import unittest
import yaml
import pandas as pd
from . import SCHEMA, TEST_SYNONYM_RULES, TEST_DATA_FOLDER
import re
import os
import synonymizer.synonymize as syn


class TestSynonymizer(unittest.TestCase):
    def setUp(self) -> None:
        with open(TEST_SYNONYM_RULES, "r") as rules, open(SCHEMA, "r") as sf:
            try:
                self.rule_book = yaml.safe_load(rules)
                self.schema = yaml.safe_load(sf)
                self.prefix_cols = ["id", "text"]
                self.rules_cols = self.schema["classes"]["Rule"]["slots"]
                self.test_cols = self.schema["classes"]["Test"]["slots"]
                self.prefix_df = pd.DataFrame(columns=self.prefix_cols)
                self.rules_df = pd.DataFrame(columns=self.rules_cols)
                self.test_df = pd.DataFrame(columns=self.test_cols)
                self.terms_cols = [
                    "cui",
                    "source",
                    "id",
                    "match_term",
                    "preferred_term",
                    "category",
                ]

                # Setup rules_df
                for idx, dic in enumerate(self.rule_book["rules"]):
                    row = pd.DataFrame(columns=self.rules_cols)
                    for col in row.columns:
                        if col in dic.keys():
                            row.loc[idx, col] = dic[col]
                    if len(row) > 0:
                        self.rules_df = pd.concat([self.rules_df, row])

            except yaml.YAMLError as exec:
                print(exec)

    def test_rule_count(self) -> None:
        self.assertEqual(len(self.rules_df), 20)

    def test_schema_compliance(self) -> None:
        for key, dic in self.schema["slots"].items():
            if "required" in dic.keys() and dic["required"]:
                self.assertFalse(self.rules_df[key].isnull().any())

    def test_tests(self) -> None:
        list_of_tests = self.rules_df[["match", "replacement", "tests"]]
        list_of_tests["tests"] = list_of_tests["tests"].explode()

        for row in list_of_tests.iterrows():

            new_concept = re.sub(
                row[1]["match"],
                row[1]["replacement"],
                row[1]["tests"]["input"],
            )

            self.assertEqual(new_concept.strip(), row[1]["tests"]["output"])

    def test_synonymize(self):
        syn.run(rule_file=TEST_SYNONYM_RULES, data_folder=TEST_DATA_FOLDER)
        termlists = {
            "envo": ["envo_output.tsv", "envo_syn_termlist.tsv"],
            "go": ["go_output.tsv", "go_syn_termlist.tsv"],
        }

        for key, val in termlists.items():
            actual_output = pd.read_csv(
                os.path.join(TEST_DATA_FOLDER, val[0]),
                sep="\t",
                low_memory=False,
            )

            expected_output = pd.read_csv(
                os.path.join(TEST_DATA_FOLDER, val[1]),
                sep="\t",
                low_memory=False,
            )

            self.assertTrue(actual_output.equals(expected_output))

            # Cleanup: remove generated output.
            os.remove(os.path.join(TEST_DATA_FOLDER, val[1]))
