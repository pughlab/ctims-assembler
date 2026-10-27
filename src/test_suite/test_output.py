from pandas import DataFrame
from src.test_suite import utils as testing_utils



def test_refactored_clinical_code(expected_clinical_df: DataFrame, generated_refactored_clinical_df: DataFrame):
    """
    Tests if the refactored clinical code outputs the same data as the original.

    :param expected_clinical_df: Fixture for data that is expected and tested against
    :param generated_refactored_clinical_df: Fixture for data that is generated and tested
    """

    testing_utils.assert_df_equals(expected_clinical_df, generated_refactored_clinical_df)


def test_refactored_genomic_code(expected_genomic_df: DataFrame, generated_refactored_genomic_df: DataFrame):
    """
    Tests if the refactored genomic code outputs the same data as the original.

    :param expected_clinical_df: Fixture for data that is expected and tested against
    :param generated_refactored_clinical_df: Fixture for data that is generated and tested
    """

    testing_utils.assert_df_equals(expected_genomic_df, generated_refactored_genomic_df)
