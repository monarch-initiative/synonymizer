import pandas as pd
import yaml
import os
from . import DATA_FOLDER, SCHEMA, SYNONYM_RULES


def run(
    rule_file: str = SYNONYM_RULES,
    schema_file: str = SCHEMA,
    data_folder: str = DATA_FOLDER,
):
    """Add rules to capture more terms as synonyms during named entity
    recognition (NER)

    :param rule_file: YAML file that contains the rules.,
                      defaults to SYNONYM_RULES
    :type rule_file: str
    :param schema_file: YAML file that provides schema., defaults to SCHEMA
    :type schema_file: str
    :param data_folder: Data folder where the input termlists are located and
                        the ouput files are saved.,
                        defaults to DATA_FOLDER
    :type data_folder: str
    """
    with open(rule_file, "r") as rules, open(schema_file, "r") as sf:
        try:
            rule_book = yaml.safe_load(rules)
            schema = yaml.safe_load(sf)
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

            for key, value in rule_book["prefixes"].items():
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

            # DEBUG BLOCK *****************************************
            # rules_exp_branch_df.to_csv(
            #     os.path.join(data_folder, "rules.tsv"),
            #     sep="\t",
            #     index=None,
            # )
            # *****************************************************

            ontologies = list(
                set([x[0] for x in prefix_df["id"].str.split(":")])
            )
            print(f"Ontologies that need synonymization: {ontologies}")

            for ont in ontologies:
                terms_filename = ont.lower() + "_termlist.tsv"
                new_terms_filename = ont.lower() + "_syn_termlist.tsv"
                new_terms_df = pd.DataFrame(columns=terms_cols)

                if os.path.isfile(os.path.join(data_folder, terms_filename)):
                    print(
                        f"Found termlist file for the ontology "
                        f"{ont} in the data folder {data_folder}"
                    )

                    terms = os.path.join(data_folder, terms_filename)
                    terms_df = pd.read_csv(
                        terms, sep="\t", low_memory=False, names=terms_cols
                    )

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
                    match_replacement_df = relevant_rules_df[
                        ["match", "replacement"]
                    ].drop_duplicates()

                    # DEBUG BLOCK *****************************************
                    # match_replacement_df.to_csv(
                    #     os.path.join(
                    #         data_folder, ont + "_match_replacement.tsv"
                    #     ),
                    #     sep="\t",
                    #     index=None,
                    # )

                    # relevant_rules_df.to_csv(
                    #     os.path.join(data_folder, ont + "_rules.tsv"),
                    #     sep="\t",
                    #     index=None,
                    # )
                    # **************************************************

                    for row in match_replacement_df.iterrows():
                        need_syn_df = terms_df[
                            terms_df.match_term.str.match(
                                row[1]["match"] + "$"
                            )
                        ]
                        need_syn_df = need_syn_df[
                            ~need_syn_df["preferred_term"].str.contains(
                                "SYNONYM_OF:"
                            )
                        ]

                        # DEBUG BLOCK *****************************************
                        # need_syn_df.to_csv(
                        #     os.path.join(data_folder, ont + "_needSyns.tsv"),
                        #     sep="\t",
                        #     index=None,
                        # )
                        # *****************************************************

                        for syn_row in need_syn_df.iterrows():
                            syn_row_df = (
                                syn_row[1]
                                .to_frame()
                                .T.reset_index()
                                .drop(["index"], axis=1)
                            )

                            term_to_replace = row[1]["match"] + "$"
                            replacement_term = row[1]["replacement"]

                            syn_row_df["match_term"] = syn_row_df[
                                "match_term"
                            ].replace(
                                term_to_replace,
                                replacement_term,
                                regex=True,
                            )

                            syn_row_df["preferred_term"] = (
                                syn_row_df["match_term"]
                                + "[SYNONYM_OF:"
                                + syn_row_df["preferred_term"]
                                + "]"
                            )

                            new_terms_df = pd.concat(
                                [new_terms_df, syn_row_df]
                            )

                    new_terms_df = new_terms_df.drop_duplicates()

                    # DEBUG BLOCK *****************************************
                    # new_terms_df.to_csv(
                    #     os.path.join(data_folder, "new_" + terms_filename),
                    #     sep="\t",
                    #     index=None,
                    # )
                    # *****************************************************

                    # Concat with original termlist to form a new one
                    new_terms_df = pd.concat([terms_df, new_terms_df])

                    new_terms_df.to_csv(
                        os.path.join(data_folder, new_terms_filename),
                        sep="\t",
                        index=None,
                        header=None,
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
    run()
