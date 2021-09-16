from types import resolve_bases
from numpy import true_divide
import pandas as pd
import yaml
import os
import re

pwd = os.getcwd()
synonym_rules = os.path.join(pwd, "rulebook/synonym_rules.yaml")
data_folder = os.path.join(pwd, "data/")
syn_schema = os.path.join(pwd, "schema.yaml")


def main():
    with open(synonym_rules, "r") as rules, open(
        syn_schema, "r"
    ) as schema_file:
        try:
            rule_book = yaml.safe_load(rules)
            schema = yaml.safe_load(schema_file)
            prefix_cols = ["id", "text"]
            rules_cols = schema["classes"]["Rule"]["slots"]
            prefix_df = pd.DataFrame(columns=prefix_cols)
            rules_df = pd.DataFrame(columns=rules_cols)
            terms_cols = [
                "cui",
                "source",
                "id",
                "match_term",
                "preferred_term",
                "category",
            ]
            new_terms_df = pd.DataFrame(columns=terms_cols)

            for key, value in rule_book["prefixes"].items():
                # key = key.replace("_", " ")
                row = pd.DataFrame([[value, key]], columns=prefix_cols)
                prefix_df = pd.concat([prefix_df, row])

            for idx, dic in enumerate(rule_book["rules"]):
                row = pd.DataFrame(columns=rules_cols)
                for col in row.columns:
                    if col in dic.keys():
                        row.loc[idx, col] = dic[col]
                if len(row) > 0:
                    rules_df = pd.concat([rules_df, row])

            rules_df = rules_df.reset_index()
            rules_df.fillna("", inplace=True)
            rules_exp_branch_df = rules_df.explode("branches")

            ontologies = list(
                set([x[0] for x in prefix_df["id"].str.split(":")])
            )
            print(f"Ontologies that need synonymization: {ontologies}")

            for ont in ontologies:
                terms_filename = ont.lower() + "_termlist.tsv"

                if os.path.isfile(os.path.join(data_folder, terms_filename)):
                    print(
                        f"Found termlist file for the ontology "
                        f"{ont} in the data folder {data_folder}"
                    )

                    terms = os.path.join(data_folder, terms_filename)
                    terms_df = pd.read_csv(
                        terms, sep="\t", low_memory=False, names=terms_cols
                    )

                    # ENVO has spaces in its terms
                    # GO has underscores in its terms
                    # if ont == "ENVO":
                    #     prefix_df["text"] = prefix_df["text"].str.replace(
                    #         "_", " "
                    #     )

                    pref_sub = prefix_df[prefix_df["id"].str.startswith(ont)]
                    terms_sub = pd.merge(
                        left=pref_sub, right=terms_df, on="id"
                    )

                    relevant_rules_df = pd.merge(
                        how="inner",
                        left=rules_exp_branch_df,
                        left_on="branches",
                        right=terms_sub,
                        right_on="text",
                    )
                    match_df = relevant_rules_df["match"].drop_duplicates()

                    relevant_rules_df.to_csv(
                        os.path.join(data_folder, "rules.tsv"),
                        sep="\t",
                        index=None,
                    )

                    for row in match_df.iteritems():
                        need_syn_df = terms_df[
                            terms_df.match_term.str.match(row[1] + "$")
                            # terms_df.match_term.str.match(
                            #     ".*(biome|ecosystem)$"
                            # )
                            # re.match(row[1] + "$", terms_df.match_term)
                        ]
                        need_syn_df = need_syn_df[
                            ~need_syn_df["preferred_term"].str.contains(
                                "SYNONYM_OF:"
                            )
                        ]

                        replacement_df = relevant_rules_df[
                            relevant_rules_df["match"] == row[1]
                        ]["replacement"]

                        need_syn_df.to_csv(
                            os.path.join(data_folder, "needSyns.tsv"),
                            sep="\t",
                            index=None,
                        )

                        for syn_row in need_syn_df.iterrows():
                            for rule in replacement_df.iteritems():
                                syn_row_df = (
                                    syn_row[1]
                                    .to_frame()
                                    .T.reset_index()
                                    .drop(["index"], axis=1)
                                )

                                term_to_replace = row[1]
                                replacement_term = rule[1]

                                syn_row_df["match_term"] = syn_row_df[
                                    "match_term"
                                ].replace(
                                    term_to_replace,
                                    replacement_term,
                                    regex=True,
                                )

                                import pdb

                                pd.set_option("display.max_colwidth", None)
                                pdb.set_trace()

                else:
                    raise (
                        FileNotFoundError(
                            f"Could not find termlist file for the ontology"
                            f"{ont} in the data folder {data_folder}"
                        )
                    )

            import pdb

            pdb.set_trace()

        except yaml.YAMLError as exec:
            print(exec)


if __name__ == "__main__":
    main()
