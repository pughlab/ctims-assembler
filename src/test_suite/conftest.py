"""
This pytest conftest.py file is a configuration module that defines fixtures and setup for testing the refactored
clinical and genomic data generation scripts. This configuration module ensures that the tests can compare the
outputs of the refactored scripts with those of the original scripts.

Before running the tests, make sure to create the following files and place them in the specified locations:

- `data_fusions.txt`: Genomic fusion input file - Place it in the '../../input/' directory.
- `allAnnotatedVariants.txt`: Genomic variants input file - Place it in the '../../input/' directory.
- `data_CNA.txt`: Genomic CNA input file - Place it in the '../../input/' directory.
- `data_mutations_extended.txt`: Genomic MAF input file - Place it in the '../../input/' directory.
- `data_clinical_samples.txt`: Clinical samples input file - Place it in the '../../input/' directory.
- `data_clinical_patients.txt`: Clinical patients input file - Place it in the '../../input/' directory.
- `sample_genomic_output.csv`: Pre-made genomic output CSV file for comparison - Place it in the '../../src/tests/test_input/' directory.
- `sample_clinical_output.csv`: Pre-made clinical output CSV file for comparison - Place it in the '../../src/tests/test_input/' directory.

These files are necessary for running the tests, as they serve as the input for the data generation scripts. The tests
will compare the output of the refactored scripts with the pre-made CSV files to ensure that the refactored scripts
produce the same results as the original scripts.

The input for the genomic assembly script does not require all files. Each input file is optional.
"""
import json
from unittest.mock import Mock

import pandas as pd
import pytest
from pandas import DataFrame

from src.test_suite import utils as test_utils
from src.tools import prepare_clinical_data, prepare_genomic_data, old_prepare_clinical_data, old_prepare_genomic_data
from src.tools.assembler_utils.datatypes.config import Config
from src.tools.assembler_utils.script_logging import init_logger

TEST_CONFIG_FP = "../../src/test_suite/test_config.json"

# Chunk size for each CSV read
DF_CHUNK_SIZE = 1000


def get_test_config() -> dict:
    """
    Opens the test config file and loads into dict.
    :return: Dictionary containing contents of config
    """
    with open(TEST_CONFIG_FP) as config_f:
        return json.load(config_f)


@pytest.fixture(scope='module')
def test_config_fixture() -> dict:
    """
    Opens the test config file and loads into dict.
    :return: Dictionary containing contents of config
    """
    return get_test_config()


@pytest.fixture(scope='module')
def clinical_config(test_config_fixture: dict) -> dict:
    """
    Get the clinical dict from the test config dict.
    :param test_config_fixture:
    :return: The clinical relevant object in the dict
    """

    return test_config_fixture["clinical"]


@pytest.fixture(scope='module')
def genomic_config(test_config_fixture: dict) -> dict:
    """
    Get the genomic dict from the test config dict.
    In addition, check if the input files in this config exist. If they dont, then create an empty version of them.
    These empty versions are used in the old assembly scripts.
    :param test_config_fixture:
    :return: The clinical relevant object in the dict
    """

    genomic = test_config_fixture["genomic"]

    # Ensure that the files used for input exist, and if they dont exist then create empty versions of them
    if test_utils.fp_does_not_exist(genomic["script_input"]["fusion_fp"]):
        genomic["script_input"]["fusion_fp"] = test_utils.create_empty_file("fusion_fp")
    if test_utils.fp_does_not_exist(genomic["script_input"]["variants_fp"]):
        genomic["script_input"]["variants_fp"] = test_utils.create_empty_file("variants_fp")
    if test_utils.fp_does_not_exist(genomic["script_input"]["cna_fp"]):
        genomic["script_input"]["cna_fp"] = test_utils.create_empty_file("cna_fp")
    if test_utils.fp_does_not_exist(genomic["script_input"]["maf_fp"]):
        genomic["script_input"]["maf_fp"] = test_utils.create_empty_file("maf_fp")
    return genomic


def generate_mock_clinical_args_obj(clinical_config) -> Mock:
    """
    Generates a Mock object containing relevant fields used in `ArgumentParser` objects.
    """

    mock = Mock()
    mock.patient_file = clinical_config["script_input"]["patient_fp"]
    mock.sample_file = clinical_config["script_input"]["sample_fp"]
    mock.study_file = clinical_config["script_input"]["study_fp"]
    mock.debug = clinical_config["script_input"]["debug_flag"]

    # This is to be set within the test
    mock.output = None

    return mock


