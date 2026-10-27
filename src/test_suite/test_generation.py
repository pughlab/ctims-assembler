from pandas import DataFrame
from src.test_suite import utils as test_utils


def test_refactored_clinical_code(generated_expected_clinical_df: DataFrame, generated_refactored_clinical_df: DataFrame):
    """
    Tests if the refactored clinical code outputs the same data as the original.
    This function generates a new output for both old and refactored versions of the `prepare_clinical_data.py` script

    :param generated_expected_clinical_df: Fixture for data that is expected and tested against
    :param generated_refactored_clinical_df: Fixture for data that is generated and tested
    """

    test_utils.assert_df_equals(generated_expected_clinical_df, generated_refactored_clinical_df)


def test_refactored_genomic_code(generated_expected_genomic_df: DataFrame, generated_refactored_genomic_df: DataFrame):

    test_utils.assert_df_equals(generated_expected_genomic_df, generated_refactored_genomic_df)
