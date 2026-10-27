import argparse


class CBioToolsArgParser(argparse.Namespace):
    """
    A class to represent the command line arguments for the cBioPortal tools.

    Attributes:
        study_id (str): The study ID to fetch data for.
        output_dir (str): The output directory to save the data to.
        output_ip (str): The IP address of the MongoDB database to output to.
    """
    study_id: str
    output_dir: str
    output_ip: str


def generate_default_arg_parser() -> argparse.ArgumentParser:
    """
    Generate the argument parser for the command line interface.

    Returns:
        argparse.ArgumentParser: The argument parser.
    """
    # help="Required arguments: --study_id, --output_dir"
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--study_id", type=str, required=True, help="The study ID to fetch data for.")
    
    mutual_exclusive_group = parser.add_mutually_exclusive_group(required=True)
    mutual_exclusive_group.add_argument("-o", "--output_dir", type=str, help="The output directory to save the data to.")
    mutual_exclusive_group.add_argument("-i", "--output_ip", type=str, help="The IP address of the MongoDB database.")

    return parser
