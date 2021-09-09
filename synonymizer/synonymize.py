import pandas as pd
import yaml
import os

pwd = os.getcwd()
synonym_rules = os.path.join(pwd, "rulebook/synonym_rules.yaml")
data_folder = os.path.join(pwd, "data/")


def main():
    with open(synonym_rules, "r") as rules:
        try:
            rule_book = yaml.safe_load(rules)
            prefix_cols = ["id", "text"]
            rules_cols = [
                "type",
                "branches",
                "match",
                "match_scope",
                "replacement",
                "replacement_scope",
            ]
            prefix_df = pd.DataFrame(columns=prefix_cols)
            rules_df = pd.DataFrame(columns=rules_cols)
            terms_cols = [
                "cui",
                "source",
                "id",
                "match_term",
                "root_term",
                "category",
            ]

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

            ontologies = list(
                set([x[0] for x in prefix_df["id"].str.split(":")])
            )
            print(f"Ontologies that need synonymization: {ontologies}")

            for ont in ontologies:
                terms_filename = ont.lower() + "_termlist.tsv"

                if os.path.isfile(os.path.join(data_folder, terms_filename)):
                    print(
                        f"Found termlist file for the ontology"
                        f"{ont} in the data folder {data_folder}"
                    )

                    terms = os.path.join(data_folder, terms_filename)
                    terms_df = pd.read_csv(
                        terms, sep="\t", low_memory=False, names=terms_cols
                    )

                    # ENVO has spaces in its terms
                    # GO has underscores in its terms
                    if ont == "ENVO":
                        prefix_df["text"] = prefix_df["text"].str.replace(
                            "_", " "
                        )

                    pref_sub = prefix_df[prefix_df["id"].str.startswith(ont)]
                    terms_sub = pd.merge(
                        left=pref_sub, right=terms_df, on="id"
                    )

                else:
                    raise (
                        FileNotFoundError(
                            f"Could not find termlist file for the ontology"
                            f"{ont} in the data folder {data_folder}"
                        )
                    )

        except yaml.YAMLError as exec:
            print(exec)


if __name__ == "__main__":
    main()
