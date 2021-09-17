import click
import logging
from . import synonymize
from typing import TextIO
from . import DATA_FOLDER, SCHEMA, SYNONYM_RULES

rule_option = click.option(
    "-r",
    "--rule",
    type=click.Path(),
    default=SYNONYM_RULES,
    help="YAML file which dictates the rules for the custom NER.",
)

schema_option = click.option(
    "-s",
    "--schema",
    type=click.Path(),
    default=SCHEMA,
    help="YAML file which provides the schema.",
)

data_option = click.option(
    "-d",
    "--data",
    type=click.Path(),
    default=DATA_FOLDER,
    help="The termlists of the ontologies used (TSV format)",
)


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
def main(verbose: int, quiet: bool):
    """Main."""
    if verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose == 1:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    if quiet:
        logging.basicConfig(level=logging.ERROR)


@main.command("run")
@rule_option
@schema_option
@data_option
def run_click(
    rule: TextIO,
    schema: TextIO,
    data: TextIO,
):
    """Run synonymizer based n the input parameters provided.

    :param rule: YAML file that contains the rules.
    :type rule: TextIO
    :param schema: YAML file that provides schema.
    :type schema: TextIO
    :param data: Data folder where the input termlists are located.
    :type data: TextIO
    """
    synonymize.run(
        rule_file=rule,
        schema_file=schema,
        data_folder=data,
    )


if __name__ == "__main__":
    main()