def generate_mock_genomic_args_obj(genomic_config) -> Mock:
    """
    Generates a Mock object containing relevant fields used in `ArgumentParser` objects.
    """

    mock = Mock()
    mock.maf_file = genomic_config["script_input"]["maf_fp"]
    mock.cna_file = genomic_config["script_input"]["cna_fp"]
    mock.variants = genomic_config["script_input"]["variants_fp"]
    mock.fusion_file = genomic_config["script_input"]["fusion_fp"]
    mock.data_sv = genomic_config["script_input"]["data_sv_fp"]
    mock.debug = genomic_config["script_input"]["debug_flag"]
    mock.config_file = genomic_config["script_input"]["config_file"]

    # This is to be set within the test
    mock.output_file = None

    return mock


@pytest.fixture(scope='module')
def expected_clinical_df(clinical_config) -> DataFrame:
    """
    Fixture to load the pre-made clinical CSV file into a pandas DataFrame.

    Returns:
        DataFrame: The pre-made clinical CSV file loaded as a pandas DataFrame.
    """

    # Load CSV file into a pandas dataframe
    fp = clinical_config["pre_made_csv_fp"]
    df = pd.read_csv(fp, chunksize=DF_CHUNK_SIZE)
    return df


@pytest.fixture(scope='module')
def expected_genomic_df(genomic_config) -> DataFrame:
    """
    Fixture to load the pre-made genomic CSV file into a pandas DataFrame.

    Returns:
        DataFrame: The pre-made genomic CSV file loaded as a pandas DataFrame.
    """

    fp = genomic_config["pre_made_csv_fp"]
    # Load CSV file into a pandas dataframe
    df = pd.read_csv(fp, chunksize=DF_CHUNK_SIZE)
    return df


@pytest.fixture(scope='module')
def generated_refactored_clinical_df(clinical_config):
    """
    Fixture to generate the clinical DataFrame using the refactored generation script.

    Returns:
        DataFrame: The clinical DataFrame generated using the refactored generation script.
    """

    mock_args_obj = generate_mock_clinical_args_obj(clinical_config)
    mock_args_obj.output = clinical_config["script_output"]["generated_refactored_fp"]

    init_logger(mock_args_obj.debug)

    # Call the function and output the result to a CSV file
    prepare_clinical_data.prepare_sample_data(mock_args_obj)

    # Load the function result from the CSV file
    df = pd.read_csv(mock_args_obj.output, chunksize=DF_CHUNK_SIZE)
    return df


@pytest.fixture(scope='module')
def generated_refactored_genomic_df(genomic_config):
    """
    Fixture to generate the genomic DataFrame using the refactored generation script.

    Returns:
        DataFrame: The genomic DataFrame generated using the refactored generation script.
    """

    mock_args_obj: Mock = generate_mock_genomic_args_obj(genomic_config)
    mock_args_obj.output_file = genomic_config["script_output"]["generated_refactored_fp"]

    init_logger(mock_args_obj.debug)
    config: Config = prepare_genomic_data.open_config(mock_args_obj.config_file)

    # Call the function and output the result to a CSV file
    prepare_genomic_data.prepare_genomic_data(mock_args_obj, config)

    # Load the function result from the CSV file
    df = pd.read_csv(mock_args_obj.output_file, chunksize=DF_CHUNK_SIZE)
    return df


@pytest.fixture(scope='module')
def generated_expected_clinical_df(clinical_config):
    """
    Fixture to generate the clinical DataFrame using the original generation script.

    Returns:
        DataFrame: The clinical DataFrame generated using the original generation script.
    """

    mock_args_obj = generate_mock_clinical_args_obj(clinical_config)
    mock_args_obj.output = clinical_config["script_output"]["generated_expected_fp"]

    # Call the function and output the result to a CSV file
    old_prepare_clinical_data.prepare_sample_data(mock_args_obj)
    # Load CSV file into a pandas dataframe
    df = pd.read_csv(mock_args_obj.output, chunksize=DF_CHUNK_SIZE)
    return df


@pytest.fixture(scope='module')
def generated_expected_genomic_df(genomic_config):
    """
    Fixture to generate the genomic DataFrame using the original generation script.

    Returns:
        DataFrame: The genomic DataFrame generated using the original generation script.
    """

    mock_args_obj = generate_mock_genomic_args_obj(genomic_config)
    mock_args_obj.output_file = genomic_config["script_output"]["generated_expected_fp"]

    # Call the function and output the result to a CSV file
    old_prepare_genomic_data.prepare_genomic_data(mock_args_obj)
    # Load CSV file into a pandas dataframe
    df = pd.read_csv(mock_args_obj.output_file, chunksize=DF_CHUNK_SIZE)
    return df
